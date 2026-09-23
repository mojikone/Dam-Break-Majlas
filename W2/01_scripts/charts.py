# -*- coding: utf-8 -*-
"""Charts for the W1 methodology report. Every number is read from data_facts.py or a named data file.
Output: W1/02_figures/charts/*.png (300 dpi). Palette: validated categorical set from the dataviz skill
(blue #2a78d6, orange #eb6834, aqua #1baf7a, yellow #eda100, magenta #e87ba4, violet #4a3aa7, red #e34948).
"""
import os, sys, math
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data_facts as F

OUT = os.path.join(HERE, "..", "02_figures", "charts")
os.makedirs(OUT, exist_ok=True)
C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", magenta="#e87ba4",
         green="#008300", violet="#4a3aa7", red="#e34948", ink="#0b0b0b", ink2="#52514e", grid="#d9d8d3", surf="#ffffff")
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.edgecolor": C["ink2"], "axes.labelcolor": C["ink"],
                     "xtick.color": C["ink2"], "ytick.color": C["ink2"], "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": C["grid"], "grid.linewidth": 0.6, "legend.frameon": False,
                     "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white"})
thousands = FuncFormatter(lambda x, p: f"{x:,.0f}")

def save(fig, name):
    p = os.path.join(OUT, name); fig.savefig(p); plt.close(fig); print("wrote", p)

# ---------------------------------------------------------------- 1. inflow hydrographs
def chart_hydrographs():
    d = pd.read_csv(os.path.join(HERE, "..", "04_data", "majlas_inflow_hydrographs.csv"))
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    series = [("PMF", "PMF (probable maximum flood)", C["red"]), ("10000yr", "10,000-year", C["orange"]),
              ("1000yr", "1,000-year", C["blue"]), ("200yr", "200-year (reservoir design flood)", C["aqua"])]
    for col, lab, col_ in series:
        ax.plot(d["hours"], d[col], color=col_, lw=1.8, label=lab)
        i = d[col].idxmax(); ax.annotate(f"{d[col].max():,.0f} m³/s", (d.loc[i, "hours"], d.loc[i, col]), xytext=(6, 2),
                                         textcoords="offset points", fontsize=8, color=C["ink"])
    ax.set_xlim(0, 48); ax.set_xlabel("Time from start of storm (hours)"); ax.set_ylabel("Inflow to the reservoir (m³/s)")
    ax.yaxis.set_major_formatter(thousands); ax.legend(loc="upper right", fontsize=8)
    save(fig, "chart_inflow_hydrographs.png")

# ---------------------------------------------------------------- 2. design floods by return period
def chart_design_floods():
    t = F.DESIGN_FLOODS  # list of (label, years, rain_mm, peak_m3s, vol_Mm3)
    labs = [r[0] for r in t]; peak = [r[3] for r in t]; vol = [r[4] for r in t]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.0), sharey=False)
    for ax, vals, lab, col in [(axes[0], peak, "Peak inflow (m³/s)", C["blue"]), (axes[1], vol, "Flood volume (Mm³)", C["orange"])]:
        y = np.arange(len(labs))
        ax.barh(y, vals, color=col, height=0.62)
        ax.set_yticks(y); ax.set_yticklabels(labs); ax.invert_yaxis(); ax.set_xlabel(lab)
        ax.xaxis.set_major_formatter(thousands); ax.grid(axis="y", visible=False)
        xmax = max(vals) * 1.28; ax.set_xlim(0, xmax)
        for yi, v in zip(y, vals):
            ax.text(xmax * 0.99, yi, f"{v:,.0f}", va="center", ha="right", fontsize=8, color=C["ink"])
    axes[1].tick_params(labelleft=False)
    fig.tight_layout(w_pad=1.5)
    save(fig, "chart_design_floods.png")

