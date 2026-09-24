# -*- coding: utf-8 -*-
"""Content of the Wadi Majlas Dam Break Analysis Report (W2, Rev 01): method, scenarios, the model as built, results, consequences.

Rev 01 (2026-09-24) applies the user's review of the 23 September build: no reference to the methodology report (this document stands
alone), no scenario that was dropped, everything ordered S1 -> S2 -> S3, no file, model-element or run-time detail, the breach parameters
justified against the regression methods HEC-RAS offers, flowcharts introduced by a paragraph, the AIDR curves shown, descriptive
conclusions, a lean run register, no file appendix.

Everything numeric comes from W2/04_data/results/<plan>/ (summary.json, consequences.json, trigger.json, warning.json) and
data_facts.py. Figures: charts from results_charts.py, maps from qgis_result_maps.py, flowcharts from FigJam, dam drawings from the
design review. Style: simple words, one idea per sentence, footnotes for jargon, scenario names only, no volume error anywhere.
"""
import os, re, json, math
import data_facts as F
import ras_setup as S
from build_report import mr, mtxt, msub, msup, mfrac, mrad, mdelim      # Word-native equation helpers (OMML)

HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(W2, "04_data", "results")
CH = os.path.join(W2, "02_figures", "charts"); MAPS = os.path.join(W2, "02_figures", "maps", "results")
FC = os.path.join(W2, "02_figures", "flowcharts"); DECKFIG = os.path.join(W2, "02_figures", "deck")
FS = 16   # table font (8 pt)
REVIEW_DATE = "20 September 2026"       # design review presentation (user, 2026-09-24)

CODE = S.FIXED_P                                    # scenario id -> plan code
BASE = ["S1D", "S1N", "S2D", "S3D"]
SENS = ["S1D-W51", "S1D-W153", "S1D-C1.44", "S1D-T3m", "S1D-T18m", "S2D-W119", "S2D-F10000", "S3D-F10000"]
ORDER = ["S1D", "S1N", "S1D-W51", "S1D-W153", "S1D-C1.44", "S1D-T3m", "S1D-T18m", "S2D", "S2D-W119", "S2D-F10000", "S3D", "S3D-F10000"]
DESC = {"S1D": "sunny-day failure, dikes in place", "S1N": "sunny-day failure, no dikes", "S2D": "flood-day (PMF) failure, dikes in place",
        "S3D": "PMF without failure, dikes in place",
        "S1D-W51": "sunny-day failure, breach 51 m wide (three monoliths)", "S1D-W153": "sunny-day failure, breach 153 m wide (nine monoliths)",
        "S1D-C1.44": "sunny-day failure, breach weir coefficient 1.44", "S1D-T3m": "sunny-day failure, breach formed in 3 minutes",
        "S1D-T18m": "sunny-day failure, breach formed in 18 minutes", "S2D-W119": "flood-day failure, breach 119 m wide (seven monoliths)",
        "S2D-F10000": "flood-day failure during the 10,000-year flood", "S3D-F10000": "10,000-year flood without failure, dikes in place"}
FILLS = {"Fill": "reservoir fill, geometry with dikes", "FillN": "reservoir fill, geometry without dikes"}
WINDOW = {"S1D": "14 h", "S1N": "14 h", "S2D": "60 h", "S3D": "60 h", "S1D-W51": "14 h", "S1D-W153": "14 h", "S1D-C1.44": "14 h",
          "S1D-T3m": "14 h", "S1D-T18m": "14 h", "S2D-W119": "36 h", "S2D-F10000": "36 h", "S3D-F10000": "36 h", "Fill": "48 h", "FillN": "48 h"}

# ------------------------------------------------------------------ data access
def load(sid):
    """summary + consequences + trigger of one scenario, or None if the run has no products."""
    d = os.path.join(RES, CODE[sid]); p = os.path.join(d, "summary.json")
    if not os.path.exists(p): return None
    s = json.load(open(p))
    for name in ("consequences.json", "trigger.json"):
        q = os.path.join(d, name)
        if os.path.exists(q): s.update({f"{name[:-5]}_{k}": v for k, v in json.load(open(q)).items()})
    return s

def have(sid): return load(sid) is not None
def n0(x): return "-" if x is None else f"{x:,.0f}"
def n1(x): return "-" if x is None else f"{x:,.1f}"
def n2(x): return "-" if x is None else f"{x:,.2f}"
def hm(h):
    """hours -> '45 min' / '2 h' / '2 h 05 min'"""
    if h is None: return "-"
    m = int(round(h * 60)); return (f"{m // 60} h" if m % 60 == 0 else f"{m // 60} h {m % 60:02d} min") if m >= 60 else f"{m} min"
def mapfile(sid, kind, ext): return os.path.join(MAPS, f"{sid} {kind} {ext}.png")
def load_w(sid):
    """warning-time products of a scenario, or None"""
    p = os.path.join(RES, CODE[sid], "warning.json"); return json.load(open(p)) if os.path.exists(p) else None
def wt(h):
    """hours -> '5 min' / '1 h 05 min' / 'not reached'"""
    return "not reached" if h is None else ("< 5 min" if h < 1 / 12 - 1e-6 else hm(h))     # 5 min = the output step
def chart(name): return os.path.join(CH, name)
def peak_pool(s): return s.get("max_stage_hw") if s else None
def place(sid, name):
    w = load_w(sid); return None if not w else w.get("places", {}).get(name)
def reached(sid, band):
    """people reached within `band` hours (warning products), or None"""
    w = load_w(sid)
    if not w or band not in w["bands_h"]: return None
    return w["people_cum"][w["bands_h"].index(band)]
SHORE = "Shoreline, 'Outflow Sea' line"; TOWN = "Qurayat, residential centre"

DECISION = os.path.join(W2, "04_data", "dikes_decision.json")
def dikes_decision():
    return json.load(open(DECISION)) if os.path.exists(DECISION) else None

KEY_HDR = ["Scenario", "Description", "Peak flow (m³/s)", "Time of peak", "Max pool (m)", "Area (km²)", "Depth gorge / plain (m)", "People"]
KEY_W = [1.15, 2.0, 0.9, 0.9, 0.75, 0.7, 0.95, 0.75]
def key_rows(sids):
    """one row per scenario for the results tables; scenarios without products are left out"""
    rows = []
    for sid in sids:
        s = load(sid)
        if s is None: continue
        rows.append([sid, DESC[sid], n0(s.get("peak_total_flow_m3s")), hm(s.get("peak_time_h")), n2(peak_pool(s)),
                     n1(s.get("inundated_area_km2_gt0.3m")), f"{n0(s.get('max_depth_m'))} / {n1(s.get('max_depth_plain_m'))}", n0(s.get("consequences_par_total"))])
    return rows
KEY_NOTE = ("Peak flow: the largest flow past the dam (breach and spillway together). Max pool: the highest reservoir level, in m a.s.l. "
            "Area: the plain and wadi covered by more than 0.3 m of water, reservoir excluded. Depth: the largest depth in the gorge below the dam "
            "and on the plain. People: residents of the flooded area.")

def run_minutes():
    """solver minutes per plan from the run log (the last successful END line of each plan)"""
    out = {}
    p = os.path.join(W2, "04_data", "run_sequence.log")
    if not os.path.exists(p): return out
    for line in open(p, encoding="utf-8"):
        m = re.search(r"END\s+(p\d+)\s+ok=True (\d+) min", line)
        if m and int(m.group(2)) > 0: out[m.group(1)] = int(m.group(2))
    return out

