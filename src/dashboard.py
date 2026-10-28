from __future__ import annotations

import html
import json
import math
from pathlib import Path

import pandas as pd

_CSS = """
:root{
  --bg:#f4f6fb; --card:#ffffff; --line:#e6ebf2; --ink:#0f172a; --mid:#64748b;
  --thead:#f8fafc; --hover:#f8fafc; --strip:#f8fafc; --track:#eef2f7;
  --blue:#3b82f6; --green:#10b981; --amber:#f59e0b; --red:#ef4444;
  --indigo:#6366f1; --purple:#8b5cf6; --teal:#14b8a6;
  --shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px -18px rgba(15,23,42,.25);
}
html[data-theme=dark]{
  --bg:#0a0f1e; --card:#121a2f; --line:#23304d; --ink:#e6ecfa; --mid:#8fa0bd;
  --thead:#16203a; --hover:#16203a; --strip:#0f1730; --track:#1d2740;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 28px -18px rgba(0,0,0,.7);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased;transition:background .25s,color .25s}
.wrap{max-width:1200px;margin:0 auto;padding:0 22px 56px}
header{background:linear-gradient(115deg,#111827 0%,#1e293b 45%,#312e81 100%);color:#fff;padding:34px 0 26px;
  border-bottom:4px solid #6366f1;position:relative;overflow:hidden}
header::after{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:radial-gradient(rgba(255,255,255,.07) 1px,transparent 1px);background-size:26px 26px}
.head-top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap;position:relative;z-index:1}
.head-right{display:flex;gap:12px;align-items:stretch}
h1{margin:0 0 8px;font-size:29px;letter-spacing:-.02em;font-weight:800}
.tagline{color:#cbd5e1;font-size:14px;max-width:640px}
.badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.badge{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);color:#e2e8f0;
  padding:4px 11px;border-radius:999px;font-size:12px;font-weight:600}
.status-box{text-align:right;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.16);
  border-radius:14px;padding:14px 20px;min-width:190px}
.status-box .s-label{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:#94a3b8}
.status-box .s-value{font-size:24px;font-weight:800;color:#6ee7b7;margin-top:3px}
.status-box .s-sub{font-size:12px;color:#cbd5e1;margin-top:2px}
.theme-btn{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.22);color:#e2e8f0;
  border-radius:14px;width:46px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.15s}
.theme-btn:hover{background:rgba(255,255,255,.2)}
.theme-btn svg{width:19px;height:19px;fill:currentColor}
html:not([data-theme=dark]) .icon-moon{display:none}
html[data-theme=dark] .icon-sun{display:none}
nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:22px;position:relative;z-index:1}
nav a{color:#cbd5e1;text-decoration:none;font-size:13px;font-weight:600;padding:7px 14px;
  border-radius:999px;border:1px solid rgba(255,255,255,.15);transition:.15s}
nav a:hover{background:rgba(255,255,255,.14);color:#fff;border-color:rgba(255,255,255,.35)}
nav a.active{background:#6366f1;border-color:#818cf8;color:#fff}
section{margin-top:34px;scroll-margin-top:16px}
.sec-head{display:flex;align-items:center;gap:11px;margin-bottom:14px}
.sec-head .dot{width:11px;height:11px;border-radius:4px;background:var(--indigo);box-shadow:0 0 0 4px rgba(99,102,241,.16)}
.sec-head h2{margin:0;font-size:19px;letter-spacing:-.01em}
.sec-head .hint{color:var(--mid);font-size:12.5px;margin-left:4px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;
  box-shadow:var(--shadow);transition:background .25s,border-color .25s}
.card h3{margin:0 0 14px;font-size:14.5px;color:var(--ink);opacity:.85;font-weight:700}
.grid{display:grid;gap:13px}
.kpis{grid-template-columns:repeat(auto-fit,minmax(196px,1fr))}
.mini{grid-template-columns:repeat(auto-fit,minmax(158px,1fr))}
.kpi{position:relative;background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:16px 17px 15px;overflow:hidden;box-shadow:var(--shadow);transition:transform .15s,box-shadow .15s}
.kpi:hover{transform:translateY(-3px);box-shadow:0 14px 30px -16px rgba(79,70,229,.5)}
.kpi::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;background:var(--accent,var(--indigo))}
.kpi-label{font-size:11px;color:var(--mid);text-transform:uppercase;letter-spacing:.07em;font-weight:700}
.kpi-value{font-size:23px;font-weight:800;margin-top:7px;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kpi-sub{font-size:11.5px;color:var(--mid);margin-top:4px}
.kpi.mini{padding:13px 15px}
.kpi.mini .kpi-value{font-size:19px}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.2px;min-width:520px}
th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{background:var(--thead);font-weight:700;font-size:11.5px;color:var(--mid);text-transform:uppercase;letter-spacing:.05em;
  white-space:nowrap;user-select:none}
table.sortable th{cursor:pointer}
table.sortable th:hover{color:var(--ink)}
th .arrow{opacity:.45;font-size:10px;margin-left:4px}
tbody tr{transition:background .1s}
tbody tr:hover{background:var(--hover)}
td.right,th.right{text-align:right}
td.nowrap{white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
.pill{display:inline-block;padding:3px 10px;border-radius:999px;font-size:11.5px;font-weight:700;white-space:nowrap}
.pill.ok{background:#d1fae5;color:#065f46}
.pill.warn{background:#fef3c7;color:#92400e}
.pill.bad{background:#fee2e2;color:#991b1b}
.pill.info{background:#e0e7ff;color:#3730a3}
.pill.muted{background:var(--track);color:var(--mid)}
html[data-theme=dark] .pill.ok{background:#064e3b;color:#6ee7b7}
html[data-theme=dark] .pill.warn{background:#78350f;color:#fcd34d}
html[data-theme=dark] .pill.bad{background:#7f1d1d;color:#fca5a5}
html[data-theme=dark] .pill.info{background:#312e81;color:#a5b4fc}
.meter{background:var(--track);border-radius:999px;height:9px;width:140px;overflow:hidden;display:inline-block;vertical-align:middle}
.meter span{display:block;height:100%;border-radius:999px;transition:width .9s cubic-bezier(.22,1,.36,1)}
.split{display:grid;grid-template-columns:360px 1fr;gap:16px}
.split2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.stack{display:grid;gap:16px}
@media(max-width:900px){.split,.split2{grid-template-columns:1fr}}
.legend{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;font-weight:600;margin-top:12px}
.legend .item{display:flex;align-items:center;gap:8px}
.swatch{width:12px;height:12px;border-radius:4px;display:inline-block;flex:none}
.note{font-size:12.2px;color:var(--mid);margin-top:12px;line-height:1.55}
.donut-wrap{display:flex;justify-content:center;padding:6px 0 2px}
.status-list{margin-top:14px;display:grid;gap:9px}
.status-row{display:flex;align-items:center;justify-content:space-between;font-size:13px;
  background:var(--strip);border:1px solid var(--line);border-radius:10px;padding:9px 13px}
.status-row .left{display:flex;align-items:center;gap:9px;font-weight:600}
.status-row .num{font-weight:700;font-variant-numeric:tabular-nums}
.reports{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:13px}
.report{display:block;background:var(--strip);border:1px solid var(--line);border-radius:13px;padding:15px 17px;
  text-decoration:none;color:inherit;transition:.15s}
.report:hover{border-color:#818cf8;transform:translateY(-3px);box-shadow:0 12px 26px -16px rgba(79,70,229,.7)}
.report .r-title{font-weight:700;font-size:14px;color:#6366f1}
.report .r-desc{font-size:12.3px;color:var(--mid);margin-top:5px;line-height:1.5}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--mid);font-size:12.5px;font-weight:600;
  padding:7px 14px;cursor:pointer;transition:.12s;font-family:inherit}
.seg button:hover{color:var(--ink);background:var(--hover)}
.seg button.on{background:var(--indigo);color:#fff}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.controls input,.controls select{background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:10px;padding:8px 12px;font-size:13px;font-family:inherit;min-width:170px;outline:none;transition:.12s}
.controls input:focus,.controls select:focus{border-color:#818cf8;box-shadow:0 0 0 3px rgba(99,102,241,.18)}
.controls label{display:flex;align-items:center;gap:7px;font-size:13px;font-weight:600;color:var(--ink);cursor:pointer}
.count-note{font-size:12.5px;color:var(--mid);margin-left:auto;font-weight:600}
.ex-scroll{max-height:430px;overflow:auto;border:1px solid var(--line);border-radius:12px}
.ex-scroll table{min-width:860px}
.ex-scroll thead th{position:sticky;top:0;z-index:2;box-shadow:inset 0 -1px 0 var(--line)}
.hidden{display:none}
.chart-tip{position:fixed;pointer-events:none;background:#0f172a;color:#f1f5f9;font-size:12px;font-weight:600;
  padding:7px 11px;border-radius:8px;box-shadow:0 8px 24px -8px rgba(0,0,0,.5);display:none;z-index:99;
  white-space:nowrap;border:1px solid rgba(255,255,255,.15)}
svg text{font-family:inherit}
.footer{margin-top:44px;border-top:1px solid var(--line);padding-top:16px;font-size:12.3px;color:var(--mid)}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
@media print{
  nav,.theme-btn,.seg{display:none}
  body{background:#fff}
  .card,.kpi{break-inside:avoid}
}
"""

