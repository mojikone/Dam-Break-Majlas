# -*- coding: utf-8 -*-
"""Charts from the dam-break results (W2/04_data/results/<plan>/connection.csv, boundary_*.csv, summary.json).
Output W2/02_figures/charts/results_*.png. Same palette and rules as W1 charts.py."""
import os, sys, json, glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(W2, "04_data", "results"); OUT = os.path.join(W2, "02_figures", "charts"); os.makedirs(OUT, exist_ok=True)
C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", magenta="#e87ba4", violet="#4a3aa7", red="#e34948", ink="#0b0b0b", ink2="#52514e", grid="#d9d8d3")
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": C["grid"],
                     "grid.linewidth": 0.6, "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white"})
thousands = FuncFormatter(lambda x, p: f"{x:,.0f}")
ORDER = ["p32", "p33", "p30", "p31", "p28", "p29", "p34", "p35", "p36", "p37", "p38", "p39", "p40", "p41", "p48", "p42"]
COLORS = [C["blue"], C["orange"], C["aqua"], C["yellow"], C["magenta"], C["green"] if "green" in C else "#008300", C["violet"], C["red"]]

LEGEND = {"p28": "S1D: sunny day, base breach 85 m in 6 min, C = 1.66", "p29": "S1N: sunny day, base breach, no dikes",
          "p30": "S2D: PMF, base breach 85 m in 6 min, C = 1.66", "p31": "S2N: PMF, base breach, no dikes",
          "p32": "S3D: PMF, no failure", "p33": "S3N: PMF, no failure, no dikes",
          "p34": "S2D-W51: breach 51 m", "p35": "S2D-W119: breach 119 m", "p36": "S2D-W153: breach 153 m",
          "p37": "S1D-W51: breach 51 m", "p38": "S1D-W153: breach 153 m", "p39": "S2D-T18m: breach in 18 min", "p40": "S2D-T3m: breach in 3 min",
          "p41": "S1D-C1.44: C = 1.44", "p42": "S2D-F10000: 10,000-yr flood, base breach", "p48": "S3D-F10000: 10,000-yr flood, no failure"}

SHORT = {"p28": "S1D: sunny day, base breach", "p29": "S1N: sunny day, no dikes", "p30": "S2D: PMF failure, base breach",
         "p35": "S2D-W119: breach 119 m", "p34": "S2D-W51: breach 51 m", "p36": "S2D-W153: breach 153 m", "p37": "S1D-W51: breach 51 m",
         "p38": "S1D-W153: breach 153 m", "p39": "S2D-T18m: breach in 18 min", "p40": "S2D-T3m: breach in 3 min", "p41": "S1D-C1.44: C = 1.44",
         "p32": "S3D: PMF, no failure", "p48": "S3D-F10000: 10,000-yr, no failure", "p42": "S2D-F10000: 10,000-yr failure"}   # axis labels of the bar chart

def name(code):
    """legend text: scenario and the breach conditions that distinguish it (user, 2026-09-23)"""
    if code in LEGEND: return LEGEND[code]
    p = os.path.join(RES, code, "summary.json")
    return json.load(open(p)).get("plan_title", code) if os.path.exists(p) else code

def load(code):
    p = os.path.join(RES, code, "connection.csv")
    return pd.read_csv(p) if os.path.exists(p) else None

def smooth(x, y, per=12):
    """display smoothing: a shape-preserving cubic interpolation (PCHIP) between the output points, `per` points per interval. It passes
    through every value, so peaks and timing are exact; only the straight segments between output points become curves."""
    from scipy.interpolate import PchipInterpolator
    x = np.asarray(x, float); y = np.asarray(y, float); keep = np.isfinite(x) & np.isfinite(y); x, y = x[keep], y[keep]
    if len(x) < 4: return x, y
    xs = np.linspace(x[0], x[-1], per * (len(x) - 1) + 1); return xs, PchipInterpolator(x, y)(xs)

