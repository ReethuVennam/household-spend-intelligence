from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from .config import DEFAULT_DATASET, FIXED_GENERATED_AT, SCALES, SEED
from .dashboard import build_dashboard
from .generator import generate_dataset
from .metrics import run_evaluation
from .validation import run_validation


def _parse_formats(value: str) -> tuple[str, ...]:
    items = tuple(x.strip().lower() for x in value.split(",") if x.strip())
    allowed = {"csv", "json", "sql"}
    bad = set(items) - allowed
    if bad:
        raise argparse.ArgumentTypeError(f"Unknown formats: {sorted(bad)}")
    if "csv" not in items:
        items = ("csv",) + items
    return tuple(dict.fromkeys(items))


def _cmd_generate(args) -> int:
    result = generate_dataset(
        scale=args.scale,
        seed=args.seed,
        out_dir=args.out,
        profiles=args.profiles,
        transactions=args.transactions,
        formats=args.formats,
    )
    manifest = result["manifest"]
    print(f"Generated {manifest['counts']['transactions']:,} transactions for {manifest['counts']['profiles']:,} profiles.")
    print(f"Scale={manifest['scale']} seed={manifest['seed']} output={Path(args.out).resolve()}")
    print(f"Anomaly impact counts: {manifest.get('anomaly_impact_counts', {})}")
    return 0


def _cmd_validate(args) -> int:
    dataset = getattr(args, "dataset", getattr(args, "out", str(DEFAULT_DATASET)))
    summary = run_validation(dataset)
    print(f"Validation: {summary['status']} ({summary['counts']['pass']} pass, {summary['counts']['warn']} warn, {summary['counts']['fail']} fail)")
    print((Path(dataset) / "validation" / "validation_summary.md").resolve())
    return 0 if summary["counts"]["fail"] == 0 else 1


def _cmd_evaluate(args) -> int:
    dataset = getattr(args, "dataset", getattr(args, "out", str(DEFAULT_DATASET)))
    report = run_evaluation(dataset)
    sections = report["sections"]
    print(f"Evaluation: categorization_accuracy={sections['categorization']['accuracy']:.4f} "
          f"treatment_accuracy={sections['treatment']['accuracy']:.4f} "
          f"recurring_f1={sections['recurring_detection']['f1']:.4f} "
          f"exception_score={sections['exception_handling_score']:.4f}")
    print((Path(dataset) / "outputs" / "evaluation_report.md").resolve())
    return 0


def _compare_manifests(left: dict, right: dict) -> dict:
    left_files = left.get("files", {})
    right_files = right.get("files", {})
    all_names = sorted(set(left_files) | set(right_files))
    mismatches = []
    rows_ok = 0
    for name in all_names:
        l = left_files.get(name)
        r = right_files.get(name)
        if l is None or r is None:
            mismatches.append({"file": name, "reason": "missing_on_one_side"})
            continue
        if l.get("rows") != r.get("rows"):
            mismatches.append({"file": name, "reason": "row_count", "left": l.get("rows"), "right": r.get("rows")})
        elif l.get("sha256") != r.get("sha256"):
            mismatches.append({"file": name, "reason": "checksum", "left": l.get("sha256"), "right": r.get("sha256")})
        else:
            rows_ok += 1
    counts_left = left.get("counts", {})
    counts_right = right.get("counts", {})
    count_mismatches = {k: [counts_left.get(k), counts_right.get(k)] for k in sorted(set(counts_left) | set(counts_right)) if counts_left.get(k) != counts_right.get(k)}
    return {
        "files_compared": len(all_names),
        "files_matching": rows_ok,
        "mismatches": mismatches,
        "count_mismatches": count_mismatches,
        "status": "PASS" if not mismatches and not count_mismatches else "FAIL",
    }