_JS = r"""
(function(){
"use strict";
var doc=document;
function qs(s,r){return (r||doc).querySelector(s);}
function qsa(s,r){return Array.prototype.slice.call((r||doc).querySelectorAll(s));}

var saved=null;
try{saved=localStorage.getItem("hsi-theme");}catch(e){}
if(saved==="dark"||saved==="light"){doc.documentElement.setAttribute("data-theme",saved);}
var themeBtn=qs("#theme-btn");
if(themeBtn){
  themeBtn.addEventListener("click",function(){
    var dark=doc.documentElement.getAttribute("data-theme")==="dark";
    var next=dark?"light":"dark";
    doc.documentElement.setAttribute("data-theme",next);
    try{localStorage.setItem("hsi-theme",next);}catch(e){}
  });
}

var navLinks=qsa("nav a");
var sections=qsa("section");
if("IntersectionObserver" in window){
  var spy=new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){
        navLinks.forEach(function(l){l.classList.toggle("active",l.getAttribute("href")==="#"+en.target.id);});
      }
    });
  },{rootMargin:"-25% 0px -65% 0px"});
  sections.forEach(function(s){spy.observe(s);});
}

function fmtCount(el,v){
  var f=el.getAttribute("data-format")||"num";
  var d=parseInt(el.getAttribute("data-decimals")||"0",10);
  var pre=el.getAttribute("data-prefix")||"";
  var suf=el.getAttribute("data-suffix")||"";
  if(f==="moneyc"){
    var a=Math.abs(v);
    if(a>=1e9)return "$"+(v/1e9).toFixed(2)+"B";
    if(a>=1e6)return "$"+(v/1e6).toFixed(1)+"M";
    if(a>=1e3)return "$"+(v/1e3).toFixed(1)+"k";
    return "$"+Math.round(v);
  }
  if(f==="pct")return (v*100).toFixed(d)+"%";
  return pre+v.toLocaleString("en-US",{minimumFractionDigits:d,maximumFractionDigits:d})+suf;
}
function animateCount(el){
  var target=parseFloat(el.getAttribute("data-count"));
  if(isNaN(target))return;
  var finalText=el.textContent;
  var reduce=window.matchMedia&&window.matchMedia("(prefers-reduced-motion:reduce)").matches;
  if(reduce)return;
  var dur=850,start=null;
  function step(ts){
    if(!start)start=ts;
    var p=Math.min((ts-start)/dur,1);
    var eased=1-Math.pow(1-p,3);
    el.textContent=p<1?fmtCount(el,target*eased):finalText;
    if(p<1)requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
function initMeters(){
  qsa(".meter > span").forEach(function(bar){
    var w=bar.style.width;
    bar.setAttribute("data-w",w);
    bar.style.width="0%";
  });
}
function revealMeters(){
  qsa(".meter > span").forEach(function(bar){
    var w=bar.getAttribute("data-w");
    if(w)bar.style.width=w;
  });
}
if("IntersectionObserver" in window){
  initMeters();
  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(!en.isIntersecting)return;
      qsa("[data-count]",en.target).forEach(animateCount);
      qsa(".meter > span",en.target).forEach(function(bar){
        var w=bar.getAttribute("data-w");if(w)bar.style.width=w;
      });
      io.unobserve(en.target);
    });
  },{rootMargin:"0px 0px -8% 0px"});
  qsa("section").forEach(function(s){io.observe(s);});
}

var tip=doc.createElement("div");
tip.className="chart-tip";
doc.body.appendChild(tip);
qsa("[data-tip]").forEach(function(el){
  el.addEventListener("mousemove",function(e){
    tip.textContent=el.getAttribute("data-tip");
    tip.style.display="block";
    tip.style.left=(e.clientX+16)+"px";
    tip.style.top=(e.clientY-12)+"px";
  });
  el.addEventListener("mouseleave",function(){tip.style.display="none";});
});

function parseNum(s){
  var cleaned=String(s).replace(/[$,%]/g,"").replace(/,/g,"").trim();
  if(cleaned.indexOf("/")>-1||cleaned.indexOf("PASS")>-1)return null;
  var v=parseFloat(cleaned);
  return isNaN(v)?null:v;
}
qsa("table.sortable").forEach(function(t){
  var headers=qsa("th",t);
  headers.forEach(function(th,i){
    th.insertAdjacentHTML("beforeend",'<span class="arrow">&#8645;</span>');
    th.addEventListener("click",function(){
      var asc=th.getAttribute("data-asc")!=="1";
      headers.forEach(function(x){x.removeAttribute("data-asc");});
      th.setAttribute("data-asc",asc?"1":"0");
      var tb=t.tBodies[0];
      var rows=Array.prototype.slice.call(tb.rows);
      rows.sort(function(a,b){
        var x=parseNum(a.cells[i].textContent),y=parseNum(b.cells[i].textContent);
        if(x!==null&&y!==null)return asc?x-y:y-x;
        var tx=a.cells[i].textContent,ty=b.cells[i].textContent;
        return asc?tx.localeCompare(ty):ty.localeCompare(tx);
      });
      rows.forEach(function(r){tb.appendChild(r);});
    });
  });
});

qsa("[data-seg]").forEach(function(seg){
  var btns=qsa("button",seg);
  btns.forEach(function(btn){
    btn.addEventListener("click",function(){
      btns.forEach(function(b){b.classList.remove("on");});
      btn.classList.add("on");
      qsa("[data-pane]",seg.closest(".card")||doc).forEach(function(p){
        p.classList.toggle("hidden",p.getAttribute("data-pane")!==btn.getAttribute("data-pane-target"));
      });
    });
  });
});

var exData=qs("#ex-data");
if(exData&&exData.textContent&&exData.textContent.trim()&&qs("#ex-body")){
  var rows=JSON.parse(exData.textContent);
  var box=qs("#ex-body");
  var search=qs("#ex-search");
  var issueSel=qs("#ex-issue");
  var mismatch=qs("#ex-mismatch");
  var note=qs("#ex-count");
  var issues=[];
  rows.forEach(function(r){if(r.i&&r.i!=="none"&&issues.indexOf(r.i)<0)issues.push(r.i);});
  issues.sort();
  issues.forEach(function(v){
    var o=doc.createElement("option");o.value=v;o.textContent=v;issueSel.appendChild(o);
  });
  function esc(s){return String(s==null?"":s);}
  function render(){
    var q=(search.value||"").toLowerCase();
    var iss=issueSel.value;
    var onlyMis=mismatch.checked;
    var htmlOut=[],shown=0;
    for(var i=0;i<rows.length;i++){
      var r=rows[i];
      if(iss!=="all"&&(r.i||"none")!==iss)continue;
      if(onlyMis&&r.p===r.t)continue;
      if(q&&String(r.x).toLowerCase().indexOf(q)<0&&String(r.id).toLowerCase().indexOf(q)<0&&String(r.u).toLowerCase().indexOf(q)<0)continue;
      shown++;
      var mis=r.p!==r.t;
      var issue=r.i&&r.i!=="none"?r.i:"";
      htmlOut.push("<tr>"+
        "<td class='nowrap'>"+esc(r.d)+"</td>"+
        "<td class='nowrap'>"+esc(r.id)+"</td>"+
        "<td>"+esc(r.x)+"</td>"+
        "<td class='right nowrap'>"+(r.a<0?"":"+")+"$"+Math.abs(r.a).toFixed(2)+"</td>"+
        "<td class='nowrap'><span class='pill info'>"+esc(r.p)+"</span></td>"+
        "<td class='nowrap'><span class='pill "+(mis?"bad":"ok")+"'>"+esc(r.t)+"</span></td>"+
        "<td>"+(issue?"<span class='pill warn'>"+esc(issue)+"</span>":"<span class='pill muted'>-</span>")+"</td>"+
        "<td class='right'>"+(r.c!=null?Number(r.c).toFixed(2):"-")+"</td>"+
        "</tr>");
    }
    box.innerHTML=htmlOut.join("")||"<tr><td colspan='8' style='text-align:center;color:var(--mid)'>No rows match the current filters</td></tr>";
    note.textContent="showing "+shown+" of "+rows.length+" rows";
  }
  search.addEventListener("input",render);
  issueSel.addEventListener("change",render);
  mismatch.addEventListener("change",render);
  render();
}
})();
"""