# ---------------------------------------------------------------- 3. reservoir elevation - storage / area
def chart_eav():
    x = pd.ExcelFile(F.HYPSO_XLSX); df = x.parse("0")
    el = df["Elevation"].values; vol = df["Volume (Mm3)"].values; area = df["Area (Km2)"].values
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.4), sharey=True)
    axes[0].plot(vol, el, color=C["blue"], lw=2); axes[0].set_xlabel("Storage (Mm³)")
    axes[1].plot(area, el, color=C["orange"], lw=2); axes[1].set_xlabel("Water surface area (km²)")
    axes[0].set_ylabel("Elevation (m a.s.l.)")
    for ax in axes:
        for lev, lab, col in [(F.FSL, f"FSL {F.FSL} m", C["aqua"]), (F.CREST, f"crest {F.CREST} m", C["ink2"]),
                              (F.PMF_LEVEL, f"PMF level {F.PMF_LEVEL} m", C["red"]), (F.BED_AT_DAM, f"wadi bed {F.BED_AT_DAM} m", C["yellow"])]:
            ax.axhline(lev, color=col, lw=0.9, ls="--")
        ax.set_ylim(15, 105)
    for lev, lab, col, dy in [(F.FSL, f"FSL {F.FSL} m", C["aqua"], 1.0), (F.PMF_LEVEL, f"PMF pool {F.PMF_LEVEL} m", C["red"], 1.0),
                              (F.BED_AT_DAM, f"wadi bed {F.BED_AT_DAM} m", C["yellow"], 1.0)]:
        axes[1].text(area.max() * 0.98, lev + dy, lab, ha="right", fontsize=7.5, color=col)
    axes[1].text(0.15, F.CREST - 3.6, f"dam crest {F.CREST} m", ha="left", fontsize=7.5, color=C["ink2"])
    axes[0].set_xlim(0, 240); axes[1].set_xlim(0, area.max() * 1.05)
    fig.tight_layout(w_pad=1.0)
    save(fig, "chart_reservoir_eav.png")

# ---------------------------------------------------------------- 4. spillway rating (ogee, free flow)
def chart_spillway_rating():
    H = np.linspace(0, F.PMF_LEVEL - F.SPILL_CREST, 200)
    fig, ax = plt.subplots(figsize=(6.3, 3.2))
    for c, lab, col in [(F.OGEE_C_LOW, f"C = {F.OGEE_C_LOW}", C["blue"]), (F.OGEE_C_HIGH, f"C = {F.OGEE_C_HIGH}", C["orange"])]:
        Q = c * F.SPILL_NET_LENGTH * H ** 1.5
        ax.plot(F.SPILL_CREST + H, Q, color=col, lw=1.8, label=f"Q = C · L · H^1.5, {lab}")
    ax.axhline(F.SPILL_QMAX, color=C["red"], lw=1, ls="--"); ax.text(F.SPILL_CREST + 0.3, F.SPILL_QMAX * 1.03, f"design capacity {F.SPILL_QMAX:,.0f} m³/s", color=C["red"], fontsize=8)
    ax.axvline(F.PMF_LEVEL, color=C["ink2"], lw=0.9, ls=":"); ax.text(F.PMF_LEVEL - 0.2, 1500, f"PMF pool {F.PMF_LEVEL} m", rotation=90, va="bottom", ha="right", fontsize=8, color=C["ink2"])
    ax.axvline(F.CREST, color=C["ink2"], lw=0.9, ls=":"); ax.text(F.CREST - 0.2, 1500, f"dam crest {F.CREST} m", rotation=90, va="bottom", ha="right", fontsize=8, color=C["ink2"])
    ax.set_xlabel("Reservoir level (m a.s.l.)"); ax.set_ylabel("Spillway discharge (m³/s)"); ax.yaxis.set_major_formatter(thousands)
    ax.set_xlim(F.SPILL_CREST, F.PMF_LEVEL + 0.5); ax.legend(loc="center left", bbox_to_anchor=(0.02, 0.62), fontsize=8)
    save(fig, "chart_spillway_rating.png")

# ---------------------------------------------------------------- 5. breach width: hand estimate of the first-minute peak
def chart_breach_peak():
    """Order-of-magnitude peak outflow the moment the breach is fully open, before drawdown, for the
    range of breach widths. Weir form Q = C·B·h^1.5 (C = 1.7 SI, HEC-RAS gravity-dam range) and the
    Ritter dry-bed solution Q = (8/27)·B·sqrt(g)·h^1.5. A check figure, not a result."""
    widths = F.BREACH_WIDTH_CASES  # list of (label, metres)
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.1), sharey=True)
    for ax, (pool, title) in zip(axes, [(F.FSL, f"Sunny day, pool {F.FSL} m"), (F.PMF_LEVEL, f"Flood day, pool {F.PMF_LEVEL} m")]):
        h = pool - F.BED_AT_DAM
        y = np.arange(len(widths))
        q_weir = [F.BREACH_WEIR_C * b * h ** 1.5 for _, b in widths]
        q_ritter = [(8 / 27) * b * math.sqrt(9.81) * h ** 1.5 for _, b in widths]
        ax.barh(y - 0.17, q_weir, height=0.32, color=C["blue"], label="weir equation, C = 1.7")
        ax.barh(y + 0.17, q_ritter, height=0.32, color=C["orange"], label="Ritter dam-break solution")
        for yi, a, b in zip(y, q_weir, q_ritter):
            ax.text(a + 2000, yi - 0.17, f"{a/1000:,.0f}k", va="center", fontsize=7.5, color=C["ink"])
            ax.text(b + 2000, yi + 0.17, f"{b/1000:,.0f}k", va="center", fontsize=7.5, color=C["ink"])
        ax.set_yticks(y); ax.set_yticklabels([f"{l}\n({b:.0f} m)" for l, b in widths]); ax.invert_yaxis()
        ax.set_title(title, fontsize=9, color=C["ink"]); ax.set_xlabel("Peak outflow at full breach (m³/s)")
        ax.xaxis.set_major_formatter(thousands); ax.grid(axis="y", visible=False); ax.set_xlim(0, 175000)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(w_pad=1.0, rect=(0, 0.04, 1, 1))
    save(fig, "chart_breach_peak_check.png")