def chart_dam_hydrographs(codes, fname, title_note="", xlim=None):
    fig, ax = plt.subplots(figsize=(6.3, 3.4)); k = 0; labels = []
    for code in codes:
        d = load(code)
        if d is None: continue
        xs, ys = smooth(d.time_h.to_numpy(), d.total_flow.to_numpy())
        ax.plot(xs, ys, color=COLORS[k % len(COLORS)], lw=1.8, label=name(code))
        i = d.total_flow.idxmax(); labels.append((float(d.time_h[i]), float(d.total_flow[i]), f"{d.total_flow[i]:,.0f}", COLORS[k % len(COLORS)])); k += 1
    if k == 0: plt.close(fig); print("skipped (no results yet)", fname); return
    # peak labels: at each peak, just above and to the right; when two peaks sit within 12 % of each other the lower one is pushed down
    ymax = max(r[1] for r in labels); ax.set_ylim(0, ymax * 1.15); placed = []
    for tx, ty, txt, col in sorted(labels, key=lambda r: -r[1]):
        dy = 4
        for py in placed:
            if abs(py - ty) < 0.12 * ymax: dy -= 11
        placed.append(ty); ax.annotate(txt, (tx, ty), xytext=(-5, dy), textcoords="offset points", fontsize=7.5, color=col, ha="right")   # left of the peak: rising limbs are steep, so nothing is there
    if xlim: ax.set_xlim(*xlim)
    ax.set_xlabel("Time from start of run (h)"); ax.set_ylabel("Flow past the dam (m³/s)"); ax.yaxis.set_major_formatter(thousands); ax.legend(fontsize=7.5)
    fig.savefig(os.path.join(OUT, fname)); plt.close(fig); print("wrote", fname)

def chart_pool(codes, fname):
    fig, ax = plt.subplots(figsize=(6.3, 3.0)); k = 0
    for code in codes:
        d = load(code)
        if d is None: continue
        ax.plot(d.time_h, d.stage_hw, color=COLORS[k % len(COLORS)], lw=1.8, label=name(code)); k += 1
    # reference levels: labels at the right end, staggered so crest and parapet (1.2 m apart) do not collide; legend away from them
    for lev, lab, va in ((84.5, "full supply level 84.5", "bottom"), (95.5, "crest 95.5", "top"), (96.7, "parapet 96.7", "bottom")):
        ax.axhline(lev, color=C["ink2"], lw=0.7, ls="--"); ax.text(0.995, lev + (0.25 if va == "bottom" else -0.25), lab, fontsize=7, color=C["ink2"], ha="right", va=va, transform=ax.get_yaxis_transform())
    ax.set_xlabel("Time from start of run (h)"); ax.set_ylabel("Reservoir level at the dam (m a.s.l.)"); ax.legend(fontsize=7.5, loc="center right")
    fig.savefig(os.path.join(OUT, fname)); plt.close(fig); print("wrote", fname)

def chart_peaks(codes, fname):
    rows = []
    for code in codes:
        p = os.path.join(RES, code, "summary.json")
        if os.path.exists(p): s = json.load(open(p)); rows.append((SHORT.get(code, name(code)), s.get("peak_total_flow_m3s", 0), s.get("inundated_area_km2_gt0.3m", 0)))
    if not rows: return
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 0.35 * len(rows) + 1.2)); y = np.arange(len(rows))
    for ax, i, lab, col in ((axes[0], 1, "Peak flow past the dam (m³/s)", C["blue"]), (axes[1], 2, "Flooded area above 0.3 m (km²)", C["orange"])):
        vals = [r[i] for r in rows]; ax.barh(y, vals, color=col, height=0.6); ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7.5); ax.invert_yaxis()
        ax.set_xlabel(lab); ax.xaxis.set_major_formatter(thousands); ax.grid(axis="y", visible=False); xm = max(vals) * 1.3 if max(vals) > 0 else 1; ax.set_xlim(0, xm)
        for yi, v in zip(y, vals): ax.text(xm * 0.99, yi, f"{v:,.0f}" if i == 1 else f"{v:.1f}", ha="right", va="center", fontsize=7.5)
    axes[1].tick_params(labelleft=False); fig.tight_layout(w_pad=1.2); fig.savefig(os.path.join(OUT, fname)); plt.close(fig); print("wrote", fname)

def read_flow_file(u):
    """boundary tables of a HEC-RAS flow file: {line name: (hours, values)}; '' = rain on the 2D area"""
    import re
    t = open(os.path.join(W2, "..", "HEC-RAS Majlas", f"Majlas.{u}"), encoding="latin-1").read().replace("\r\n", "\n"); out = {}
    for b in re.split(r"\n(?=Boundary Location=)", t)[1:]:
        name = b.split("\n")[0][18:].split(",")[7].strip(); m = re.search(r"(Flow|Precipitation) Hydrograph= (\d+)", b); iv = re.search(r"Interval=(\S+)", b)
        if not m: continue
        n = int(m.group(2)); lines = b.split("\n"); start = next(i for i, l in enumerate(lines) if l.startswith(m.group(1) + " Hydrograph=")) + 1
        vals = []
        for s in lines[start:]:                        # fixed 8-character columns; a value that fills all 8 has no leading space
            if "=" in s or len(vals) >= n: break
            vals += [float(s[k:k + 8]) for k in range(0, len(s), 8) if s[k:k + 8].strip()]
        vals = vals[:n]
        step = {"5MIN": 5, "10MIN": 10, "1HOUR": 60}[iv.group(1)] / 60.0
        out[name] = (np.arange(n) * step, np.array(vals))
    return out