SEVERITY_PILL = {"low": "ok", "medium": "warn", "high": "bad"}
ISSUE_PILL = {
    "transfer_double_count": "bad",
    "refund_treated_as_new_expense": "bad",
    "timezone_boundary_date": "warn",
    "recurring_series_skip": "warn",
    "budget_taxonomy_mismatch": "warn",
}
STATUS_PILL = {"under": "ok", "near": "warn", "over": "bad"}
STATUS_COLORS = {"under": "#10b981", "near": "#f59e0b", "over": "#ef4444"}
KPI_ACCENTS = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#2563eb"]

MONTH_ABBR = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _int(value) -> str:
    return f"{int(round(float(value))):,}"


def _money(value, decimals: int = 0) -> str:
    return f"${float(value):,.{decimals}f}"


def _money_c(value) -> str:
    value = float(value)
    a = abs(value)
    if a >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if a >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if a >= 1_000:
        return f"${value / 1_000:.1f}k"
    return f"${value:.0f}"


def _pct(value, decimals: int = 2) -> str:
    return f"{float(value) * 100:.{decimals}f}%"


def _kpi(label: str, value: str, sub: str = "", accent: str = "",
         count: float | None = None, fmt: str = "num", decimals: int = 0,
         suffix: str = "", prefix: str = "") -> str:
    style = f' style="--accent:{_esc(accent)}"' if accent else ""
    attrs = ""
    if count is not None:
        attrs = (f' data-count="{count}" data-format="{_esc(fmt)}" data-decimals="{decimals}"'
                 f' data-suffix="{_esc(suffix)}" data-prefix="{_esc(prefix)}"')
    sub_html = f'<div class="kpi-sub">{_esc(sub)}</div>' if sub else ""
    return (
        f'<div class="kpi"{style}><div class="kpi-label">{_esc(label)}</div>'
        f'<div class="kpi-value"{attrs}>{_esc(value)}</div>{sub_html}</div>'
    )