def _cmd_reproduce(args) -> int:
    temp_root = Path(tempfile.mkdtemp(prefix="opencode_repro_"))
    first = temp_root / "run_a"
    second = temp_root / "run_b"
    try:
        print(f"Reproducibility run A: scale={args.scale} seed={args.seed} formats={','.join(args.formats)}")
        a = generate_dataset(scale=args.scale, seed=args.seed, out_dir=first, formats=args.formats)["manifest"]
        print("Reproducibility run B: regenerating with identical seed")
        b = generate_dataset(scale=args.scale, seed=args.seed, out_dir=second, formats=args.formats)["manifest"]
        comparison = _compare_manifests(a, b)
        report = {
            "seed": args.seed,
            "scale": args.scale,
            "formats": list(args.formats),
            "generated_at": FIXED_GENERATED_AT,
            "run_a_counts": a.get("counts", {}),
            "run_b_counts": b.get("counts", {}),
            "transaction_count_a": a.get("transactions"),
            "transaction_count_b": b.get("transactions"),
            "comparison": comparison,
            "method": "Two fresh generations with the same seed; compare per-file row counts and SHA-256 checksums.",
        }
        out = Path(args.out)
        (out / "outputs").mkdir(parents=True, exist_ok=True)
        view = dict(report)
        (out / "outputs" / "reproducibility_report.json").write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8")
        md = [
            "# Reproducibility Report",
            "",
            f"Seed: `{args.seed}`  ",
            f"Scale: `{args.scale}`  ",
            f"Formats: `{','.join(args.formats)}`",
            "",
            f"Files compared: **{comparison['files_compared']}**  ",
            f"Files matching: **{comparison['files_matching']}**  ",
            f"Status: **{comparison['status']}**",
            "",
            "Method: two fresh generations with the same seed, compared by row count and SHA-256 checksum.",
            "",
        ]
        if comparison["mismatches"]:
            md.append("## Mismatches")
            md.append("")
            md.append("| File | Reason | Left | Right |")
            md.append("|---|---|---|---|")
            for item in comparison["mismatches"][:50]:
                md.append(f"| {item.get('file')} | {item.get('reason')} | {item.get('left', '')} | {item.get('right', '')} |")
            md.append("")
        (out / "outputs" / "reproducibility_report.md").write_text("\n".join(md), encoding="utf-8")
        print(f"Reproducibility: {comparison['status']} ({comparison['files_matching']}/{comparison['files_compared']} files match)")
        print((out / "outputs" / "reproducibility_report.md").resolve())
        return 0 if comparison["status"] == "PASS" else 1
    finally:
        if not args.keep:
            shutil.rmtree(temp_root, ignore_errors=True)
        else:
            print(f"Temporary runs kept at {temp_root}")


def _cmd_dashboard(args) -> int:
    dataset = getattr(args, "dataset", getattr(args, "out", str(DEFAULT_DATASET)))
    out = build_dashboard(dataset)
    print(f"Dashboard: {out.resolve()}")
    print(f"Size: {out.stat().st_size:,} bytes")
    return 0


def _cmd_all(args) -> int:
    rc = _cmd_generate(args)
    if rc != 0:
        return rc
    rc = _cmd_validate(args)
    if rc != 0:
        return rc
    rc = _cmd_evaluate(args)
    if rc != 0:
        return rc
    return _cmd_dashboard(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synthetic-spend-insights", description="Synthetic transaction, recurring-payment, and budget analytics data platform.")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate the dataset")
    gen.add_argument("--scale", choices=sorted(SCALES), default="full")
    gen.add_argument("--seed", type=int, default=SEED)
    gen.add_argument("--out", default=str(DEFAULT_DATASET))
    gen.add_argument("--profiles", type=int, default=None)
    gen.add_argument("--transactions", type=int, default=None)
    gen.add_argument("--formats", type=_parse_formats, default=("csv", "json", "sql"))
    gen.set_defaults(func=_cmd_generate)

    val = sub.add_parser("validate", help="Validate dataset integrity and reconciliation")
    val.add_argument("--dataset", default=str(DEFAULT_DATASET))
    val.set_defaults(func=_cmd_validate)

    ev = sub.add_parser("evaluate", help="Evaluate pipeline outputs against ground truth")
    ev.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ev.set_defaults(func=_cmd_evaluate)

    dash = sub.add_parser("dashboard", help="Build the static HTML dashboard")
    dash.add_argument("--dataset", default=str(DEFAULT_DATASET))
    dash.set_defaults(func=_cmd_dashboard)

    rep = sub.add_parser("reproduce", help="Generate twice and compare row counts and checksums")
    rep.add_argument("--scale", choices=sorted(SCALES), default="starter")
    rep.add_argument("--seed", type=int, default=SEED)
    rep.add_argument("--formats", type=_parse_formats, default=("csv",))
    rep.add_argument("--out", default=str(DEFAULT_DATASET))
    rep.add_argument("--keep", action="store_true")
    rep.set_defaults(func=_cmd_reproduce)

    allp = sub.add_parser("all", help="Generate, validate, evaluate, and build the dashboard")
    allp.add_argument("--scale", choices=sorted(SCALES), default="full")
    allp.add_argument("--seed", type=int, default=SEED)
    allp.add_argument("--out", default=str(DEFAULT_DATASET))
    allp.add_argument("--profiles", type=int, default=None)
    allp.add_argument("--transactions", type=int, default=None)
    allp.add_argument("--formats", type=_parse_formats, default=("csv", "json", "sql"))
    allp.set_defaults(func=_cmd_all)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