# ------------------------------------------------------------------ the report
def content(d):
    s1d, s1n, s2d, s3d = (load(x) for x in BASE)
    w1, w2, w3 = load_w("S1D"), load_w("S2D"), load_w("S3D")
    # ============================================================ front matter
    d.H1("Abbreviations and Nomenclature", numbered=False)
    d.P("Terms and short names used in this report.")
    d.TBL(["Term", "Meaning"], [
        ["AIDR", "Australian Institute for Disaster Resilience; its flood hazard classes H1 to H6 are used here"],
        ["Breach", "The opening that forms in the dam when it fails"],
        ["EAP", "Emergency action plan"],
        ["FSL", f"Full supply level, {F.FSL} m a.s.l., the spillway crest"],
        ["HEC-RAS", "The two-dimensional hydraulic model used for the analysis (Hydrologic Engineering Center, River Analysis System)"],
        ["Monolith", f"One concrete block of the dam between two vertical joints; the dam has {F.N_BLOCKS} of them"],
        ["PAR", "Population at risk: people living in the flooded area"],
        ["PMF, PMP", "Probable maximum flood, probable maximum precipitation"],
        ["S1", "Sunny-day failure: the dam fails with the reservoir full and no flood in the wadi (S1D with the dikes, S1N without)"],
        ["S2", "Flood-day failure: the dam fails at the peak of the PMF (S2D)"],
        ["S3", "PMF without failure: the flood alone, the reference for what the failure adds (S3D)"],
        ["D, N", "With the downstream training dikes; without them"],
        ["S1D-W51, S1D-W153, S2D-W119", "Sensitivity runs with a breach 51, 153 or 119 m wide instead of 85 m"],
        ["S1D-T3m, S1D-T18m", "Sensitivity runs with the breach formed in 3 or 18 minutes instead of 6"],
        ["S1D-C1.44", "Sensitivity run with a breach weir coefficient of 1.44 instead of 1.66"],
        ["S2D-F10000, S3D-F10000", "The flood-day failure and the no-failure run repeated with the 10,000-year flood instead of the PMF"],
        ["m a.s.l.", "Metres above sea level"],
    ], "Abbreviations and terms.", "abbr", col_w=[1.6, 4.4], font_sz=FS)

    # ============================================================ executive summary
    d.H1("Executive Summary", numbered=False)
    d.P(f"This report presents the dam break analysis of the Wadi Majlas Flood Protection Dam, a {F.HEIGHT_THALWEG:.0f} m high roller-compacted "
        f"concrete gravity dam about {F.DAM_TO_QURAYAT_KM} km upstream of Qurayat. A two-dimensional hydraulic model of the reservoir, the gorge "
        "and the coastal plain down to the sea was built for the study. Three scenarios were analysed: a sunny-day failure (S1D), a failure at "
        "the peak of the probable maximum flood (S2D) and the probable maximum flood without failure (S3D), the last being the reference against "
        "which the failure is measured. The sunny-day failure was also run without the downstream training dikes (S1N), and eight sensitivity "
        "runs bound the breach parameters and the flood: twelve result runs in all.")
    if s1d:
        d.P(f"**Sunny-day failure (S1D).** With the reservoir at the full supply level and no flood, the sudden failure of five monoliths "
            f"(85 m of the dam) releases {n0(s1d.get('volume_through_dam_Mm3'))} Mm³ in about two hours. The peak outflow is "
            f"{n0(s1d.get('peak_total_flow_m3s'))} m³/s, reached {hm((s1d.get('peak_time_h') or 2) - 2.0)} after the failure begins. Water deeper than "
            f"0.3 m covers {n1(s1d.get('inundated_area_km2_gt0.3m'))} km² of the coastal plain. The wave reaches the plain within "
            f"{hm(s1d.get('arrival_h_median'))}, the residential centre of Qurayat within {wt(place('S1D', TOWN))} and the shoreline within "
            f"{wt(place('S1D', SHORE))}. About {n0(s1d.get('consequences_par_total'))} people live in the flooded area, "
            f"{n0(s1d.get('consequences_par_H4plus'))} of them where the flood is unsafe for people and vehicles or worse; "
            f"{n0(reached('S1D', 0.25))} of them are reached within 15 minutes of the breach and {n0(reached('S1D', 0.5))} within 30 minutes.")
    if s2d and s3d:
        d.P(f"**Flood-day failure (S2D).** The dam is assumed to fail when the reservoir reaches its maximum level during the PMF, "
            f"{n2(s2d.get('trigger_max_stage_hw'))} m a.s.l. at {hm(s2d.get('trigger_time_h'))} into the storm, a level and a moment taken from the "
            f"no-failure run S3D. The peak outflow rises from {n0(s3d.get('peak_total_flow_m3s'))} m³/s without failure to "
            f"{n0(s2d.get('peak_total_flow_m3s'))} m³/s with failure. The flooded area grows only from {n1(s3d.get('inundated_area_km2_gt0.3m'))} to "
            f"{n1(s2d.get('inundated_area_km2_gt0.3m'))} km², because the flood has already covered the plain; what the failure adds is depth, force "
            f"and speed. The area in the worst hazard class grows from {n1(s3d.get('hazard_area_km2', {}).get('H6'))} to "
            f"{n1(s2d.get('hazard_area_km2', {}).get('H6'))} km², the people in the flooded area from {n0(s3d.get('consequences_par_total'))} to "
            f"{n0(s2d.get('consequences_par_total'))}, and the failure wave adds 0.3 m or more to the water already standing on "
            f"{n0(reached('S2D', 0.25))} people within 15 minutes of the breach.")
    if s3d:
        d.P(f"**PMF without failure (S3D).** The reservoir peaks at {n2(peak_pool(s3d))} m a.s.l., {F.PARAPET - (peak_pool(s3d) or 0):.2f} m below "
            f"the parapet, and the spillway passes {n0(s3d.get('peak_total_flow_m3s'))} m³/s against its design discharge of {F.SPILL_QMAX:,.0f} m³/s. "
            f"The dam is not overtopped. The flood alone covers {n1(s3d.get('inundated_area_km2_gt0.3m'))} km² of the plain with "
            f"{n0(s3d.get('consequences_par_total'))} people in it, but it builds up over hours: the residential centre is reached "
            f"{wt(place('S3D', TOWN))} after the storm starts and the shoreline {wt(place('S3D', SHORE))} after.")
    if s1d and s1n:
        d.P(f"**Effect of the training dikes.** The dikes were designed for the 200-year wadi flood, not for a dam break. In the sunny-day failure the "
            f"flooded area is {n1(s1d.get('inundated_area_km2_gt0.3m'))} km² with the dikes and {n1(s1n.get('inundated_area_km2_gt0.3m'))} km² without, "
            f"and the population at risk {n0(s1d.get('consequences_par_total'))} and {n0(s1n.get('consequences_par_total'))} respectively: a difference "
            "well under one per cent. The dikes were therefore kept in every other run and the no-dikes condition was not pursued further.")
    if w1 and w3:
        d.P("**Warning time is what separates the scenarios.** In extent and hazard class the flood without failure looks almost as bad as the "
            f"failure; in time it does not. The sunny-day wave reaches {n0(reached('S1D', 0.25))} people within 15 minutes of the breach and "
            f"{n0(reached('S1D', 1.0))} within an hour, whereas the flood without failure needs {wt(place('S3D', TOWN))} to reach the town and about "
            "twelve hours to reach everyone it will reach. Warning for a dam failure must therefore come from the dam itself, before the failure, "
            "not from the flood.")
    if have("S1D-W51") and have("S1D-W153"):
        d.P(f"**Sensitivity.** The breach width sets the peak almost in proportion ({n0(load('S1D-W51').get('peak_total_flow_m3s'))} to "
            f"{n0(load('S1D-W153').get('peak_total_flow_m3s'))} m³/s for three to nine monoliths) but hardly moves the flooded area or the people in "
            "it; the formation time and the weir coefficient change the peak by about a tenth; the 10,000-year flood gives the same picture as the "
            "PMF with a tenth less flow. The base-case results are therefore robust, and the bounds are quoted with them.")
    d.P("The results are meant for the emergency action plan and for the design review: the arrival times and hazard maps show where warning "
        "and evacuation are needed first, and the no-failure runs confirm the spillway capacity against the PMF. {{f:glance}} puts the three "
        "scenarios side by side.")
    if os.path.exists(chart("results_at_a_glance.png")):
        d.FIG(chart("results_at_a_glance.png"), "The three scenarios at a glance: peak flow at the dam, flooded area and people in it.", "glance", width_cm=16)

    # ============================================================ 1 introduction
    d.H1("Introduction")
    d.H2("Purpose and scope")
    d.P("A dam break analysis answers three questions: how fast and how far would the water go if the dam failed, who and what would be in its way, "
        "and how much worse is a failure than the flood the dam is already passing. This report answers them for the Wadi Majlas dam with a "
        "two-dimensional hydraulic model, and gives the numbers that the emergency action plan[[fn: Emergency action plan (EAP): the document that "
        "tells the operator and the authorities what to do, and whom to warn, when the dam is in danger. The arrival times and hazard maps in this "
        "report are its main technical input.]] needs.")
    d.P("Chapter 2 sets out the method: how a concrete gravity dam fails, how the breach was sized, how the flood is routed and how the consequences "
        "are measured. Chapter 3 defines the scenarios and the runs, chapter 4 describes the model as built with every input, chapters 5 to 7 give the "
        "results of the sunny-day failure, the flood-day failure and the flood without failure, chapter 8 the sensitivity of the results to the "
        "breach parameters, chapter 9 the consequences for people and property, including who is reached and when. Chapters 10 and 11 discuss the "
        "findings and draw the conclusions.")
    d.H2("The dam and the valley in brief")
    d.P(f"The dam is a roller-compacted concrete (RCC) gravity dam with a grout-enriched RCC facing, {F.HEIGHT_THALWEG:.0f} m above the wadi bed, {F.CREST_LENGTH:.0f} m long at the crest "
        f"({F.CREST} m a.s.l.), with a {F.PARAPET - F.CREST:.1f} m parapet to {F.PARAPET} m a.s.l. The ungated ogee spillway, {F.SPILL_NET_LENGTH:.0f} m net "
        f"length at {F.SPILL_CREST} m a.s.l., is designed for {F.SPILL_QMAX:,.0f} m³/s. The reservoir holds {F.VOL_FSL_MM3} Mm³ at the full supply level. "
        f"Downstream, the wadi leaves a gorge and crosses the coastal plain of Qurayat, where two training dikes, {F.DIKE_LENGTH_M / 1000:.1f} km long on each "
        f"bank, guide the {F.DIKE_DESIGN_RP}-year flood to the sea. Chapter 4 gives the dam as designed and the model built on it.")

    # ============================================================ 2 methodology
    d.H1("Methodology")
    d.H2("The analysis in outline")
    d.P("The analysis runs from the data to the inputs of the emergency plan in the steps of {{f:fc_process}}: the dam type fixes the failure mode "
        "and the breach; the scenarios fix the water in the reservoir and in the wadi at the moment of failure; the two-dimensional model routes the "
        "flood over the terrain; the results are turned into depth, velocity, hazard class and arrival time on a 2 m grid; and the people and "
        "properties in the flooded area are counted, by hazard class and by the time at which the water reaches them. Each step is described below.")
    if os.path.exists(os.path.join(FC, "fc1_process.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc1_process.png"), "The dam break analysis process, from data to emergency-plan inputs.", "fc_process", width_cm=22.9, max_h_cm=15.0))

    d.H2("Failure mode of a concrete gravity dam and the breach parameters")
    d.P("A roller-compacted concrete gravity dam does not erode. It fails, if at all, by the sudden sliding or overturning of one or more monoliths, "
        "the blocks between vertical contraction joints, when the water load exceeds what the foundation contact can hold. The breach is therefore "
        "rectangular, vertical-sided and essentially instantaneous, and its width is a whole number of monoliths. This is the failure mode assumed "
        "here, and it decides how the breach is sized.")
    Vw = F.VOL_FSL_MM3 * 1e6; hb = F.FSL - F.BED_AT_DAM; g = 9.81
    B_p = 0.27 * 1.0 * Vw ** 0.32 * hb ** 0.04; B_o = 0.27 * 1.3 * Vw ** 0.32 * hb ** 0.04; tf = 63.2 * math.sqrt(Vw / (g * hb ** 2)) / 3600
    Ver = 0.0261 * (Vw * hb) ** 0.769; tf2 = 0.0179 * Ver ** 0.364
    Bv = 2.5 * hb + 54.9; tv1 = 0.015 * hb; tv2 = 0.020 * hb + 0.25
    d.P("HEC-RAS offers five methods to compute breach parameters: MacDonald and Langridge-Monopolis (1984), Froehlich (1995), Froehlich (2008), "
        "Von Thun and Gillette (1990) and Xu and Zhang (2009). All five are regression equations fitted to the recorded failures of earth and "
        "rockfill embankments, 42 to 182 cases each, in which water erodes a trapezoidal channel through the fill over half an hour to several "
        "hours. Their inputs are the volume and depth of water above the breach floor and, for Xu and Zhang, the erodibility of the fill and the "
        "type of embankment; the 'concrete-faced' type in that method is a concrete-faced rockfill dam, not a concrete gravity dam. None of the "
        "five was fitted to a concrete dam, and none can represent a block that slides out in minutes. {{t:regr}} shows what they would give for the "
        f"Majlas sunny-day pool ({F.VOL_FSL_MM3} Mm³, {hb:.1f} m of water above the breach floor): widths of the right order, because they scale "
        "with the reservoir, but formation times of one to three hours, ten to thirty times too long for a concrete dam. A breach that opens "
        "slowly gives a lower peak, so using them here would understate the wave. They were therefore not used.")
    d.TBL(["Method (HEC-RAS parameter calculator)", "Fitted to", "Width for Majlas (m)", "Formation time (h)", "Applies to a concrete gravity dam?"], [
        ["Froehlich (2008)", "74 embankment failures", f"{B_p:,.0f} to {B_o:,.0f}", f"{tf:.1f}", "No: erosion of fill"],
        ["Froehlich (1995)", "63 embankment failures", "of the same order", "of the same order", "No: erosion of fill"],
        ["MacDonald and Langridge-Monopolis (1984)", "42 embankment failures", "from the eroded volume", f"{tf2:.1f}", "No: erosion of fill"],
        ["Von Thun and Gillette (1990)", "57 embankment failures", f"{Bv:,.0f}", f"{tv1:.1f} to {tv2:.1f}", "No: erosion of fill"],
        ["Xu and Zhang (2009)", "182 earth and rockfill failures", "needs the erodibility of the fill", "needs the erodibility of the fill", "No: 'concrete-faced' means a concrete-faced rockfill dam"],
        ["Guidance for concrete gravity dams (below)", "Concrete dam case histories", f"whole monoliths, up to {0.5 * F.CREST_LENGTH:.0f} (half the crest)", f"{F.BREACH_TIME_RANGE[0]} to {F.BREACH_TIME_RANGE[1]}", "Yes"],
    ], "The regression methods offered by the model, evaluated for the Majlas sunny-day pool, against the guidance adopted.", "regr", col_w=[1.9, 1.3, 1.1, 1.0, 1.4], font_sz=FS)
    d.P("For concrete gravity dams the United States federal guidance gives the breach as a number of whole monoliths with vertical sides, usually "
        "not more than half the crest length, formed in 0.1 to 0.5 hour (USACE), 0.1 to 0.3 hour (FERC) or 0.1 to 0.2 hour (NWS). "
        "{{t:guide}} sets the three side by side.")
    d.TBL(["Source", "Breach width", "Side slopes", "Formation time (h)"], [
        ["USACE (1980, 2007), as tabulated in the HEC-RAS reference and in TD-39", "Usually not more than 0.5 of the crest length, whole monoliths", "Vertical", "0.1 to 0.5"],
        ["FERC Engineering Guidelines", "Usually not more than 0.5 of the crest length, whole monoliths", "Vertical", "0.1 to 0.3"],
        ["NWS (National Weather Service)", "Usually not more than 0.5 of the crest length, whole monoliths", "Vertical", "0.1 to 0.2"],
    ], "Breach parameters for concrete gravity dams in the United States federal guidance.", "guide", col_w=[2.4, 2.4, 0.8, 1.0], font_sz=FS)
    d.P(f"The base case takes five monoliths, {5 * 17:.0f} m, the width of two spillway bays. The spillway blocks are the tallest of the dam and "
        "carry the largest load; a failure that takes out two bays removes the ogee and the piers between them, opens the full height of the dam "
        f"down to the wadi bed and stays within the federal ceiling of half the crest ({0.5 * F.CREST_LENGTH:.0f} m). The formation time is the short end of the "
        "guidance, 0.1 hour: a monolith that slides leaves the dam in minutes, and a shorter time gives the higher, more conservative peak. The "
        "weir coefficient of the opening is the upper value of the range HEC-RAS gives for a clean, sharp-edged breach in a gravity dam "
        f"({F.BREACH_WEIR_C_RANGE_SI[0]} to {F.BREACH_WEIR_C_RANGE_SI[1]} in SI units). Each of the three is then varied in the sensitivity runs to the "
        "bounds in {{t:bparams}}: one bay and half the crest for the width, twice and half the formation time, and the lower coefficient.")
    d.TBL(["Parameter", "Base case", "Sensitivity bounds", "Basis"], [
        ["Failure mode", "Sliding of whole monoliths, vertical sides", "-", "Concrete gravity dam"],
        ["Breach width", f"{5 * 17:.0f} m, five monoliths (two spillway bays)", f"{3 * 17:.0f} m (three monoliths, one bay) and {9 * 17:.0f} m (nine monoliths, about half the crest); {7 * 17:.0f} m on the flood day", "Federal guidance: whole monoliths, at most half the crest"],
        ["Breach bottom", f"{F.BREACH_BOTTOM} m a.s.l.", "-", "Wadi bed at the axis: the block leaves down to its foundation contact"],
        ["Formation time", f"{F.BREACH_TIME_BASE} h (6 minutes)", f"{F.BREACH_TIME_RANGE[0]} h (3 minutes) and {F.BREACH_TIME_RANGE[1]} h (18 minutes)", "Short end of USACE 0.1 to 0.5 h, FERC 0.1 to 0.3 h, NWS 0.1 to 0.2 h"],
        ["Weir coefficient of the opening", f"{F.BREACH_WEIR_C_RANGE_SI[1]} (SI)", f"{F.BREACH_WEIR_C_RANGE_SI[0]}", "HEC-RAS range for a gravity-dam breach, 2.6 to 3.0 in US units"],
        ["Opening", "Sine-wave progression to the full width", "-", "A fast, smooth opening; the model option for a concrete dam"],
    ], "Breach parameters of the base case and the bounds tested.", "bparams", col_w=[1.3, 1.8, 2.2, 1.9], font_sz=FS)
    Bb = 5 * 17.0; Qw = F.BREACH_WEIR_C_RANGE_SI[1] * Bb * hb ** 1.5; Qr = 8 / 27 * Bb * math.sqrt(g) * hb ** 1.5
    d.P("Two hand calculations bound the peak outflow before any model result is trusted. The weir equation applied to the fully open breach at "
        "the starting pool gives the upper value:")
    d.EQ(msub(mr("Q"), mr("p")) + mr("=") + mr("C") + mr("B") + msup(mdelim(mr("H") + mr("-") + msub(mr("Z"), mr("b"))), mr("1.5")), "weir",
         [("Q_{p}", "peak outflow through the breach (m³/s)"), ("C", f"weir coefficient of the opening, {F.BREACH_WEIR_C_RANGE_SI[1]} m^{{0.5}}/s in the base case"),
          ("B", f"breach width, {Bb:.0f} m in the base case"), ("H", "pool level at failure (m a.s.l.)"), ("Z_{b}", f"breach bottom, {F.BED_AT_DAM} m a.s.l.")])
    d.P("The Ritter solution for the sudden removal of a wall onto a dry bed gives the lower value, because it accounts for the drop of the water "
        "surface at the opening:")
    d.EQ(msub(mr("Q"), mr("p")) + mr("=") + mfrac(mr("8"), mr("27")) + mr("B") + mrad(mr("g")) + msup(mdelim(mr("H") + mr("-") + msub(mr("Z"), mr("b"))), mr("1.5")), "ritter",
         [("g", "gravity, 9.81 m/s²")])
    d.P(f"For the base breach and the full supply level the weir equation gives about {round(Qw, -3):,.0f} m³/s and the Ritter solution about "
        f"{round(Qr, -3):,.0f} m³/s. The modelled sunny-day peak of {n0(s1d.get('peak_total_flow_m3s')) if s1d else '-'} m³/s lies between them, "
        "lower than the weir value because the pool drops during the six minutes of formation and the tailwater rises in the stilling basin.")

    d.H2("Scenarios and the reference case")
    d.P("Three scenarios frame the question. Each starts with the reservoir at the full supply level:")
    d.BULS([
        "**Sunny-day failure (S1).** No flood in the wadi, the reservoir at the full supply level, the dam fails without warning. This gives the "
        "sharpest wave and the least warning, because nobody expects a flood; it is the case the emergency plan is written for.",
        "**Flood-day failure (S2).** The probable maximum flood is passing and the dam fails at the moment the reservoir reaches its highest level, "
        "when the load on the dam is greatest. That level and moment are read from the no-failure run of the same flood.",
        "**Baseline, the PMF without failure (S3).** The same flood with the dam holding. It is the reference: only what the failure adds to it "
        "counts against the dam, and it also confirms the spillway capacity.",
    ])
    d.P("The three are summarised with their default conditions in {{f:fc_matrix}}, and their names and settings are listed in chapter 3.")
    if os.path.exists(os.path.join(FC, "fc5_scenarios.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc5_scenarios.png"), "The three scenarios and their default conditions.", "fc_matrix", width_cm=22.9, max_h_cm=15.0))
    d.P("For every consequence measure, the dam's contribution is the difference between the failure run and its no-failure twin:")
    d.EQ(mr("ΔC") + mr("=") + msub(mr("C"), mr("failure")) + mr("-") + msub(mr("C"), mtxt("no failure")), "incr",
         [("ΔC", "the dam's contribution to any consequence measure C: depth, area, people, hazard class"),
          ("C_{failure}, C_{no failure}", "the measure in the failure run and in its no-failure twin")])

    d.H2("Hydraulic model")
    d.P("The flood is routed in two dimensions over one mesh from the reservoir to the sea, with the dam as a weir connection whose profile carries "
        "the spillway and the non-overflow crest and into which the breach is cut. The inflows to the reservoir and from the two side catchments, "
        "and the rain on the plain, come from the hydrology study. {{f:fc_hecras}} shows the order in which the model was assembled, from the "
        "terrain to the checks made before a result was used; chapter 4 gives every input as built.")
    if os.path.exists(os.path.join(FC, "fc3_hecras.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc3_hecras.png"), "How the hydraulic model was assembled.", "fc_hecras", width_cm=22.9, max_h_cm=15.0))
    d.P("Two relations govern the model at the dam and in the solver: the spillway follows the ogee equation, and the time step is kept below the "
        "Courant limit:")
    d.EQ(mr("Q") + mr("=") + msub(mr("C"), mr("s")) + mr("L") + msup(mr("H"), mr("1.5")), "ogee",
         [("Q", "spillway discharge (m³/s)"), ("C_{s}", f"discharge coefficient of the ogee, {F.MODEL['connection']['coef']}"),
          ("L", f"net crest length, {F.SPILL_NET_LENGTH:.0f} m"), ("H", f"head above the crest at {F.SPILL_CREST} m (m)")])
    d.EQ(mr("Cr") + mr("=") + mfrac(mr("V") + mr("Δt"), mr("Δx")), "courant",
         [("Cr", "Courant number, kept between 0.4 and 0.9 by halving and doubling the step"), ("V", "flow velocity plus wave celerity (m/s)"),
          ("Δt", "time step (s)"), ("Δx", "cell size in the direction of flow (m)")])

    d.H2("Consequences")
    d.P("For each run the model gives, on a 2 m grid, the maximum depth and velocity, their product, the time at which the water first arrives and "
        "the duration of flooding. Depth and velocity are combined into the six Australian (AIDR) flood hazard classes, from H1, safe for people "
        "and vehicles, to H6, where buildings fail; a cell takes the highest class that any of the three limits gives:")
    d.EQ(mr("D") + mr("×") + mr("V") + mr("=") + mtxt("depth") + mr("×") + mtxt("velocity"), "dv",
         [("D", "maximum depth (m)"), ("V", "maximum velocity (m/s)"), ("D × V", "their product (m²/s), the measure of the force on a person or a wall")])
    d.TBL(["Class", "D × V limit (m²/s)", "Depth limit (m)", "Velocity limit (m/s)", "Meaning"], [
        ["H1", f"{F.HAZ['H1'][0]}", f"{F.HAZ['H1'][1]}", f"{F.HAZ['H1'][2]}", "Generally safe for people, vehicles and buildings"],
        ["H2", f"{F.HAZ['H2'][0]}", f"{F.HAZ['H2'][1]}", f"{F.HAZ['H2'][2]}", "Unsafe for small vehicles"],
        ["H3", f"{F.HAZ['H3'][0]}", f"{F.HAZ['H3'][1]}", f"{F.HAZ['H3'][2]}", "Unsafe for vehicles, children and the elderly"],
        ["H4", f"{F.HAZ['H4'][0]}", f"{F.HAZ['H4'][1]}", f"{F.HAZ['H4'][2]}", "Unsafe for people and vehicles"],
        ["H5", f"{F.HAZ['H5'][0]}", f"{F.HAZ['H5'][1]}", f"{F.HAZ['H5'][2]}", "Unsafe for people and vehicles; buildings vulnerable to structural damage"],
        ["H6", "above H5", "", "", "Unsafe for everything; buildings fail"],
    ], "AIDR flood hazard classes: a cell is in the class whose limits it exceeds.", "haz", col_w=[0.6, 1.1, 0.9, 1.0, 3.0], font_sz=FS)
    d.P("{{f:aidr}} draws the same limits as curves in the depth-velocity plane; the classes are the same as those used in the flood-risk study of "
        "the downstream works, so the two studies can be read together.")
    if os.path.exists(chart("aidr_vulnerability_curves.png")):
        d.FIG(chart("aidr_vulnerability_curves.png"), "General flood hazard vulnerability curves (Australian AIDR Guideline 7-3).", "aidr", width_cm=12.5)
    d.P("People are counted on a 100 m population grid[[fn: GHS-POP 2025, the global population grid of the European Commission's Joint Research "
        "Centre, at 100 m; the count is the sum of the cells whose centre lies in water deeper than 0.3 m.]] and properties on the plot layer of the "
        "flood-risk study, within the flooded area and per hazard class:")
    d.EQ(mr("PAR") + mr("=") + mr("Σ") + msub(mr("P"), mr("i")) + mtxt("  for every cell i with ") + msub(mr("D"), mr("i")) + mr(">") + mr("0.3") + mtxt(" m"), "par",
         [("PAR", "population at risk"), ("P_{i}", "people in population cell i (100 m)"), ("D_{i}", "maximum depth at the centre of cell i (m)")])
    d.P("Arrival is timed from each scenario's own trigger: a failure from the moment the breach opens, the flood without failure from the start of "
        "the storm. A place counts as reached when the water there rises 0.3 m above what was there before the trigger; for the flood-day failure, "
        "whose plain is already under the flood when the dam goes, it is the moment the failure makes the water 0.3 m deeper than the flood alone "
        "would at the same instant. People and plots are then counted by the time at which they are reached.")

    d.H2("Sensitivity and checks")
    d.P("The breach width, the formation time, the weir coefficient of the opening and the flood itself are varied one at a time from the base case, "
        "so that each result carries a bound. Whether the training dikes needed their own set of runs was decided by the sunny-day pair, which "
        "isolates the dam's contribution:")
    d.EQ(mfrac(mdelim(msub(mr("X"), mr("N")) + mr("-") + msub(mr("X"), mr("D")), "|", "|"), msub(mr("X"), mr("D"))) + mr("<") + mr("5") + mr("%"), "dikes",
         [("X", "flooded area, people in the flooded area and median arrival time"), ("N, D", "without and with the training dikes")])
    d.P("Every run was checked for a clean solver finish and mass conservation before its products were used. {{f:fc_campaign}} shows the runs "
        "in the order they were made: the preparation of the model, the base runs with the dikes decision between them, and the sensitivity runs "
        "and products that followed.")
    if os.path.exists(os.path.join(FC, "fc6_campaign.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc6_campaign.png"), "The runs as executed, with the dikes decision.", "fc_campaign", width_cm=22.9, max_h_cm=15.0))

    d.H2("Standards and guidance followed")
    d.P("The analysis follows the international practice for concrete dams; {{t:std}} lists the documents and what each one was used for. "
        "The full references are at the end of the report.")
    d.TBL(["Document", "Used for"], [
        ["USACE, HEC-RAS 6.6 User's, 2D Modeling and Hydraulic Reference Manuals (2024)", "Model set-up, the weir connection and breach options, the breach weir coefficients, the solver"],
        ["USACE, Using HEC-RAS for Dam Break Studies, TD-39 (Brunner, 2014)", "Breach parameters by dam type, run set-up and checks for dam-break models"],
        ["FERC, Engineering Guidelines, Chapter II (2015)", "Breach width, side slopes and formation time for concrete gravity dams; inflow design flood"],
        ["ICOLD Bulletin 111 (2020)", "Scenarios, incremental reading of the consequences, presentation of the results"],
        ["AIDR Guideline 7-3, Flood Hazard (2017)", "The hazard classes H1 to H6 from depth and velocity"],
    ], "Standards and guidance and what each was used for.", "std", col_w=[3.0, 3.6], font_sz=FS)

    # ============================================================ 3 scenarios and runs
    d.H1("Scenarios and Runs")
    d.P("The scenarios of chapter 2 were run as listed in {{t:scen}}. The training dikes are in place in every run; the sunny-day failure was "
        "also run without them, to test whether they matter.")
    d.TBL(["Name", "Scenario", "Reservoir at the start", "Inflow", "Failure"], [
        ["S1D", "Sunny-day failure, dikes in place", f"Full supply level, {F.FSL} m", "None", "Five monoliths at a set time, two hours into the run"],
        ["S1N", "Sunny-day failure, no dikes", f"Full supply level, {F.FSL} m", "None", "As S1D"],
        ["S2D", "Flood-day failure", f"Full supply level, {F.FSL} m", "PMF, with rain on the plain", "Five monoliths at the moment the reservoir reaches its maximum level, read from S3D"],
        ["S3D", "PMF without failure", f"Full supply level, {F.FSL} m", "PMF, with rain on the plain", "None"],
    ], "The scenarios.", "scen", col_w=[0.7, 1.5, 1.4, 1.3, 2.6], font_sz=FS)
    d.P("A sunny-day failure[[fn: Sunny-day failure: a failure with no flood in the river, for example from a foundation problem or an earthquake. "
        "It gives the least warning, because nobody expects a flood.]] gives the largest breach flow relative to the normal flow and the least warning. "
        "The flood-day failure is assumed to happen at the worst moment of the PMF, when the reservoir is at its highest and the load on the dam is "
        "greatest; this is the usual convention for a concrete gravity dam, whose critical case is the peak water load rather than overtopping. "
        "The PMF without failure is the reference that shows what the failure adds.")
    dec = dikes_decision()
    if dec is not None and s1d and s1n:
        d.H2("The training dikes")
        rd = dec["relative_differences"]; a, b = dec["S1D"], dec["S1N"]
        d.P("The training dikes were designed for the 200-year wadi flood. The two sunny-day runs, with and without them, isolate the dam's "
            "contribution with nothing else in the valley; {{t:dikes_cmp}} compares them.")
        d.TBL(["Quantity", "S1D, with dikes", "S1N, without dikes", "Difference"], [
            ["Peak flow at the dam (m³/s)", n0(a["peak_total_flow_m3s"]), n0(b["peak_total_flow_m3s"]), f"{rd['peak_total_flow_m3s']:.1%}"],
            ["Flooded area > 0.3 m (km²)", n1(a["inundated_area_km2_gt0.3m"]), n1(b["inundated_area_km2_gt0.3m"]), f"{rd['inundated_area_km2_gt0.3m']:.1%}"],
            ["People in the flooded area", n0(a["par_total"]), n0(b["par_total"]), f"{rd['par_total']:.1%}"],
            ["Median arrival time on the plain", hm(a["arrival_h_median"]), hm(b["arrival_h_median"]), f"{rd['arrival_h_median']:.1%}"],
        ], "Effect of the training dikes on the sunny-day failure.", "dikes_cmp", col_w=[2.4, 1.3, 1.3, 1.0], font_sz=FS)
        d.P("A wave of this size overtops the dikes within minutes and spreads over the whole plain; the dikes neither contain it nor steer it to a "
            "measurable degree. The with-dikes runs therefore stand for both conditions, and every other scenario was run with the dikes in place.")
    d.H2("Sensitivity runs")
    d.P("The sensitivity runs change one parameter at a time from the base case: the breach width (three, five, seven and nine monoliths), the "
        "formation time (3, 6 and 18 minutes), the weir coefficient of the breach opening, and the flood (the 10,000-year flood instead of the PMF). "
        "The breach mechanics are tested on the sunny-day scenario, where the dam's contribution stands alone; the flood day carries one width "
        "check and the smaller flood.")
    d.TBL(["Name", "What is changed from the base case", "Purpose"], [
        ["S1D-W51, S1D-W153", "Breach width 51 and 153 m (three and nine monoliths) instead of 85 m (five monoliths), sunny day", "How much the peak and the flooded area depend on how many monoliths go"],
        ["S1D-T3m, S1D-T18m", "Formation time 3 min and 18 min instead of 6 min, sunny day", "Whether the speed of the failure matters"],
        ["S1D-C1.44", "Breach weir coefficient 1.44 instead of 1.66, sunny day", "Lower bound of the flow through the opening"],
        ["S2D-W119", "Breach width 119 m (seven monoliths), flood day", "The width question checked on the flood day"],
        ["S3D-F10000, S2D-F10000", "10,000-year flood instead of the PMF, without and with failure", "How the flood-day results change with a smaller flood"],
    ], "The sensitivity runs.", "sens", col_w=[1.8, 2.6, 2.6], font_sz=FS)

    # ============================================================ 4 the model as built
    d.H1("The Model as Built")
    M = F.MODEL
    d.H2("Extent, terrain, mesh and roughness")
    d.P(f"The model is one two-dimensional area of {M['area_km2']} km² from the upper reservoir to the shoreline, shown in {{f:reach}} with its "
        "boundary lines: the inflow to the reservoir, the two side catchments that join below the dam, and the two outflow lines at the coast. "
        "The terrain is the 5 m digital terrain model of the survey with the design surfaces of the dam and the dikes added; the dam body itself "
        "was cut out of it so that the dam connection alone controls the flow. Two terrains and two meshes were built, with and without the "
        "training dikes. {{t:mesh}} lists the mesh, the roughness and the solver settings.")
    if os.path.exists(os.path.join(MAPS, "Model extent.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(MAPS, "Model extent.png"), "The model: 2D flow area, boundary condition lines, dam connection and training dikes.", "reach", width_cm=22.9, max_h_cm=15.0))
    d.TBL(["Item", "As built"], [
        ["Cells", f"{M['cells_dikes']:,} with dikes, {M['cells_nodikes']:,} without"],
        ["Cell size", f"median {M['cell_size_m']['median']} m, 10 % of cells below {M['cell_size_m']['p10']} m, largest {M['cell_size_m']['max']} m; "
                      f"{M['connection_cells_m'][0]} m along the dam connection, {M['connection_cells_m'][1]} m beyond"],
        ["Breaklines", f"{M['breaklines']} lines at {M['breakline_spacing_m'][0]} to {M['breakline_spacing_m'][1]} m: dike crests, wadi banks, road embankments, dam axis"],
        ["Roughness", "; ".join(f"n = {k}: {v} % of the area" for k, v in M['manning'].items())],
        ["Solver", f"Full-momentum shallow-water equations[[fn: The Eulerian-Lagrangian scheme of the shallow-water equations (SWE-ELM), the full-momentum "
                   "solver of HEC-RAS 6.6, which keeps the inertia of the wave that a diffusion-wave solver drops.]], adaptive time step on a Courant "
                   f"number[[fn: Courant number: the distance the water moves in one time step divided by the cell size. Keeping it below one keeps the "
                   f"solution stable.]] of {M['solver']['courant'][0]} to {M['solver']['courant'][1]}, results every {M['solver']['output_min']} minute, "
                   f"maps every {M['solver']['mapping_min']} minutes"],
        ["Simulation windows", "14 h for the sunny-day runs (breach at hour 2), 60 h for the flood-day base runs, 36 h for the flood-day sensitivity runs"],
    ], "The 2D model as built.", "mesh", col_w=[1.2, 5.0], font_sz=FS)
    d.H2("The dam as designed")
    d.P(f"The model represents the dam as finalised in the design review of {REVIEW_DATE}. It is a roller-compacted concrete (RCC) gravity dam with a grout-enriched RCC facing on a straight axis, "
        f"{F.CREST_LENGTH:.0f} m long at the crest and {F.HEIGHT_THALWEG} m high above the wadi bed ({F.HEIGHT_FOUNDATION} m above the foundation at "
        f"{F.FOUNDATION_LEVEL:.1f} m a.s.l.). The crest is {F.CREST_WIDTH:.1f} m wide at {F.CREST} m a.s.l. with a parapet to {F.PARAPET} m; the upstream face is "
        f"{F.US_SLOPE} and the downstream face {F.DS_SLOPE}. {{{{f:dam_elev}}}} shows the upstream elevation: {F.N_BLOCKS} monoliths separated by "
        f"{F.N_BLOCKS - 1} contraction joints, B1 of 31.21 m against the left bank, B2 to B16 of 17.00 m each and B17 of 25.79 m against the right bank. "
        "The central blocks under the spillway stand on the foundation at −15.0 m; the abutment blocks step up the banks.")
    d.P(f"The spillway sits on the central blocks: a free ogee with its crest at {F.SPILL_CREST} m a.s.l., the full supply level, in {F.SPILL_BAYS} bays of "
        f"{F.SPILL_BAY_WIDTH:.0f} m between {F.SPILL_PIERS} piers of {F.SPILL_PIER_THK:.0f} m ({F.SPILL_NET_LENGTH:.0f} m net, {F.SPILL_GROSS_LENGTH:.0f} m gross, "
        f"218 m between the training walls), a stepped chute at {F.DS_SLOPE} and a {F.BASIN_TYPE} stilling basin {F.BASIN_LENGTH:.0f} m long with its floor at "
        f"{F.BASIN_FLOOR} m a.s.l. Its design capacity is {F.SPILL_QMAX:,.0f} m³/s. The bottom outlet, one {F.BO_DIAMETER} m pipe in the left diversion culvert "
        f"rated {F.BO_QMAX:.0f} m³/s, is closed in every run. {{{{f:dam_sec}}}} and {{{{f:spill_sec}}}} show the non-overflow and spillway sections with their levels; "
        "{{t:dam}} lists the values and where each one enters the model.")
    d.TBL(["Item", "As designed", "In the model"], [
        ["Dam type", F.DAM_TYPE, "Failure by sliding of whole monoliths, vertical breach sides (chapter 2)"],
        ["Crest / parapet top", f"{F.CREST} / {F.PARAPET} m a.s.l.", f"Non-overflow crest of the connection at {F.PARAPET} m: the parapet is credited, so the PMF pool of {n2(peak_pool(s3d)) if s3d else '-'} m does not overtop the dam"],
        ["Crest width / length", f"{F.CREST_WIDTH:.1f} m / {F.CREST_LENGTH:.0f} m", f"Weir width {M['connection']['width_m']:.0f} m; connection line along the axis"],
        ["Height above wadi bed / foundation", f"{F.HEIGHT_THALWEG} m / {F.HEIGHT_FOUNDATION} m", f"Wadi bed at the axis {F.BED_AT_DAM} m a.s.l. = breach bottom"],
        ["Foundation level", f"{F.FOUNDATION_LEVEL:.1f} m a.s.l.", "Below the breach bottom; not modelled"],
        ["Faces, upstream / downstream", f"{F.US_SLOPE} / {F.DS_SLOPE}", "Vertical breach sides; the chute slope is in the terrain downstream"],
        ["Monoliths", f"{F.N_BLOCKS} blocks: 31.21 m, 15 × 17.00 m, 25.79 m; {F.N_BLOCKS - 1} joints", "Breach width in whole 17 m blocks: 51, 85 (base), 119 and 153 m = 3, 5, 7 and 9 blocks"],
        ["Spillway", f"Free ogee at {F.SPILL_CREST} m, {F.SPILL_BAYS} × {F.SPILL_BAY_WIDTH:.0f} m bays, {F.SPILL_PIERS} × {F.SPILL_PIER_THK:.0f} m piers, net {F.SPILL_NET_LENGTH:.0f} m, {F.SPILL_QMAX:,.0f} m³/s",
         f"Weir profile at {F.SPILL_CREST} m over {F.SPILL_NET_LENGTH:.0f} m of the connection; ogee coefficient {M['connection']['coef']}"],
        ["Stilling basin", f"{F.BASIN_TYPE}, {F.BASIN_LENGTH:.0f} m, floor {F.BASIN_FLOOR} m a.s.l.", "In the terrain"],
        ["Bottom outlet", f"One {F.BO_DIAMETER} m pipe, intakes {F.BO_INTAKES[0]:.0f} and {F.BO_INTAKES[1]:.0f} m, {F.BO_QMAX:.0f} m³/s", "Closed"],
        ["Reservoir", f"{F.VOL_FSL_MM3} Mm³ at {F.FSL} m; {F.VOL_MWL_MM3} Mm³ at {F.MWL_TABLE} m", f"Storage from the terrain: {M['fill']['volume_Mm3']} Mm³ at {M['fill']['pool_m']} m after the fill"],
    ], f"The dam as designed and where each value enters the model (design review, {REVIEW_DATE}).", "dam", col_w=[1.4, 2.6, 3.0], font_sz=FS)
    d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(DECKFIG, "dam_elevation_monoliths_crop.png"), f"Upstream elevation of the dam: the {F.N_BLOCKS} monoliths B1 to B17 with their widths, crest {F.CREST} m, parapet {F.PARAPET} m and the foundation at {F.FOUNDATION_LEVEL:.1f} m (design review, September 2026).", "dam_elev", width_cm=22.9, max_h_cm=15.0))
    d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(DECKFIG, "dam_section_nonoverflow_crop.png"), f"Section through a non-overflow block: crest {F.CREST} m, parapet {F.PARAPET} m, galleries at 74.0 and 42.5 m, faces {F.US_SLOPE} and {F.DS_SLOPE} (design review, September 2026).", "dam_sec", width_cm=22.9, max_h_cm=15.0))
    d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(DECKFIG, "dam_section_spillway_crop.png"), f"Section through a spillway block: ogee crest {F.SPILL_CREST} m, stepped chute, stilling basin floor {F.BASIN_FLOOR} m, foundation {F.FOUNDATION_LEVEL:.1f} m (design review, September 2026).", "spill_sec", width_cm=22.9, max_h_cm=15.0))
    d.H2("The dam and the breach in the model")
    d.P("The dam is a weir connection[[fn: The model element that links two parts of the 2D area through a structure. Its profile carries the "
        "spillway crest and the non-overflow crest; the breach is cut into it.]] whose profile carries the "
        f"non-overflow crest at {F.PARAPET} m and the ogee at {F.SPILL_CREST} m over {F.SPILL_NET_LENGTH:.0f} m of its length; weir coefficient "
        f"{M['connection']['coef']}, width {M['connection']['width_m']:.0f} m, submergence limit {M['connection']['max_submergence']}. "
        "The breach is the base case of chapter 2, {{t:breach}}.")
    d.TBL(["Parameter", "Base value", "Basis"], [
        ["Failure mode", "Sliding of whole monoliths, vertical sides", "Concrete gravity dam (chapter 2)"],
        ["Breach width", "85 m (five monoliths of 17 m)", "Two spillway bays; within the guidance ceiling of half the crest"],
        ["Breach bottom", f"{F.BREACH_BOTTOM} m a.s.l.", "Wadi bed at the axis"],
        ["Formation time", "0.1 h (6 min)", "Short end of the guidance for concrete dams"],
        ["Weir coefficient", "1.66 (SI)", "Upper value of the range for a gravity-dam breach, 1.44 to 1.66"],
        ["Progression", "Sine wave", "A fast, smooth opening"],
        ["Trigger, sunny day", "Set time, 2 h into the run", "Gives the model two hours to settle on the restart"],
        ["Trigger, flood day", "Set time = moment of maximum pool in S3D", "Failure at the highest load"],
    ], "Breach parameters of the base case as entered in the model.", "breach", col_w=[1.4, 2.2, 3.4], font_sz=FS)
    d.H2("Boundary conditions")
    B = M["bc"]
    d.P(f"Three hydrographs feed the model: the inflow to the Majlas dam reservoir, the side wadi J11 and the southern catchment of "
        f"{F.SOUTH_CATCHMENT_KM2} km², both of which join the wadi below the dam. They come from the hydrology study's catchment model, extended with "
        "the southern catchment; {{f:hms}} shows that model and the three elements whose hydrographs are taken. Rain falls directly on the modelled "
        f"area with the same storm, reduced by the areal factor of {B['rain_areal_factor']}. The sunny-day runs have no inflow and no rain. "
        "{{t:floods}} gives the design floods behind the two flood-day inputs, and {{f:inputs}} the hydrographs and the rain as fed to the model.")
    if os.path.exists(os.path.join(MAPS, "HEC-HMS model.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(MAPS, "HEC-HMS model.png"), "The catchment model of the hydrology study and the three elements whose hydrographs feed the 2D model.", "hms", width_cm=22.9, max_h_cm=15.0))
    DF = {r[0]: r for r in F.DESIGN_FLOODS}
    d.TBL(["Flood", "Storm rainfall (mm)", "Peak inflow to the reservoir (m³/s)", "Volume (Mm³)"], [
        ["200-year (design flood of the training dikes)", n1(DF["200-yr"][2]), n0(DF["200-yr"][3]), n1(DF["200-yr"][4])],
        ["10,000-year", n1(DF["10,000-yr"][2]), n0(DF["10,000-yr"][3]), n1(DF["10,000-yr"][4])],
        ["Probable maximum flood (PMF)", n1(DF["PMF"][2]), n0(DF["PMF"][3]), n1(DF["PMF"][4])],
    ], "Design floods of the hydrology study used in this analysis (48-hour storm).", "floods", col_w=[2.6, 1.3, 1.6, 1.1], font_sz=FS)
    if os.path.exists(chart("results_inputs_hydrographs.png")):
        d.FIG(chart("results_inputs_hydrographs.png"), "The inputs to the flood-day runs: rain on the 2D area and the inflow hydrographs at the three boundary lines, PMF and 10,000-year flood.", "inputs", width_cm=15)
    d.P("{{t:bc}} lists the boundary conditions of the flood-day runs; the coast is a free outflow at the sea level of the maritime tables"
        f"[[fn: Mean higher high water at Qurayyat, {F.TIDE['mhhw_cd']} m above chart datum, which lies {F.TIDE['z0_m']} m below mean sea level: "
        f"{F.SEA_LEVEL} m a.s.l. ({F.TIDE['source']}). The shoreline terrain is higher, so the sea does not back water into the model; a storm surge "
        "coinciding with the flood is outside the scope of this study.]].")
    d.TBL(["Boundary", "PMF", "10,000-year flood"], [
        ["Inflow to the reservoir", f"{B['dam_pmf'][0]:,} m³/s at {B['dam_pmf'][1]} h, {B['dam_pmf'][2]} Mm³", f"{B['dam_10k'][0]:,} m³/s at {B['dam_10k'][1]} h, {B['dam_10k'][2]} Mm³"],
        ["Side wadi J11", f"{B['j11_pmf'][0]:,} m³/s at {B['j11_pmf'][1]} h, {B['j11_pmf'][2]} Mm³", f"{B['j11_10k'][0]:,} m³/s at {B['j11_10k'][1]} h, {B['j11_10k'][2]} Mm³"],
        ["Southern catchment", f"{B['jsouth_pmf'][0]:,} m³/s at {B['jsouth_pmf'][1]} h, {B['jsouth_pmf'][2]} Mm³", f"{B['jsouth_10k'][0]:,} m³/s at {B['jsouth_10k'][1]} h, {B['jsouth_10k'][2]} Mm³"],
        ["Rain on the 2D area", f"{B['rain_pmp_mm']} mm, peak {B['rain_pmp_peak_mm_10min']} mm in 10 min", f"{B['rain_10k_mm']} mm"],
        ["Coast, two outflow lines", "Free outflow at normal depth[[fn: Normal-depth outflow: the water leaves the model at the slope of the terrain, as it would along an open shore.]]", "same"],
        ["Sea level", f"{F.SEA_LEVEL} m a.s.l., mean higher high water", "same"],
    ], "Boundary conditions of the flood-day runs (times from the start of the storm).", "bc", col_w=[1.8, 2.4, 2.4], font_sz=FS)
    d.H2("Starting the runs: the fill and the restart file")
    Fi = M["fill"]
    d.P("A run needs the reservoir full at the start. Instead of an initial-condition point, each geometry was filled once by a "
        f"{Fi['window_h']}-hour run: {Fi['q_m3s']:,} m³/s for {Fi['hours']} hours with one-hour ramps, {Fi['volume_Mm3']} Mm³, which brings the pool to "
        f"{Fi['pool_m']} m without spilling. The final state was saved as a restart file[[fn: Restart file: a saved state of the model, water levels "
        "everywhere, used as the starting point of a run.]], and every scenario starts from it with two hours of settling before a breach opens.")

    # ============================================================ 5 results: sunny day
    d.H1("Results: Sunny-day Failure")
    d.P("The sunny-day runs answer the question the emergency plan asks first: how much water, how fast, and where, when the dam fails with no flood "
        "in the wadi. {{t:s1}} gives the key results" + f"[[fn: {KEY_NOTE}]]" + ".")
    d.TBL(KEY_HDR, key_rows(["S1D", "S1N"]), "Sunny-day failure: key results.", "s1", col_w=KEY_W, font_sz=FS)
    if s1d:
        d.P(f"The breach opens two hours into the run. Within six minutes the opening is {n0(s1d.get('breach_final_width'))} m wide down to the wadi bed, and the "
            f"outflow peaks at {n0(s1d.get('peak_total_flow_m3s'))} m³/s. The reservoir level falls from {n2(peak_pool(s1d))} m to below 40 m a.s.l. within one hour "
            f"and {n0(s1d.get('volume_through_dam_Mm3'))} Mm³ leave the reservoir in about two hours. The wave fills the gorge to more than 40 m depth at the dam, "
            f"reaches the coastal plain within {hm(s1d.get('arrival_h_median'))} of the breach, the residential centre within {wt(place('S1D', TOWN))}, "
            f"the shoreline within {wt(place('S1D', SHORE))} and the last corner of the flooded area after {hm(s1d.get('arrival_h_max'))}. "
            f"In the gorge below the dam the water stands {n0(s1d.get('max_depth_m'))} m deep; on the plain depths reach {n1(s1d.get('max_depth_plain_m'))} m "
            f"and velocities {n1(s1d.get('max_velocity_ms'))} m/s. {{{{f:hyd_d}}}} and {{{{f:pool}}}} draw the flow past the dam and the reservoir level for the "
            "three scenarios; the sunny-day wave is the sharp one.")
    if os.path.exists(chart("results_dam_hydrographs_base_dikes.png")):
        d.FIG(chart("results_dam_hydrographs_base_dikes.png"), "Flow past the dam in the three scenarios.", "hyd_d", width_cm=15)
    if os.path.exists(chart("results_pool_levels.png")):
        d.FIG(chart("results_pool_levels.png"), "Reservoir level at the dam in the three scenarios.", "pool", width_cm=15)
    d.P("{{f:map_S1D_depth}} to {{f:map_S1N_haz}} map the maximum depth over the whole reach and, for Qurayat, the hazard class with the arrival "
        "of the wave drawn as isochrones, black for the earliest, greying with time. The isochrones are travel times of the water; the warning time "
        "available to people is shorter by the time it takes to detect the failure and to spread the alarm.")
    for sid in ("S1D", "S1N"):
        if os.path.exists(mapfile(sid, "hazard-iso-grey", "town")):
            d.LANDSCAPE(lambda dd, sid=sid: (dd.FIG(mapfile(sid, "depth", "reach"), f"{sid}, {DESC[sid]}: maximum depth.", f"map_{sid}_depth", width_cm=22.9, max_h_cm=15.0),
                                             dd.FIG(mapfile(sid, "hazard-iso-grey", "town"), f"{sid}: flood hazard class (AIDR) with the arrival of a 0.3 m rise after the breach, isochrones black (earliest) to grey, Qurayat.", f"map_{sid}_haz", width_cm=22.9, max_h_cm=15.0)))

    # ============================================================ 6 results: flood day
    d.H1("Results: Flood-day Failure")
    d.P("The flood-day runs add the failure to a valley already under the PMF; the difference to the no-failure run of chapter 7 is the dam's "
        "contribution. {{t:s2}} gives the key results, for the PMF and for the 10,000-year flood.")
    d.TBL(KEY_HDR, key_rows(["S2D", "S2D-F10000"]), "Flood-day failure: key results.", "s2", col_w=KEY_W, font_sz=FS)
    if s2d and s3d:
        h6_2, h6_3 = s2d.get("hazard_area_km2", {}).get("H6"), s3d.get("hazard_area_km2", {}).get("H6")
        d.P(f"The failure is triggered {hm(s2d.get('trigger_time_h'))} into the storm, when the reservoir stands at {n2(s2d.get('trigger_max_stage_hw'))} m a.s.l., "
            f"the maximum level of the no-failure run. The outflow peaks at {n0(s2d.get('peak_total_flow_m3s'))} m³/s, against {n0(s3d.get('peak_total_flow_m3s'))} m³/s "
            f"over the spillway without failure. The flooded area grows only from {n1(s3d.get('inundated_area_km2_gt0.3m'))} to {n1(s2d.get('inundated_area_km2_gt0.3m'))} km², "
            f"because the PMF has already covered the plain; what the failure adds is depth, force and speed. The area in the worst hazard class, H6, grows from "
            f"{n1(h6_3)} to {n1(h6_2)} km², and the people in the flooded area from {n0(s3d.get('consequences_par_total'))} to {n0(s2d.get('consequences_par_total'))}. "
            "The plain is under water before the dam fails, so the arrival that matters is that of the failure wave on top of the flood: the moment the "
            f"failure makes the water 0.3 m deeper than the flood alone would. That wave reaches the residential centre {wt(place('S2D', TOWN))} after the "
            f"breach and the shoreline {wt(place('S2D', SHORE))} after; chapter 9 counts the people it reaches.")
    f2, f3 = load("S2D-F10000"), load("S3D-F10000")
    if f2 and f3:
        d.P(f"During the 10,000-year flood the same failure, triggered at the {n2(f2.get('trigger_max_stage_hw'))} m pool, peaks at {n0(f2.get('peak_total_flow_m3s'))} m³/s "
            f"against {n0(f3.get('peak_total_flow_m3s'))} m³/s without failure, floods {n1(f2.get('inundated_area_km2_gt0.3m'))} km² with "
            f"{n0(f2.get('consequences_par_total'))} people, and adds 0.3 m to the water standing on {n0(reached('S2D-F10000', 0.25))} "
            "people within 15 minutes: the smaller flood lowers the peak by a tenth and changes little else.")
    for sid in ("S2D",):
        if os.path.exists(mapfile(sid, "hazard-iso-grey", "town")):
            d.LANDSCAPE(lambda dd, sid=sid: (dd.FIG(mapfile(sid, "depth", "reach"), f"{sid}, {DESC[sid]}: maximum depth.", f"map_{sid}_depth", width_cm=22.9, max_h_cm=15.0),
                                             dd.FIG(mapfile(sid, "hazard-iso-grey", "town"), f"{sid}: flood hazard class (AIDR) with the arrival of the failure wave over the PMF (0.3 m extra depth), isochrones black (earliest) to grey, Qurayat.", f"map_{sid}_haz", width_cm=22.9, max_h_cm=15.0)))

    # ============================================================ 7 results: no failure
    d.H1("Results: the PMF without Failure")
    d.P("The no-failure runs show what the valley faces from the flood alone, and give the maximum reservoir level and the moment of the failure "
        "for the flood-day runs. {{t:s3}} gives the key results for the PMF and for the 10,000-year flood.")
    d.TBL(KEY_HDR, key_rows(["S3D", "S3D-F10000"]), "PMF without failure: key results.", "s3", col_w=KEY_W, font_sz=FS)
    if s3d:
        over = (peak_pool(s3d) or 0) - F.CREST
        d.P(f"The reservoir peaks at {n2(peak_pool(s3d))} m a.s.l., {abs(over):.2f} m {'above' if over > 0 else 'below'} the crest and "
            f"{F.PARAPET - (peak_pool(s3d) or 0):.2f} m below the parapet, and the spillway passes {n0(s3d.get('peak_total_flow_m3s'))} m³/s against a design "
            f"discharge of {F.SPILL_QMAX:,.0f} m³/s: the dam is not overtopped. The flood covers {n1(s3d.get('inundated_area_km2_gt0.3m'))} km² of the plain, "
            f"much of it in the worst hazard class, but it builds up over hours: the residential centre is reached {wt(place('S3D', TOWN))} after the storm "
            f"starts and the shoreline {wt(place('S3D', SHORE))} after.")
    if f3:
        d.P(f"The 10,000-year flood, run on the same model as a check, peaks at {n2(peak_pool(f3))} m a.s.l., {n2(F.CREST - peak_pool(f3))} m below the crest, "
            f"with {n0(f3.get('peak_total_flow_m3s'))} m³/s over the spillway; it covers {n1(f3.get('inundated_area_km2_gt0.3m'))} km² of the plain with "
            f"{n0(f3.get('consequences_par_total'))} people in it, and reaches the town {wt(place('S3D-F10000', TOWN))} "
            "after the storm starts, two hours later than the PMF.")
    d.P("{{f:map_S3D_depth}} maps the maximum depth, {{f:map_S3D_haz}} the hazard class with the arrival isochrones in hours, and {{f:map_S3D_arr}} the "
        "arrival time on its own, where the slow build-up of the flood over the plain is easier to read.")
    if os.path.exists(mapfile("S3D", "depth", "reach")):
        d.LANDSCAPE(lambda dd: dd.FIG(mapfile("S3D", "depth", "reach"), f"S3D, {DESC['S3D']}: maximum depth.", "map_S3D_depth", width_cm=22.9, max_h_cm=15.0))
    if os.path.exists(mapfile("S3D", "hazard-iso-grey", "town")):
        d.LANDSCAPE(lambda dd: dd.FIG(mapfile("S3D", "hazard-iso-grey", "town"), "S3D: flood hazard class (AIDR) with the arrival of a 0.3 m rise after the start of the storm, isochrones in hours, black (earliest) to grey, Qurayat.", "map_S3D_haz", width_cm=22.9, max_h_cm=15.0))
    if os.path.exists(mapfile("S3D", "arrival-pmf", "town")):
        d.LANDSCAPE(lambda dd: dd.FIG(mapfile("S3D", "arrival-pmf", "town"), "S3D: arrival of a 0.3 m rise after the start of the storm, Qurayat.", "map_S3D_arr", width_cm=22.9, max_h_cm=15.0))

    # ============================================================ 8 sensitivity
    d.H1("Sensitivity of the Results to the Breach Parameters")
    d.P("The breach is prescribed, not computed, so its width, speed and discharge coefficient were varied one at a time to see how far the results "
        "move; the flood was varied too. {{t:senstab}} gives the key results of the eight runs, with the base cases for comparison.")
    d.TBL(KEY_HDR, key_rows(ORDER), "Sensitivity runs and base cases: key results.", "senstab", col_w=KEY_W, font_sz=FS)
    d.P("{{f:hyd_sw}} to {{f:hyd_f}} draw the flow past the dam for each family of runs, and {{f:peaks}} the peak flow and the flooded area of every run.")
    if os.path.exists(chart("results_dam_hydrographs_sunny_width.png")):
        d.FIG(chart("results_dam_hydrographs_sunny_width.png"), "Flow past the dam for the sunny-day breach-width runs (51, 85 and 153 m).", "hyd_sw", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_sunny_time.png")):
        d.FIG(chart("results_dam_hydrographs_sunny_time.png"), "Flow past the dam for the three formation times, sunny day (3, 6 and 18 min).", "hyd_st", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_sunny_coef.png")):
        d.FIG(chart("results_dam_hydrographs_sunny_coef.png"), "Flow past the dam for the two breach weir coefficients, sunny day.", "hyd_sc", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_width.png")):
        d.FIG(chart("results_dam_hydrographs_width.png"), "Flow past the dam for the flood-day breach-width check (85 and 119 m).", "hyd_w", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_time_flood.png")):
        d.FIG(chart("results_dam_hydrographs_time_flood.png"), "Flow past the dam for the flood-day failure during the PMF and during the 10,000-year flood.", "hyd_f", width_cm=15)
    if os.path.exists(chart("results_peaks_and_areas.png")):
        d.FIG(chart("results_peaks_and_areas.png"), "Peak flow and flooded area of all runs.", "peaks", width_cm=15)
    w51, w153, t3, t18, c144, s1 = load("S1D-W51"), load("S1D-W153"), load("S1D-T3m"), load("S1D-T18m"), load("S1D-C1.44"), s1d
    q = lambda x: n0((x or {}).get("peak_total_flow_m3s"))
    if w51 and w153 and t3 and t18 and c144 and s1:
        d.P(f"In short: the breach width sets the peak almost in proportion ({q(w51)}, {q(s1)} and {q(w153)} m³/s for 51, 85 and 153 m) while the "
            f"flooded area hardly moves ({n1(w51.get('inundated_area_km2_gt0.3m'))} to {n1(w153.get('inundated_area_km2_gt0.3m'))} km²), because the plain is "
            f"wide and flat. The formation time changes the peak by about a tenth either way ({q(t3)} m³/s in 3 minutes, {q(t18)} in 18) and neither "
            f"the extent nor the people in it, but it does change the first quarter hour: {n0(reached('S1D-T3m', 0.25))} people are reached within 15 minutes "
            f"of a 3-minute breach, {n0(reached('S1D', 0.25))} with 6 minutes and {n0(reached('S1D-T18m', 0.25))} with 18. The lower weir coefficient trims "
            f"the peak by {100 * (1 - c144.get('peak_total_flow_m3s', 0) / s1.get('peak_total_flow_m3s', 1)):.0f} %. On the flood day a 119 m breach raises "
            f"the peak from {q(s2d)} to {q(load('S2D-W119'))} m³/s and the flooded area by {n1((load('S2D-W119') or {}).get('inundated_area_km2_gt0.3m', 0) - (s2d or {}).get('inundated_area_km2_gt0.3m', 0))} km²; "
            "the 10,000-year flood gives the same picture as the PMF with about a tenth less flow.")

    # ============================================================ 9 consequences
    d.H1("Consequences")
    d.P("People and land use in the flooded area were counted on the population grid and the plot layer of the flood-risk study, as set out in "
        "chapter 2. {{t:cons}} gives, for every run, the people in the flooded area and how many of them are where the flood is unsafe for people "
        "(H4 or worse), the plots touched, and the area in each hazard class; {{f:people_hz}} draws the people by class.")
    rows = []
    for sid in ORDER:
        s = load(sid)
        if s is None: continue
        hz = s.get("hazard_area_km2", {})
        rows.append([sid, n0(s.get("consequences_par_total")), n0(s.get("consequences_par_H4plus")), n0(s.get("consequences_plots_total")),
                     n0(s.get("consequences_plots_Residential")), n1(hz.get("H1", 0) + hz.get("H2", 0) + hz.get("H3", 0)), n1(hz.get("H4", 0)), n1(hz.get("H5", 0)), n1(hz.get("H6", 0))])
    d.TBL(["Scenario", "People in flooded area", "of whom in H4 or worse", "Plots touched", "of which residential", "H1 to H3 (km²)", "H4 (km²)", "H5 (km²)", "H6 (km²)"],
          rows, "People, plots and hazard classes per scenario.", "cons", col_w=[1.1, 0.9, 0.9, 0.8, 0.9, 0.8, 0.7, 0.7, 0.7], font_sz=FS)
    if os.path.exists(chart("results_people_by_hazard.png")):
        d.FIG(chart("results_people_by_hazard.png"), "People in the flooded area by hazard class, per scenario.", "people_hz", width_cm=15)
    d.H2("Warning time: who is reached, and when")
    d.P("The hazard maps alone make the flood without failure look almost as bad as the failure: similar area, similar classes. What separates them "
        "is time. The sunny-day wave reaches the town within minutes of the breach; the PMF takes hours to build up, and its rain and side "
        "wadis wet the plain long before the reservoir spills. This section puts the scenarios on the clock that matters for the emergency plan, "
        "with the definition of chapter 2: a failure is timed from the breach, the flood without failure from the start of the storm, and the "
        "flood-day failure by the extra depth its wave adds to the flood. The times are travel times; the warning time available to people is "
        "shorter by the time it takes to detect the failure and to spread the alarm, which depend on the dam's instrumentation and the authorities' "
        "procedures and are not set by this study.")
    W = {sid: load_w(sid) for sid in ORDER}; W = {k: v for k, v in W.items() if v}
    fails = [sid for sid in ORDER if sid in W and not sid.startswith("S3")]
    pmfs = [sid for sid in ORDER if sid in W and sid.startswith("S3")]
    PLACES = ["Gorge exit, start of the fan", "Head of the training dikes", TOWN, SHORE, "Southern outlet, 'Outflow 2' line"]
    PLACE_LABEL = {"Gorge exit, start of the fan": "Gorge exit, start of the fan", "Head of the training dikes": "Head of the training dikes",
                   TOWN: "Qurayat, residential centre", SHORE: "Shoreline, main outlet", "Southern outlet, 'Outflow 2' line": "Shoreline, southern outlet"}
    if W:
        pl_cols = [sid for sid in ("S1D", "S1N", "S2D", "S2D-F10000", "S3D", "S3D-F10000") if sid in W]
        d.P("{{t:places}} gives the time at which the rise reaches five places along the wadi, from the gorge exit to the shore; the flood-day "
            "columns are the failure wave over the flood, the S3 columns count from the start of the storm.")
        d.TBL(["Place"] + pl_cols, [[PLACE_LABEL[name]] + [wt(W[sid]["places"].get(name)) for sid in pl_cols] for name in PLACES],
              "Arrival of a 0.3 m rise at five places: failures timed from the breach, the flood without failure from the start of the storm.", "places",
              col_w=[2.0] + [0.9] * len(pl_cols), font_sz=FS)
    if fails:
        b = W[fails[0]]["bands_h"]; hdr = ["Scenario"] + [f"within {hm(x)}" for x in b[:7]] + ["Total"]
        rows = []
        for sid in fails:
            w = W[sid]; rows.append([f"{sid}, people"] + [n0(v) for v in w["people_cum"][:7]] + [n0(w["people_total"])])
            rows.append([f"{sid}, plots"] + [n0(v) for v in w["plots_cum"][:7]] + [n0(w["plots_total"])])
        d.P("{{t:bands_fail}} counts, for the failures, the people and the plots reached within each time after the breach; the last column "
            "is everyone in the flooded area, whether or not the rise reaches 0.3 m. {{f:warn}} draws the same counts as curves.")
        d.TBL(hdr, rows, "People and plots reached within a given time after the breach (cumulative).", "bands_fail", col_w=[1.5] + [0.8] * 8, font_sz=FS)
    if pmfs:
        b = W[pmfs[0]]["bands_h"]; hdr = ["Scenario"] + [f"within {x:g} h" for x in b[:6]] + ["Total"]
        rows = []
        for sid in pmfs:
            w = W[sid]; rows.append([f"{sid}, people"] + [n0(v) for v in w["people_cum"][:6]] + [n0(w["people_total"])])
            rows.append([f"{sid}, plots"] + [n0(v) for v in w["plots_cum"][:6]] + [n0(w["plots_total"])])
        d.P("{{t:bands_pmf}} does the same for the flood without failure, in hours from the start of the storm.")
        d.TBL(hdr, rows, "People and plots reached within a given time after the start of the storm, no failure (cumulative).", "bands_pmf", col_w=[1.5] + [0.8] * 7, font_sz=FS)
    if os.path.exists(chart("results_people_vs_time.png")):
        d.FIG(chart("results_people_vs_time.png"), "People reached against time: failures from the breach (left), the flood without failure from the start of the storm (right).", "warn", width_cm=15)
    mx = [sid for sid in ("S1D", "S2D") if sid in W]
    if mx:
        b = W[mx[0]]["bands_h"]; grp = ["H1-H3", "H4", "H5", "H6"]
        hdr = ["Reached within"] + [f"{sid} {g}" for sid in mx for g in grp]
        rows = []
        for i, x in enumerate(b):
            key = str(x); rows.append([hm(x) if i == 0 else f"{hm(b[i - 1])} to {hm(x)}"] + [n0(W[sid]["matrix"][key][g]) for sid in mx for g in grp])
        rows.append(["later"] + [n0(W[sid]["matrix"]["later"][g]) for sid in mx for g in grp])
        while len(rows) > 1 and all(v in ("0", "-") for v in rows[-1][1:]): rows.pop()
        d.P("{{t:matrix}} splits the people reached in each interval by the hazard class they end up in, the two inputs a life-safety "
            "estimate needs: how little warning, and how severe the flood. H4 and worse is unsafe for people on foot.")
        d.TBL(hdr, rows, "People newly reached in each interval after the breach, by final hazard class: sunny-day and flood-day failure.", "matrix",
              col_w=[1.3] + [0.7] * (4 * len(mx)), font_sz=FS)
    d.P("{{f:map_S1D_pop}} to {{f:map_S3D_pop}} show where the people are: the population grid with the flooded area of each scenario outlined.")
    for sid in ("S1D", "S2D", "S3D"):
        if os.path.exists(mapfile(sid, "population", "town")):
            d.LANDSCAPE(lambda dd, sid=sid: dd.FIG(mapfile(sid, "population", "town"), f"{sid}: people per 100 m cell with the flooded area outlined.", f"map_{sid}_pop", width_cm=22.9, max_h_cm=15.0))

    # ============================================================ 10 discussion
    d.H1("Discussion")
    d.H2("What the failure adds to the flood")
    d.P("The flood-day runs are read against the no-failure twins: the difference in depth, arrival time and hazard class is the effect of the dam, "
        "and only that difference belongs to the dam-safety classification. The sunny-day runs stand alone: there is no flood to compare with, and "
        "everything in the flooded area is the dam's doing. Measured by extent the failure adds little to the PMF, because the flood has already "
        "covered the plain; measured by depth and hazard class it adds a third more area in the worst class; measured by time it changes everything, "
        "because the flood gives hours and the failure wave gives minutes. Arrival time is the most important difference between the scenarios.")
    d.H2("The training dikes")
    d.P(f"The dikes were designed to pass the {F.DIKE_DESIGN_RP}-year wadi flood. A dam break wave is one to two orders of magnitude larger and "
        "overtops them within minutes. The comparison of the sunny-day failure with and without them showed no significant difference in flooded "
        "area, people at risk or arrival time, so the analysis was carried on with the dikes in place only. The plan should not rely on them.")
    d.H2("Limits of the analysis")
    d.BULS([
        "The breach is prescribed, not computed: its width and speed follow the guidance for concrete gravity dams (chapter 2) and are bounded by the sensitivity runs.",
        "The terrain of the plain is the 5 m digital terrain model; buildings are not resolved, so depths in the town are those of an open plain with the town's roughness.",
        "The population grid is a 2025 estimate at 100 m; the plot layer is the flood-risk study layer.",
        f"The sea level is fixed at mean higher high water, {F.SEA_LEVEL:.2f} m a.s.l.; a storm surge coinciding with the PMF was not modelled.",
        "The arrival times are travel times of the water; detection and alarm times are not included.",
    ])

    # ============================================================ 11 conclusions
    d.H1("Conclusions and Recommendations")
    d.H2("What each scenario means")
    if s1d:
        d.P(f"**Sunny-day failure (S1D).** A failure of five monoliths with the reservoir full releases {n0(s1d.get('volume_through_dam_Mm3'))} Mm³ with a "
            f"peak of {n0(s1d.get('peak_total_flow_m3s'))} m³/s and floods {n1(s1d.get('inundated_area_km2_gt0.3m'))} km² of the coastal plain, "
            f"{n1(s1d.get('hazard_area_km2', {}).get('H6'))} km² of it in the worst hazard class, where buildings fail. About {n0(s1d.get('consequences_par_total'))} "
            f"people live in that area and {n0(s1d.get('consequences_par_H4plus'))} of them where the water is unsafe for people. The wave reaches the "
            f"residential centre {wt(place('S1D', TOWN))} after the breach and the shoreline {wt(place('S1D', SHORE))} after; {n0(reached('S1D', 0.25))} people "
            f"are reached within 15 minutes and {n0(reached('S1D', 1.0))} within an hour. This is the scenario the emergency plan must be written for: "
            "there is no flood to warn of, so the warning has to come from the dam's own monitoring, before the failure.")
    if s1n and s1d:
        d.P(f"**Sunny-day failure without the dikes (S1N).** The result is the same as with them: {n1(s1n.get('inundated_area_km2_gt0.3m'))} km² and "
            f"{n0(s1n.get('consequences_par_total'))} people against {n1(s1d.get('inundated_area_km2_gt0.3m'))} km² and {n0(s1d.get('consequences_par_total'))}. "
            "That is why the other scenarios were run with the dikes in place only.")
    if s2d and s3d:
        d.P(f"**Flood-day failure (S2D).** A failure at the peak of the PMF raises the peak flow from {n0(s3d.get('peak_total_flow_m3s'))} to "
            f"{n0(s2d.get('peak_total_flow_m3s'))} m³/s but the flooded area only from {n1(s3d.get('inundated_area_km2_gt0.3m'))} to "
            f"{n1(s2d.get('inundated_area_km2_gt0.3m'))} km², because the plain is already under the flood. The failure adds depth, force and above all "
            f"speed: the worst hazard class grows from {n1(s3d.get('hazard_area_km2', {}).get('H6'))} to {n1(s2d.get('hazard_area_km2', {}).get('H6'))} km², "
            f"the people in the flooded area from {n0(s3d.get('consequences_par_total'))} to {n0(s2d.get('consequences_par_total'))}, and the failure wave "
            f"adds 0.3 m or more to the water standing on {n0(reached('S2D', 0.25))} people within 15 minutes of the breach, reaching the shoreline in "
            f"{wt(place('S2D', SHORE))}. The 10,000-year flood gives the same picture with a tenth less flow.")
    if s3d:
        d.P(f"**PMF without failure (S3D).** The spillway passes the PMF with a maximum pool of {n2(peak_pool(s3d))} m a.s.l., "
            f"{F.PARAPET - (peak_pool(s3d) or 0):.2f} m below the parapet: the dam is not overtopped. The flood alone covers {n1(s3d.get('inundated_area_km2_gt0.3m'))} km² "
            f"with {n0(s3d.get('consequences_par_total'))} people, {n1(s3d.get('hazard_area_km2', {}).get('H6'))} km² of it in the worst class, but it takes "
            f"{wt(place('S3D', TOWN))} to reach the residential centre and about twelve hours to reach everyone: there is time to warn and to move people, "
            "which the failure scenarios do not give.")
    d.P("{{f:concl}} puts the three scenarios side by side on the four measures that matter: how much water, how much of the plain and how severely, "
        "how many people, and how fast they are reached.")
    if os.path.exists(chart("results_conclusions.png")):
        d.FIG(chart("results_conclusions.png"), "The three scenarios compared: peak flow, flooded area with the H6 share, people in the flooded area with the H4+ share, and people reached early and late.", "concl", width_cm=16)
    d.H2("Sensitivity")
    if w51 and w153 and t3 and t18 and c144 and s1 and have("S2D-W119") and f2 and f3:
        sw = load("S2D-W119")
        d.TBL(["Parameter varied", "Range tested", "Peak flow at the dam", "Flooded area", "People reached within 15 min"], [
            ["Breach width, sunny day", "51, 85, 153 m (3, 5, 9 monoliths)", f"{q(w51)} to {q(w153)} m³/s", f"{n1(w51.get('inundated_area_km2_gt0.3m'))} to {n1(w153.get('inundated_area_km2_gt0.3m'))} km²", f"{n0(reached('S1D-W51', 0.25))} to {n0(reached('S1D-W153', 0.25))}"],
            ["Formation time, sunny day", "3, 6, 18 min", f"{q(t18)} to {q(t3)} m³/s", f"{n1(t18.get('inundated_area_km2_gt0.3m'))} to {n1(t3.get('inundated_area_km2_gt0.3m'))} km²", f"{n0(reached('S1D-T18m', 0.25))} to {n0(reached('S1D-T3m', 0.25))}"],
            ["Weir coefficient, sunny day", "1.44, 1.66", f"{q(c144)} to {q(s1)} m³/s", f"{n1(c144.get('inundated_area_km2_gt0.3m'))} to {n1(s1.get('inundated_area_km2_gt0.3m'))} km²", f"{n0(reached('S1D-C1.44', 0.25))} to {n0(reached('S1D', 0.25))}"],
            ["Breach width, flood day", "85, 119 m (5, 7 monoliths)", f"{q(s2d)} to {q(sw)} m³/s", f"{n1(s2d.get('inundated_area_km2_gt0.3m'))} to {n1(sw.get('inundated_area_km2_gt0.3m'))} km²", f"{n0(reached('S2D', 0.25))} to {n0(reached('S2D-W119', 0.25))}"],
            ["Flood, with failure", "10,000-year, PMF", f"{q(f2)} to {q(s2d)} m³/s", f"{n1(f2.get('inundated_area_km2_gt0.3m'))} to {n1(s2d.get('inundated_area_km2_gt0.3m'))} km²", f"{n0(reached('S2D-F10000', 0.25))} to {n0(reached('S2D', 0.25))}"],
            ["Flood, without failure", "10,000-year, PMF", f"{q(f3)} to {q(s3d)} m³/s", f"{n1(f3.get('inundated_area_km2_gt0.3m'))} to {n1(s3d.get('inundated_area_km2_gt0.3m'))} km²", "-"],
        ], "What the sensitivity runs move, from the lowest to the highest value tested.", "sens_sum", col_w=[1.5, 1.4, 1.3, 1.2, 1.2], font_sz=FS)
        d.P("The breach width is the parameter that matters for the peak flow, and the peak follows it almost in proportion; the flooded area and the "
            "people in it hardly move with any parameter, because the plain is wide and flat and fills either way. The formation time matters for "
            "the first quarter hour of warning and for nothing else. The base case therefore gives a robust picture, and the bounds of {{t:sens_sum}} "
            "should be quoted with it.")
    d.H2("Recommendations")
    d.BULS([
        "The emergency action plan should be built on the sunny-day failure: its arrival isochrones are the warning zones, and the hazard maps give the evacuation routes and the safe ground.",
        "Warning must come from the dam, before the failure: instrumentation and an alarm procedure with a detection-plus-dissemination time well under fifteen minutes, since that is how long the wave takes to reach the town.",
        "During a major flood the plain is already flooded and the failure wave arrives within minutes; the evacuation of the low plain should therefore be part of the flood-warning procedure itself, not wait for a dam alarm.",
        "The training dikes should not be relied on in the plan: they are overtopped by every failure scenario.",
        "The results should be quoted with their bounds: peak flow within the range of the breach widths tested, the flooded area and the people in it essentially fixed.",
    ])

    # ============================================================ references
    d.H1("References", numbered=False)
    d.BULS([
        "AIDR (2017). Guideline 7-3: Flood Hazard. Australian Institute for Disaster Resilience, Melbourne.",
        "Brunner, G.W. (2014). Using HEC-RAS for Dam Break Studies. Training Document TD-39, Hydrologic Engineering Center, US Army Corps of Engineers, Davis, California.",
        "FERC (2015). Engineering Guidelines for the Evaluation of Hydropower Projects, Chapter II: Selecting and Accommodating Inflow Design Floods for Dams. Federal Energy Regulatory Commission, Washington DC.",
        "Froehlich, D.C. (1995). Embankment dam breach parameters revisited. Water Resources Engineering, Proceedings of the 1995 ASCE Conference, 887-891.",
        "Froehlich, D.C. (2008). Embankment dam breach parameters and their uncertainties. Journal of Hydraulic Engineering, 134(12), 1708-1721.",
        "ICOLD (2020). Bulletin 111: Dam Break Flood Analysis, Review and Recommendations. International Commission on Large Dams, Paris.",
        "MacDonald, T.C. and Langridge-Monopolis, J. (1984). Breaching characteristics of dam failures. Journal of Hydraulic Engineering, 110(5), 567-586.",
        "Smith, G.P., Davey, E.K. and Cox, R.J. (2014). Flood Hazard. Technical Report 2014/07, Water Research Laboratory, University of New South Wales.",
        "US Army Corps of Engineers (2024). HEC-RAS River Analysis System, version 6.6: User's Manual, 2D Modeling User's Manual and Hydraulic Reference Manual. Hydrologic Engineering Center, Davis, California.",
        "Von Thun, J.L. and Gillette, D.R. (1990). Guidance on breach parameters. Internal memorandum, US Bureau of Reclamation, Denver.",
        "Xu, Y. and Zhang, L.M. (2009). Breaching parameters for earth and rockfill dams. Journal of Geotechnical and Geoenvironmental Engineering, 135(12), 1957-1970.",
    ])

    # ============================================================ appendix
    d.H1("Appendix A: Run Register", numbered=False)
    mins = run_minutes(); total = sum(mins.get(CODE[sid], 0) for sid in ["Fill", "FillN"] + ORDER)
    d.P(f"Fourteen runs were made for this report: two reservoir fills that produced the starting state of each geometry, the four scenario runs and "
        f"the eight sensitivity runs, about {total / 60:.0f} hours of computation in all. {{{{t:reg}}}} lists them with their simulation window and the "
        "solver's own completion status.")
    rows = []
    for sid in ["Fill", "FillN"] + ORDER:
        if sid in FILLS: rows.append([sid, FILLS[sid], WINDOW[sid], "restart file written"]); continue
        s = load(sid)
        st = (s or {}).get("solution", "-") or "-"; st = "completed" if "Finished Successfully" in st else st
        rows.append([sid, DESC[sid], WINDOW[sid], st])
    d.TBL(["Run", "Description", "Simulation window", "Solver status"], rows, "Run register.", "reg", col_w=[1.2, 3.4, 1.2, 1.2], font_sz=FS)