def _pill(text, kind: str) -> str:
    return f'<span class="pill {_esc(kind)}">{_esc(text)}</span>'


def _meter(value) -> str:
    frac = max(0.0, min(1.0, float(value)))
    color = "#10b981" if frac >= 0.95 else "#f59e0b" if frac >= 0.8 else "#ef4444"
    return (f'<span class="meter"><span data-w="{frac * 100:.1f}%" '
            f'style="width:{frac * 100:.1f}%;background:{color}"></span></span>')


def _nice_max(value: float) -> float:
    if value <= 0:
        return 1.0
    base = 10 ** math.floor(math.log10(value))
    for mult in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0):
        if value <= mult * base:
            return mult * base
    return 10.0 * base


def _axis_money(value: float) -> str:
    a = abs(value)
    if a >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if a >= 1_000:
        return f"${value / 1_000:.0f}k"
    return f"${value:.0f}"


def _svg_monthly(months, spend, income) -> str:
    w, h = 840, 330
    left, right, top, bottom = 70, 18, 20, 52
    pw, ph = w - left - right, h - top - bottom
    ymax = _nice_max(max(max(spend), max(income)) * 1.05)
    slot = pw / max(len(months), 1)
    bw = slot * 0.30
    parts = [
        f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Monthly spend versus income">',
        '<defs><linearGradient id="gs" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#60a5fa"/><stop offset="100%" stop-color="#3b82f6"/></linearGradient>'
        '<linearGradient id="gi" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#34d399"/><stop offset="100%" stop-color="#10b981"/></linearGradient></defs>',
    ]
    for i in range(5):
        frac = i / 4
        y = top + ph * (1 - frac)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + pw}" y2="{y:.1f}" style="stroke:currentColor;opacity:.13"/>')
        parts.append(
            f'<text x="{left - 9}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="currentColor" '
            f'opacity=".55">{_axis_money(ymax * frac)}</text>'
        )
    for idx, (m, s, inc) in enumerate(zip(months, spend, income)):
        cx = left + slot * idx + slot / 2
        hs = ph * (s / ymax)
        hi = ph * (inc / ymax)
        label = MONTH_ABBR.get(str(m)[5:7], str(m)[5:7])
        tip_s = f"{label} {str(m)[:4]}: spend {_money_c(s)} / income {_money_c(inc)}"
        tip_i = f"{label} {str(m)[:4]}: income {_money_c(inc)} / spend {_money_c(s)}"
        parts.append(f'<rect x="{cx - bw - 2:.1f}" y="{top + ph - hs:.1f}" width="{bw:.1f}" height="{hs:.1f}" fill="url(#gs)" rx="4" data-tip="{_esc(tip_s)}"><title>{_esc(tip_s)}</title></rect>')
        parts.append(f'<rect x="{cx + 2:.1f}" y="{top + ph - hi:.1f}" width="{bw:.1f}" height="{hi:.1f}" fill="url(#gi)" rx="4" data-tip="{_esc(tip_i)}"><title>{_esc(tip_i)}</title></rect>')
        parts.append(f'<text x="{cx:.1f}" y="{top + ph + 19}" text-anchor="middle" font-size="11.5" font-weight="600" fill="currentColor" opacity=".65">{label}</text>')
    parts.append(f'<line x1="{left}" y1="{top + ph}" x2="{left + pw}" y2="{top + ph}" style="stroke:currentColor;opacity:.3"/>')
    parts.append("</svg>")
    return "".join(parts)