# ---------------------------------------------------------------- 6. AIDR hazard classes H1..H6
def chart_hazard_classes():
    d = np.linspace(0, 5, 400)
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    cols = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#1c5cab", "#0d366b"]
    # curves: velocity limit for each class boundary as a function of depth
    def vlim(dv, dmax, vmax):
        v = np.where(d > 0, dv / np.maximum(d, 1e-6), vmax); v = np.minimum(v, vmax); v[d > dmax] = 0; return v
    bounds = [F.HAZ["H1"], F.HAZ["H2"], F.HAZ["H3"], F.HAZ["H4"], F.HAZ["H5"]]
    prev = np.zeros_like(d)
    labels = ["H1 safe for people, vehicles and buildings", "H2 unsafe for small vehicles", "H3 unsafe for vehicles, children and the elderly",
              "H4 unsafe for people and vehicles", "H5 unsafe for people and vehicles, buildings vulnerable", "H6 unsafe for everything, buildings fail"]
    top = 5.0
    for i, (dv, dmax, vmax) in enumerate(bounds):
        v = vlim(dv, dmax, vmax)
        ax.fill_between(d, prev, np.maximum(v, prev), color=cols[i], label=labels[i]); prev = np.maximum(v, prev)
    ax.fill_between(d, prev, top, color=cols[5], label=labels[5])
    ax.set_xlim(0, 5); ax.set_ylim(0, top); ax.set_xlabel("Depth (m)"); ax.set_ylabel("Velocity (m/s)"); ax.grid(False)
    ax.legend(loc="upper right", fontsize=7, framealpha=0.95, frameon=True, edgecolor="white")
    save(fig, "chart_hazard_classes.png")

# ---------------------------------------------------------------- 7. programme (indicative)
def chart_programme():
    tasks = F.PROGRAMME  # (task, start_week, weeks)
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    y = np.arange(len(tasks))
    for yi, (t, s, w) in zip(y, tasks):
        ax.barh(yi, w, left=s, height=0.55, color=C["blue"] if "review" not in t.lower() else C["orange"])
        ax.text(s + w + 0.15, yi, f"wk {s+1}" if w == 1 else f"wk {s+1}-{s+w}", va="center", fontsize=7.5, color=C["ink2"])
    ax.set_yticks(y); ax.set_yticklabels([t for t, _, _ in tasks], fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("Week from approval of this methodology"); ax.set_xlim(0, max(s + w for _, s, w in tasks) + 3); ax.grid(axis="y", visible=False)
    save(fig, "chart_programme.png")

# ---------------------------------------------------------------- 8. breach development in HEC-RAS (concept)
def chart_breach_progression():
    t = np.linspace(0, 1, 200)
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    ax.plot(t * F.BREACH_TIME_BASE * 60, t, color=C["blue"], lw=2, label="linear progression (used for concrete dams)")
    ax.plot(t * F.BREACH_TIME_BASE * 60, 0.5 - 0.5 * np.cos(np.pi * t), color=C["orange"], lw=2, ls="--", label="sine progression (typical for embankments)")
    ax.set_xlabel("Time from start of breach (minutes)"); ax.set_ylabel("Share of full breach\nopening (0 to 1)")
    ax.set_ylim(0, 1.05); ax.legend(loc="lower right", fontsize=8)
    ax.text(F.BREACH_TIME_BASE * 60 * 0.02, 0.93, f"full breach reached after {F.BREACH_TIME_BASE} h ({F.BREACH_TIME_BASE*60:.0f} min), base case", fontsize=8, color=C["ink2"])
    save(fig, "chart_breach_progression.png")

if __name__ == "__main__":
    chart_hydrographs(); chart_design_floods(); chart_eav(); chart_spillway_rating(); chart_breach_peak()
    chart_hazard_classes(); chart_programme(); chart_breach_progression()