def chart_inputs(fname="results_inputs_hydrographs.png"):
    """the three inflow hydrographs and the hyetograph for the PMF and the 10,000-year flood, as fed into HEC-RAS"""
    pmf, k10 = read_flow_file("u28"), read_flow_file("u29")
    fig, axes = plt.subplots(2, 1, figsize=(6.3, 5.2), sharex=True, gridspec_kw={"height_ratios": [1, 2.2]})
    ax = axes[1]
    for (nm, lab), col in zip((("Majlas Dam", "Reservoir inflow"), ("Jsouth", "Southern catchment"), ("J11", "Side wadi J11")), (C["blue"], C["orange"], C["aqua"])):
        h, q = pmf[nm]; ax.plot(h, q, color=col, lw=1.8, label=f"{lab}, PMF")
        h, q = k10[nm]; ax.plot(h, q, color=col, lw=1.2, ls="--", label=f"{lab}, 10,000-yr")
    ax.set_xlim(0, 48); ax.set_ylabel("Inflow (m³/s)"); ax.set_xlabel("Time from the start of the storm (h)"); ax.yaxis.set_major_formatter(thousands); ax.legend(fontsize=7, ncol=2)
    ax = axes[0]; h, p = pmf[""]; ax.bar(h, p, width=10 / 60, color=C["blue"], label="PMP"); h2, p2 = k10[""]; ax.bar(h2, p2, width=10 / 60, color=C["orange"], alpha=0.7, label="10,000-yr")
    ax.set_ylabel("Rain (mm per 10 min)"); ax.legend(fontsize=7); ax.set_title("Rain on the 2D area (areal factor 0.76 applied) and inflows at the three boundary lines", fontsize=8.5, loc="left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fname)); plt.close(fig); print("wrote", fname)

def chart_glance(codes=("p28", "p32", "p30"), fname="results_at_a_glance.png"):
    """one panel per key number for the base scenarios: peak flow at the dam, flooded area, people in the flooded area"""
    rows = []
    for code in codes:
        p = os.path.join(RES, code, "summary.json")
        if not os.path.exists(p): continue
        s = json.load(open(p)); c = os.path.join(RES, code, "consequences.json"); c = json.load(open(c)) if os.path.exists(c) else {}
        rows.append((name(code).split(":")[0], s.get("peak_total_flow_m3s", 0), s.get("inundated_area_km2_gt0.3m", 0), c.get("par_total", 0), s.get("arrival_h_median")))
    if not rows: print("skipped (no results yet)", fname); return
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.3)); y = np.arange(len(rows))
    for ax, i, lab, col, fmt in ((axes[0], 1, "Peak flow at the dam (m³/s)", C["blue"], "{:,.0f}"), (axes[1], 2, "Flooded area > 0.3 m (km²)", C["orange"], "{:.1f}"), (axes[2], 3, "People in the flooded area", C["red"], "{:,.0f}")):
        vals = [r[i] for r in rows]; ax.barh(y, vals, color=col, height=0.55); ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=8); ax.invert_yaxis()
        ax.set_xlabel(lab, fontsize=7.5); ax.xaxis.set_major_formatter(thousands); ax.grid(axis="y", visible=False); xm = max(vals) * 1.35 if max(vals) > 0 else 1; ax.set_xlim(0, xm); ax.tick_params(axis="x", labelsize=7)
        for yi, v in zip(y, vals): ax.text(v + xm * 0.02, yi, fmt.format(v), va="center", fontsize=7.5)
    for ax in axes[1:]: ax.tick_params(labelleft=False)
    fig.tight_layout(w_pad=0.8); fig.savefig(os.path.join(OUT, fname)); plt.close(fig); print("wrote", fname)