def _svg_hbar(items) -> str:
    w = 840
    label_w, value_w, rh = 160, 100, 34
    rows = max(len(items), 1)
    h = rows * rh + 14
    vmax = max((v for _, v in items), default=1) or 1
    bar_area = w - label_w - value_w - 20
    palette = ["#6366f1", "#3b82f6", "#0ea5e9", "#14b8a6", "#10b981", "#84cc16", "#f59e0b", "#f97316",
               "#ef4444", "#ec4899", "#8b5cf6", "#64748b"]
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Spend by category">']
    for i, (label, value) in enumerate(items):
        y = 7 + i * rh
        bw = bar_area * (value / vmax)
        color = palette[i % len(palette)]
        tip_text = f"{label}: {_money_c(value)} net spend"
        parts.append(f'<text x="{label_w - 12}" y="{y + 19}" text-anchor="end" font-size="12.5" font-weight="600" fill="currentColor">{_esc(label)}</text>')
        parts.append(f'<rect x="{label_w}" y="{y + 5}" width="{bar_area:.1f}" height="20" rx="10" style="fill:currentColor;opacity:.07"/>')
        parts.append(f'<rect x="{label_w}" y="{y + 5}" width="{max(bw, 3):.1f}" height="20" fill="{color}" rx="10" data-tip="{_esc(tip_text)}"><title>{_esc(tip_text)}</title></rect>')
        parts.append(f'<text x="{label_w + bar_area + 10:.1f}" y="{y + 19}" text-anchor="end" font-size="12.5" font-weight="700" fill="currentColor">{_money_c(value)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _svg_donut(items) -> str:
    size = 210
    r, sw = 74, 34
    c = size / 2
    total = sum(v for _, v, _ in items) or 1
    circ = 2 * math.pi * r
    parts = [
        f'<svg viewBox="0 0 {size} {size}" width="210" height="210" role="img" aria-label="Budget status distribution">',
        f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" style="stroke:currentColor;opacity:.07" stroke-width="{sw}"/>',
    ]
    offset = 0.0
    for label, v, color in items:
        seg = circ * (v / total)
        tip_text = f"{label}: {v:,} rows ({v / total * 100:.1f}%)"
        parts.append(
            f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-dasharray="{max(seg - 2, 0):.2f} {max(circ - seg + 2, 0):.2f}" stroke-dashoffset="{-offset:.2f}" '
            f'stroke-linecap="butt" transform="rotate(-90 {c} {c})" data-tip="{_esc(tip_text)}"><title>{_esc(tip_text)}</title></circle>'
        )
        offset += seg
    parts.append(f'<text x="{c}" y="{c - 4}" text-anchor="middle" font-size="30" font-weight="800" fill="currentColor">{_int(total)}</text>')
    parts.append(f'<text x="{c}" y="{c + 18}" text-anchor="middle" font-size="11.5" font-weight="600" fill="currentColor" opacity=".55">BUDGET ROWS</text>')
    parts.append("</svg>")
    return "".join(parts)


def _table(headers, rows, aligns=None, raw=False, sortable: bool = True) -> str:
    aligns = aligns or ["left"] * len(headers)
    cls = ' class="sortable"' if sortable else ""
    head = "".join(f'<th class="{a}">{_esc(h)}</th>' for h, a in zip(headers, aligns))
    body = []
    for row in rows:
        cells = "".join(
            f'<td class="{a}">{c if raw else _esc(c)}</td>' for c, a in zip(row, aligns)
        )
        body.append(f"<tr>{cells}</tr>")
    return (f'<div class="tw"><table{cls}><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def build_dashboard(dataset_dir: str = "dataset") -> Path:
    root = Path(dataset_dir)
    manifest = json.loads((root / "metadata" / "manifest.json").read_text(encoding="utf-8"))
    evaluation = json.loads((root / "outputs" / "evaluation_report.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "validation" / "validation_summary.json").read_text(encoding="utf-8"))

    monthly = pd.read_csv(root / "outputs" / "monthly_spend.csv")
    budgets = pd.read_csv(root / "outputs" / "budget_comparison.csv")
    recurring = pd.read_csv(root / "outputs" / "recurring_series.csv")
    anomalies = pd.read_csv(root / "ground_truth" / "anomaly_manifest.csv")
    cat = pd.read_csv(
        root / "outputs" / "categorized_transactions.csv",
        usecols=["offset_category_code", "spend_amount_usd"],
    )
    explorer_path = root.parent / "samples" / "explorer_sample.csv"
    explorer = pd.read_csv(explorer_path) if explorer_path.exists() else None

    counts = manifest["counts"]
    vc = validation["counts"]
    sec = evaluation["sections"]
    cat_sec = sec["categorization"]
    tre = sec["treatment"]
    per = sec["period_assignment"]
    trf = sec["transfer_and_refund"]
    rec = sec["recurring_detection"]
    bud = sec["budget_comparison"]
    total_checks = vc["pass"] + vc["warn"] + vc["fail"]

    mon = (
        monthly.groupby("period_month", sort=True, as_index=False)
        .agg(spend_usd=("spend_usd", "sum"), income_usd=("income_usd", "sum"))
    )
    months = mon["period_month"].tolist()
    spend_vals = [float(v) for v in mon["spend_usd"]]
    income_vals = [float(v) for v in mon["income_usd"]]

    by_cat = (
        cat[cat["spend_amount_usd"] != 0]
        .groupby("offset_category_code", sort=True)["spend_amount_usd"]
        .sum()
        .sort_values(ascending=False, kind="mergesort")
        .head(12)
    )
    cat_items = [(str(k), float(v)) for k, v in by_cat.items()]

    status_counts = budgets["status"].value_counts().to_dict()
    donut_items = [
        (k, int(v), STATUS_COLORS.get(k, "#94a3b8"))
        for k, v in sorted(status_counts.items(), key=lambda kv: -kv[1])
    ]
    budget_total = float(budgets["budget_amount_usd"].sum())
    actual_total = float(budgets["actual_spend_usd"].sum())
    variance_total = float(budgets["variance_usd"].sum())
    over = budgets.loc[budgets["status"] == "over"].sort_values("variance_usd", kind="mergesort").head(10)

    rec_status = recurring["status"].value_counts().to_dict()
    rec_missed = int((recurring["missed_occurrences"] > 0).sum())
    rec_expected = float(recurring["expected_amount_usd"].sum())
    rec_by_cat = recurring["category_code"].value_counts().head(8)

    anomaly_rows = (
        anomalies.groupby("issue_type", sort=True, as_index=False)
        .agg(
            anomalies=("anomaly_id", "count"),
            impact=("impact_count", "sum"),
            severity=("severity", "first"),
            behavior=("observed_behavior", "first"),
            resolution=("expected_resolution", "first"),
        )
        .sort_values("impact", ascending=False, kind="mergesort")
    )

    kpi_data = [
        ("Transactions", _int(counts["transactions"]), f"{manifest['scale']} scale, year {manifest['year']}",
         counts["transactions"], "num", 0, "", ""),
        ("Profiles", _int(counts["profiles"]), f"{_int(counts['accounts'])} accounts",
         counts["profiles"], "num", 0, "", ""),
        ("Budgets", _int(counts["budgets"]), f"{_int(counts['recurring_series'])} detected recurring series",
         counts["budgets"], "num", 0, "", ""),
        ("Strict net spend", _money_c(trf["strict_net_spend_usd"]), "transfers and refunds excluded",
         trf["strict_net_spend_usd"], "moneyc", 0, "", ""),
        ("Overstatement avoided", _money_c(trf["naive_spend_overstatement_usd"]), "naive minus strict spend",
         trf["naive_spend_overstatement_usd"], "moneyc", 0, "", ""),
        ("Categorization", _pct(cat_sec["accuracy"]), f"macro F1 {cat_sec['macro_f1']:.4f}",
         cat_sec["accuracy"], "pct", 2, "", ""),
        ("Recurring F1", f"{rec['f1']:.4f}", f"recall {_pct(rec['recall'], 1)}, precision {_pct(rec['precision'], 1)}",
         rec["f1"], "num", 4, "", ""),
        ("Validation", validation["status"], f"{vc['pass']}/{total_checks} checks passed",
         None, "num", 0, "", ""),
    ]
    kpis = "".join(
        _kpi(label, value, sub, KPI_ACCENTS[i % len(KPI_ACCENTS)],
             count=count, fmt=fmt, decimals=decimals, suffix=suffix, prefix=prefix)
        for i, (label, value, sub, count, fmt, decimals, suffix, prefix) in enumerate(kpi_data)
    )

    score_rows = [
        ("Categorization accuracy", cat_sec["accuracy"], _pct(cat_sec["accuracy"]),
         f"macro F1 {cat_sec['macro_f1']:.4f}, coverage {_pct(cat_sec['coverage'], 1)}"),
        ("Treatment accuracy", tre["accuracy"], _pct(tre["accuracy"]),
         f"support {tre['support']:,} labelled transactions"),
        ("Local-period accuracy", per["local_month_accuracy"], _pct(per["local_month_accuracy"]),
         f"UTC baseline {_pct(per['utc_month_accuracy'])} across {per['boundary_cases']:,} boundary cases"),
        ("Recurring precision", rec["precision"], f"{rec['precision']:.3f}",
         "matched series of all detected series"),
        ("Recurring recall", rec["recall"], f"{rec['recall']:.3f}",
         "detectable ground-truth series found"),
        ("Recurring F1", rec["f1"], f"{rec['f1']:.3f}",
         f"skip recall {_pct(rec['skip_recall'], 1)}, skip precision {_pct(rec['skip_precision'], 1)}"),
        ("Budget taxonomy resolution", bud["resolution_accuracy"], _pct(bud["resolution_accuracy"], 1),
         f"{bud['resolved_alias_rows']:,} legacy-code rows resolved, {bud['unresolved_rows']} unresolved"),
        ("Exception handling score", float(sec["exception_handling_score"]),
         f"{float(sec['exception_handling_score']):.2f}",
         f"{bud['naive_mismatch_false_under_rows']:,} false 'under' rows avoided by alias mapping"),
    ]
    scorecard = _table(
        ["Metric", "Result", "Score", "Detail"],
        [
            [_esc(label), _esc(value), _meter(frac), _esc(detail)]
            for label, frac, value, detail in score_rows
        ],
        aligns=["left", "right", "left", "left"],
        raw=True,
    )
    extra_rows = [
        [_esc("Strict net spend"), _esc(_money(trf["strict_net_spend_usd"], 2)),
         _pill("in report", "info"), _esc(f"naive overstatement avoided {_money(trf['naive_spend_overstatement_usd'], 2)}")],
        [_esc("Transfers / refunds handled"),
         _esc(f"{_int(trf['transfers_handled_as_transfer'])} / {_int(trf['refunds_handled_as_refund'])}"),
         _pill("rules", "info"),
         _esc(f"{_int(trf['transfer_transactions'])} transfer legs, {_int(trf['refund_transactions'])} refund credits")],
        [_esc("Data quality"), _esc(_pct(1 - float(sec["data_quality"]["uncategorized_rate"]), 1)),
         _meter(1 - float(sec["data_quality"]["uncategorized_rate"])),
         _esc(f"fallback {_pct(sec['data_quality']['fallback_rate'], 1)}, mean confidence {float(sec['data_quality']['mean_confidence']):.3f}")],
        [_esc("Validation"), _esc(f"PASS {vc['pass']}/{total_checks}"),
         _pill("PASS", "ok") if vc["fail"] == 0 else _pill("FAIL", "bad"),
         _esc(f"{vc['warn']} warnings, {vc['fail']} failures across PK/FK/reconciliation checks")],
    ]
    scorecard += _table(["Additional measure", "Value", "Status", "Detail"], extra_rows,
                        aligns=["left", "right", "left", "left"], raw=True)

    monthly_svg = _svg_monthly(months, spend_vals, income_vals)
    monthly_total_spend = sum(spend_vals)
    monthly_total_income = sum(income_vals)
    monthly_rows = []
    for m, s, inc in zip(months, spend_vals, income_vals):
        monthly_rows.append([
            MONTH_ABBR.get(str(m)[5:7], str(m)[5:7]) + " " + str(m)[:4],
            _money(s, 2), _money(inc, 2), _money(s - inc, 2),
        ])
    monthly_table = _table(["Month", "Strict spend", "Income", "Spend - income"], monthly_rows,
                           aligns=["left", "right", "right", "right"])
    cat_svg = _svg_hbar(cat_items)

    donut = _svg_donut(donut_items)
    status_list = "".join(
        f'<div class="status-row"><span class="left"><span class="swatch" style="background:{STATUS_COLORS.get(k, "#94a3b8")}"></span>'
        f'{_esc(k.capitalize())} {_pill(k, STATUS_PILL.get(k, "info"))}</span>'
        f'<span class="num">{_int(v)} rows &middot; {_pct(v / len(budgets), 1)}</span></div>'
        for k, v in sorted(status_counts.items(), key=lambda kv: -kv[1])
    )

    over_rows = [
        [
            _esc(r["user_id"]),
            _esc(r["period_month"]),
            _esc(r["resolved_category_code"]),
            _esc(_money(r["budget_amount_usd"], 2)),
            _esc(_money(r["actual_spend_usd"], 2)),
            _pill(_money(r["variance_usd"], 2), "bad"),
            _esc(f"{float(r['usage_pct']):.1f}%"),
        ]
        for r in over.to_dict("records")
    ]
    over_table = _table(
        ["User", "Month", "Category", "Budget", "Actual", "Over by", "Usage"],
        over_rows,
        aligns=["left", "left", "left", "right", "right", "right", "right"],
        raw=True,
    )

    rec_kpi_data = [
        ("Series detected", _int(rec["detected_series"]), f"of {rec['detectable_series']:,} detectable",
         rec["detected_series"], "num", 0, "", ""),
        ("Matched", _int(rec["matched_series"]), f"{rec['false_positives']} FP, {rec['false_negatives']} FN",
         rec["matched_series"], "num", 0, "", ""),
        ("Precision", f"{rec['precision']:.3f}", "of detected, truly recurring",
         rec["precision"], "num", 3, "", ""),
        ("Recall", f"{rec['recall']:.3f}", "of ground-truth detectable series",
         rec["recall"], "num", 3, "", ""),
        ("Skips flagged", _int(rec["skip_series_flagged"]), f"of {rec['skip_series']} seeded skips",
         rec["skip_series_flagged"], "num", 0, "", ""),
        ("Expected monthly", _money_c(rec_expected), "sum of series expected amounts",
         rec_expected, "moneyc", 0, "", ""),
        ("Amount MAPE", _pct(rec["amount_mape_matched"], 1), "matched series only",
         rec["amount_mape_matched"], "pct", 1, "", ""),
        ("Next-date error", f"{rec['next_date_median_abs_error_days']:.1f} d",
         f"median over {rec['next_date_compared']:,} series",
         rec["next_date_median_abs_error_days"], "num", 1, " d", ""),
    ]
    rec_kpis = "".join(
        _kpi(label, value, sub, KPI_ACCENTS[(i + 3) % len(KPI_ACCENTS)],
             count=count, fmt=fmt, decimals=decimals, suffix=suffix, prefix=prefix)
        for i, (label, value, sub, count, fmt, decimals, suffix, prefix) in enumerate(rec_kpi_data)
    )
    rec_status_rows = [
        [_esc(k), _pill(_int(v), "info"), _esc(_pct(v / max(len(recurring), 1), 1))]
        for k, v in sorted(rec_status.items())
    ]
    rec_status_table = _table(["Detection status", "Series", "Share"], rec_status_rows,
                              aligns=["left", "right", "right"], raw=True)
    rec_cat_rows = [[k, _int(v)] for k, v in rec_by_cat.items()]
    rec_cat_table = _table(["Top categories", "Series"], rec_cat_rows, aligns=["left", "right"])

    anomaly_table = _table(
        ["Issue type", "Cases", "Impacted rows", "Severity", "Observed behaviour", "Expected resolution"],
        [
            [
                _esc(r["issue_type"]),
                _esc(_int(r["anomalies"])),
                _esc(_int(r["impact"])),
                _pill(r["severity"], SEVERITY_PILL.get(str(r["severity"]), "info")),
                _esc(r["behavior"]),
                _esc(r["resolution"]),
            ]
            for r in anomaly_rows.to_dict("records")
        ],
        aligns=["left", "right", "right", "left", "left", "left"],
        raw=True,
    )

    explorer_section = ""
    explorer_json = ""
    if explorer is not None:
        ex_records = []
        for r in explorer.to_dict("records"):
            ex_records.append({
                "id": str(r["transaction_id"]),
                "d": str(r["transaction_date"]),
                "u": str(r["user_id"]),
                "x": str(r["descriptor"]),
                "a": round(float(r["amount_usd"]), 2),
                "p": str(r["predicted_category_code"]),
                "t": str(r["true_category_code"]),
                "c": round(float(r["confidence"]), 3) if pd.notna(r["confidence"]) else None,
                "i": str(r["issue_type"]) if pd.notna(r["issue_type"]) else "none",
            })
        explorer_json = json.dumps(ex_records, separators=(",", ":"), ensure_ascii=True).replace("</", "<\\/")
        n_mismatch = sum(1 for r in ex_records if r["p"] != r["t"])
        n_issue = sum(1 for r in ex_records if r["i"] != "none")
        explorer_section = f"""
<section id="explorer">
  <div class="sec-head"><span class="dot" style="background:#ec4899;box-shadow:0 0 0 4px rgba(236,72,153,.16)"></span><h2>Data explorer</h2><span class="hint">sampled rows with predictions next to hidden ground truth</span></div>
  <div class="card">
    <h3>Transactions: predicted vs. true labels</h3>
    <div class="controls">
      <input id="ex-search" type="search" placeholder="Search descriptor, txn id, user..." aria-label="Search rows">
      <select id="ex-issue" aria-label="Filter by issue type"><option value="all">All issue types</option></select>
      <label><input type="checkbox" id="ex-mismatch"> Category mismatches only</label>
      <span id="ex-count" class="count-note"></span>
    </div>
    <div class="ex-scroll">
      <table>
        <thead><tr><th>Date</th><th>Transaction</th><th>Descriptor</th><th class="right">Amount</th>
        <th>Predicted</th><th>Ground truth</th><th>Issue label</th><th class="right">Conf.</th></tr></thead>
        <tbody id="ex-body"></tbody>
      </table>
    </div>
    <div class="note">Sample of {_int(len(ex_records))} rows from the full dataset: {_int(n_issue)} carry injected edge-case labels and {_int(n_mismatch)} differ from the rule engine's prediction (shown in red). The pipeline never sees the ground-truth columns; they live only in <code>ground_truth/</code> for evaluation.</div>
  </div>
</section>"""

    reports = [
        ("validation/validation_summary.md", "Validation summary",
         f"{vc['pass']} checks with expected outcomes, reconciliation, and known exceptions"),
        ("outputs/evaluation_report.md", "Evaluation report",
         "Metrics against ground truth: per-class scores, confusions and distributions"),
        ("outputs/reproducibility_report.md", "Reproducibility report",
         "Two fixed-seed runs compared row counts and SHA-256 checksums"),
        ("metadata/manifest.json", "Manifest",
         "Per-file row counts, byte sizes and SHA-256 checksums"),
        ("metadata/source_manifest.json", "Source manifest",
         "Data provenance, fields, transformations and licensing note"),
        ("../docs/data_dictionary.md", "Data dictionary",
         "Full field-level documentation for every export"),
        ("../schema.sql", "Database schema",
         "DDL with primary keys, foreign keys, enums and indexes"),
        ("../README.md", "Project README",
         "Workflow, business rules, exception handling and metrics"),
    ]
    report_cards = "".join(
        f'<a class="report" href="{_esc(href)}"><div class="r-title">{_esc(title)}</div>'
        f'<div class="r-desc">{_esc(desc)}</div></a>'
        for href, title, desc in reports
    )

    generated_at = manifest["generated_at"]
    nav_items = [
        ("overview", "Overview"), ("spend", "Spend"), ("budgets", "Budgets"),
        ("recurring", "Recurring"), ("exceptions", "Exceptions"),
    ]
    if explorer_section:
        nav_items.append(("explorer", "Explorer"))
    nav_items.append(("reports", "Reports"))
    nav_html = "".join(f'<a href="#{eid}">{label}</a>' for eid, label in nav_items)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Household Spend Intelligence - Dashboard</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="head-top">
      <div>
        <h1>Household Spend Intelligence</h1>
        <div class="tagline">Deterministic synthetic household spending analytics &mdash; categorization, recurring payment detection, budget comparison, labelled exceptions, and reproducible evaluation.</div>
        <div class="badges">
          <span class="badge">seed {_int(manifest['seed'])}</span>
          <span class="badge">{_esc(manifest['scale'])} scale</span>
          <span class="badge">{_int(counts['transactions'])} transactions</span>
          <span class="badge">{_int(counts['profiles'])} profiles</span>
          <span class="badge">generated {_esc(generated_at)}</span>
        </div>
      </div>
      <div class="head-right">
        <div class="status-box">
          <div class="s-label">Validation</div>
          <div class="s-value">{_esc(validation['status'])}</div>
          <div class="s-sub">{vc['pass']} passed &middot; {vc['warn']} warn &middot; {vc['fail']} fail</div>
        </div>
        <button id="theme-btn" class="theme-btn" type="button" aria-label="Toggle dark mode" title="Toggle dark mode">
          <svg class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          <svg class="icon-sun" viewBox="0 0 24 24"><path d="M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0-15a1 1 0 0 1 1 1v2a1 1 0 1 1-2 0V3a1 1 0 0 1 1-1zm0 18a1 1 0 0 1 1 1v2a1 1 0 1 1-2 0v-2a1 1 0 0 1 1-1zM4 12a1 1 0 0 1 1-1h2a1 1 0 1 1 0 2H5a1 1 0 0 1-1-1zm14 0a1 1 0 0 1 1-1h2a1 1 0 1 1 0 2h-2a1 1 0 0 1-1-1zM5.64 5.64a1 1 0 0 1 1.41 0l1.42 1.42A1 1 0 0 1 7.06 8.46L5.64 7.05a1 1 0 0 1 0-1.41zm11.31 11.31a1 1 0 0 1 1.41 0l1.42 1.42a1 1 0 0 1-1.41 1.41l-1.42-1.41a1 1 0 0 1 0-1.42zM18.36 5.64a1 1 0 0 1 0 1.41l-1.42 1.42A1 1 0 0 1 15.54 7.05l1.41-1.41a1 1 0 0 1 1.41 0zM8.46 15.54a1 1 0 0 1 0 1.41l-1.42 1.42a1 1 0 1 1-1.41-1.41l1.41-1.42a1 1 0 0 1 1.42 0z"/></svg>
        </button>
      </div>
    </div>
    <nav>{nav_html}</nav>
  </div>
</header>
<div class="wrap">

<section id="overview">
  <div class="sec-head"><span class="dot"></span><h2>Overview</h2><span class="hint">headline figures and scorecard against ground truth</span></div>
  <div class="grid kpis">{kpis}</div>
  <div class="card" style="margin-top:16px">
    <h3>Scorecard against ground truth &mdash; click any column header to sort</h3>
    {scorecard}
    <div class="note">Score bars: green at &ge;95%, amber at &ge;80%, red below. Ground truth is held in <code>dataset/ground_truth/</code> and never joined into pipeline features.</div>
  </div>
</section>

<section id="spend">
  <div class="sec-head"><span class="dot" style="background:#3b82f6;box-shadow:0 0 0 4px rgba(59,130,246,.16)"></span><h2>Spend and income</h2><span class="hint">strict ledger, local period months</span></div>
  <div class="stack">
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
        <h3 style="margin:0">Monthly spend versus income (all households)</h3>
        <div class="seg" data-seg>
          <button type="button" class="on" data-pane-target="spend-chart">Chart</button>
          <button type="button" data-pane-target="spend-table">Table</button>
        </div>
      </div>
      <div data-pane="spend-chart" style="margin-top:14px">
        {monthly_svg}
        <div class="legend">
          <span class="item"><span class="swatch" style="background:#3b82f6"></span>Strict spend &mdash; {_money_c(monthly_total_spend)} annual</span>
          <span class="item"><span class="swatch" style="background:#10b981"></span>Income &mdash; {_money_c(monthly_total_income)} annual</span>
        </div>
      </div>
      <div data-pane="spend-table" class="hidden" style="margin-top:14px">{monthly_table}</div>
      <div class="note">Strict spend excludes both transfer legs and offsets refunds against their original category. Periods use the local transaction date, so UTC and local months differ at boundaries.</div>
    </div>
    <div class="card">
      <h3>Net spend by category (top 12)</h3>
      {cat_svg}
      <div class="note">Refunds are netted into the refunded purchase category through the pipeline treatment rules, so bars show net household outflow. Hover any bar for exact values.</div>
    </div>
  </div>
</section>

<section id="budgets">
  <div class="sec-head"><span class="dot" style="background:#10b981;box-shadow:0 0 0 4px rgba(16,185,129,.16)"></span><h2>Budget comparison</h2><span class="hint">{_int(counts['budgets'])} monthly category budgets vs actuals</span></div>
  <div class="split">
    <div class="card">
      <h3>Budget status distribution</h3>
      <div class="donut-wrap">{donut}</div>
      <div class="status-list">{status_list}</div>
      <div class="note">Budget {_money(budget_total)} vs actual {_money(actual_total)} &rarr; variance {_money(variance_total)}.</div>
    </div>
    <div class="card">
      <h3>Most over-budget households (top 10) &mdash; sortable</h3>
      {over_table}
      <div class="note">Legacy category codes (FOOD, TRANSPORTATION, SUBSCRIPTIONS, UTIL, MISC) are resolved through the <code>category_alias</code> table before comparison, avoiding {bud['naive_mismatch_false_under_rows']:,} false "under" results.</div>
    </div>
  </div>
</section>

<section id="recurring">
  <div class="sec-head"><span class="dot" style="background:#8b5cf6;box-shadow:0 0 0 4px rgba(139,92,246,.16)"></span><h2>Recurring payment detection</h2><span class="hint">detector output vs separate ground truth</span></div>
  <div class="grid mini">{rec_kpis}</div>
  <div class="split2" style="margin-top:16px">
    <div class="card">
      <h3>Detected series by status</h3>
      {rec_status_table}
      <div class="note">{_int(rec_missed)} series have missed occurrences and are reported as gaps rather than silently shifted.</div>
    </div>
    <div class="card">
      <h3>Detected series by category (top 8)</h3>
      {rec_cat_table}
      <div class="note">Ground truth series use separate <code>TRU-</code> IDs so detected and true series can never be confused.</div>
    </div>
  </div>
</section>

<section id="exceptions">
  <div class="sec-head"><span class="dot" style="background:#ef4444;box-shadow:0 0 0 4px rgba(239,68,68,.16)"></span><h2>Labelled exceptions</h2><span class="hint">five required edge cases with ground truth and expected resolution</span></div>
  <div class="card">
    {anomaly_table}
    <div class="note">Anomalies are injected deliberately and labelled in <code>ground_truth/anomaly_manifest.csv</code> with impact counts and expected resolution. Every case is scored by <code>evaluate</code>.</div>
  </div>
</section>
{explorer_section}
<section id="reports">
  <div class="sec-head"><span class="dot" style="background:#f59e0b;box-shadow:0 0 0 4px rgba(245,158,11,.16)"></span><h2>Reports and documentation</h2><span class="hint">every claim above is backed by these artifacts</span></div>
  <div class="reports">{report_cards}</div>
</section>

<footer class="footer">
  Synthetic data for evaluation only &middot; generator {_esc(manifest['generator_version'])} &middot; schema {_esc(manifest['schema_version'])} &middot; project {_esc(manifest['project_version'])} &middot; {_esc(generated_at)} &middot; no real personal data.
</footer>
</div>
<script type="application/json" id="ex-data">{explorer_json}</script>
<script>{_JS}</script>
</body>
</html>
"""

    out = root / "dashboard.html"
    out.write_text(html_doc, encoding="utf-8")
    return out
