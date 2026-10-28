export const MONTH_ABBR = {
  "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
  "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
};

export function monthLabel(month) {
  return (MONTH_ABBR[month.slice(5, 7)] || month.slice(5, 7)) + " " + month.slice(0, 4);
}

export function monthShort(month) {
  return MONTH_ABBR[month.slice(5, 7)] || month.slice(5, 7);
}

export function fmtInt(v) {
  return Math.round(v).toLocaleString("en-US");
}

export function fmtMoney(v, dec = 0) {
  return "$" + v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

export function fmtMoneyC(v) {
  const a = Math.abs(v);
  if (a >= 1e9) return "$" + (v / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return "$" + (v / 1e6).toFixed(1) + "M";
  if (a >= 1e3) return "$" + (v / 1e3).toFixed(1) + "k";
  return "$" + Math.round(v);
}

export function fmtPct(v, dec = 2) {
  return (v * 100).toFixed(dec) + "%";
}

export function fmtNum(v, dec = 0) {
  return v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

export function niceMax(value) {
  if (value <= 0) return 1;
  const base = Math.pow(10, Math.floor(Math.log10(value)));
  for (const mult of [1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10]) {
    if (value <= mult * base) return mult * base;
  }
  return 10 * base;
}

export function axisMoney(v) {
  const a = Math.abs(v);
  if (a >= 1e6) return "$" + (v / 1e6).toFixed(1) + "M";
  if (a >= 1e3) return "$" + (v / 1e3).toFixed(0) + "k";
  return "$" + v.toFixed(0);
}

export const SEVERITY_PILL = { low: "ok", medium: "warn", high: "bad" };
export const ISSUE_PILL = {
  transfer_double_count: "bad",
  refund_treated_as_new_expense: "bad",
  timezone_boundary_date: "warn",
  recurring_series_skip: "warn",
  budget_taxonomy_mismatch: "warn",
};
export const STATUS_PILL = { under: "ok", near: "warn", over: "bad" };
export const KPI_ACCENTS = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#2563eb"];