def chart_hazard_people(codes, fname="results_people_by_hazard.png"):
    """people in the flooded area per hazard class, stacked, one bar per scenario"""
    HZC = {"H1": "#0000ff", "H2": "#00ecff", "H3": "#00a504", "H4": "#00ff30", "H5": "#fff900", "H6": "#f41f1f"}
    rows = []
    for code in codes:
        c = os.path.join(RES, code, "consequences.json")
        if os.path.exists(c): d = json.load(open(c)); rows.append((name(code).split(":")[0], [d.get(f"par_H{i}", 0) for i in range(1, 7)]))
    if not rows: print("skipped (no results yet)", fname); return
    fig, ax = plt.subplots(figsize=(6.3, 0.45 * len(rows) + 1.4)); y = np.arange(len(rows)); left = np.zeros(len(rows))
    for i in range(6):
        vals = np.array([r[1][i] for r in rows]); ax.barh(y, vals, left=left, color=HZC[f"H{i + 1}"], height=0.6, label=f"H{i + 1}", edgecolor="white", lw=0.3); left += vals
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=8); ax.invert_yaxis(); ax.set_xlabel("People in the flooded area, by AIDR hazard class"); ax.xaxis.set_major_formatter(thousands)
    for yi, tot in zip(y, left): ax.text(tot * 1.01, yi, f"{tot:,.0f}", va="center", fontsize=7.5)
    ax.set_xlim(0, left.max() * 1.15); ax.grid(axis="y", visible=False); ax.legend(fontsize=7, ncol=6, loc="lower right", bbox_to_anchor=(1, 1.0))
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fname)); plt.close(fig); print("wrote", fname)


def chart_warning(fname="results_people_vs_time.png"):
    """cumulative people reached against time: failures from the breach (minutes), the PMF from the start of the storm (hours).
    'Reached' = the depth rises 0.3 m above the pre-event state (for a flood-day failure: above the PMF at the same instant)."""
    import json
    def W(code):
        p = os.path.join(RES, code, "warning.json"); return json.load(open(p)) if os.path.exists(p) else None
    left = [("p28", C["blue"], "-", 2.0), ("p29", C["blue"], "--", 1.2), ("p37", C["aqua"], "-", 1.2), ("p38", C["yellow"], "-", 1.2),
            ("p30", C["orange"], "-", 2.0), ("p35", C["orange"], "--", 1.2), ("p34", C["red"], "--", 1.0), ("p36", C["magenta"], "--", 1.0),
            ("p40", C["violet"], ":", 1.0), ("p39", C["violet"], "--", 1.0), ("p42", C["ink2"], "--", 1.0)]
    right = [("p32", C["blue"], "-", 2.0), ("p48", C["blue"], "--", 1.2)]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.0), gridspec_kw={"width_ratios": [1.3, 1]})
    for ax, rows, scale, xl, xlab in ((axes[0], left, 60.0, (0, 120), "Minutes after the breach"), (axes[1], right, 1.0, (0, 18), "Hours after the start of the storm")):
        for code, col, ls, lw in rows:
            w = W(code)
            if w is None: continue
            t = np.array(w["curve"]["t_h"]) * scale; y = np.array(w["curve"]["people"])
            ax.step(t, y, where="post", color=col, ls=ls, lw=lw, label=SHORT.get(code, name(code)))
        ax.set_xlim(*xl); ax.set_xlabel(xlab); ax.yaxis.set_major_formatter(thousands); ax.legend(fontsize=6.2, loc="lower right")
        ax.set_ylim(0, None)
    axes[0].set_ylabel("People reached (cumulative)")
    fig.tight_layout(w_pad=1.0); fig.savefig(os.path.join(OUT, fname)); plt.close(fig); print("wrote", fname)

if __name__ == "__main__":
    try: chart_inputs()
    except Exception as e: print("inputs chart failed:", e)
    chart_glance()
    chart_hazard_people([c for c in ORDER if os.path.exists(os.path.join(RES, c, "consequences.json"))])
    have = [c for c in ORDER if os.path.exists(os.path.join(RES, c, "connection.csv"))]
    chart_dam_hydrographs([c for c in have if c in ("p32", "p30", "p28")], "results_dam_hydrographs_base_dikes.png")
    chart_dam_hydrographs([c for c in have if c in ("p28", "p29")], "results_dam_hydrographs_sunny_dikes.png", xlim=(1.5, 6))     # S1D vs S1N
    chart_dam_hydrographs([c for c in have if c in ("p28", "p37", "p38")], "results_dam_hydrographs_sunny_width.png", xlim=(1.5, 6))
    chart_dam_hydrographs([c for c in have if c in ("p28", "p41")], "results_dam_hydrographs_sunny_coef.png", xlim=(1.5, 6))
    chart_dam_hydrographs([c for c in have if c in ("p30", "p34", "p35", "p36")], "results_dam_hydrographs_width.png")
    chart_dam_hydrographs([c for c in have if c in ("p30", "p39", "p40", "p42")], "results_dam_hydrographs_time_flood.png")
    chart_dam_hydrographs([c for c in have if c in ("p32", "p48")], "results_dam_hydrographs_nofail_floods.png")
    chart_pool([c for c in have if c in ("p32", "p30", "p28")], "results_pool_levels.png")
    chart_peaks(have, "results_peaks_and_areas.png")
    chart_warning()
