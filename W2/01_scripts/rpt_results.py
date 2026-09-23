# -*- coding: utf-8 -*-
"""Content of the Wadi Majlas Dam Break Analysis Report (W2, Rev 00): the runs, the results, the consequences.

Everything numeric comes from W2/04_data/results/<plan>/ (summary.json, consequences.json, trigger.json) and data_facts.py; a scenario
whose run is not finished is reported as pending, so the report can be built at any time during the campaign. Figures: charts from
results_charts.py, maps from qgis_result_maps.py, a few W1 figures for the introduction. Style rules as in the W1 methodology report:
simple words, one idea per sentence, footnotes for jargon, no plan codes in the text (scenario names only), no volume error anywhere.
"""
import os, re, json, glob
import data_facts as F
import ras_setup as S
from build_report import mr, mtxt, msub, msup, mfrac, mrad, mdelim      # Word-native equation helpers (OMML)
FC = os.path.join(W2 if "W2" in globals() else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")), "02_figures", "flowcharts")

HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
W1 = os.path.abspath(os.path.join(W2, "..", "W1"))
RES = os.path.join(W2, "04_data", "results")
CH = os.path.join(W2, "02_figures", "charts"); MAPS = os.path.join(W2, "02_figures", "maps", "results")
W1FIG = os.path.join(W1, "02_figures")
DECKFIG = os.path.join(W2, "02_figures", "deck")     # drawings taken from the design review deck (Data/20260921-Majlas Dam Design.pptx)
FS = 16   # table font (8 pt)

CODE = S.FIXED_P                                    # scenario id -> plan code
SID = {v: k for k, v in CODE.items()}               # plan code -> scenario id
BASE = ["S3D", "S3N", "S1D", "S1N", "S2D", "S2N"]
SENS = ["S1D-W51", "S1D-W153", "S1D-C1.44", "S1D-T3m", "S1D-T18m", "S2D-W119", "S3D-F10000", "S2D-F10000", "S2D-W51", "S2D-W153", "S2D-T18m", "S2D-T3m"]
# runs given up on 2026-09-23 08:50 (user decision): the breach mechanics are tested on the sunny day, where a run takes an hour, not fifteen
DROPPED = {"S2D-W51": "not run: width tested on the sunny day and once on the flood day (S2D-W119)",
           "S2D-W153": "not run: width tested on the sunny day and once on the flood day (S2D-W119)",
           "S2D-T18m": "stopped at 36 %: formation time tested on the sunny day (S1D-T18m)",
           "S2D-T3m": "stopped at 24 %: formation time tested on the sunny day (S1D-T3m)"}
DESC = {"S1D": "sunny-day failure, dikes in place", "S1N": "sunny-day failure, no dikes", "S2D": "flood-day (PMF) failure, dikes in place",
        "S2N": "flood-day (PMF) failure, no dikes", "S3D": "PMF without failure, dikes in place", "S3N": "PMF without failure, no dikes",
        "S2D-W51": "flood-day failure, breach 51 m wide (3 monoliths)", "S2D-W119": "flood-day failure, breach 119 m wide (7 monoliths)",
        "S2D-W153": "flood-day failure, breach 153 m wide (9 monoliths)", "S1D-W51": "sunny-day failure, breach 51 m wide",
        "S1D-W153": "sunny-day failure, breach 153 m wide", "S2D-T18m": "flood-day failure, breach formed in 18 minutes",
        "S2D-T3m": "flood-day failure, breach formed in 3 minutes", "S1D-C1.44": "sunny-day failure, breach weir coefficient 1.44",
        "S1D-T3m": "sunny-day failure, breach formed in 3 minutes", "S1D-T18m": "sunny-day failure, breach formed in 18 minutes",
        "S3D-F10000": "10,000-year flood without failure, dikes in place", "S2D-F10000": "flood-day failure during the 10,000-year flood"}

# ------------------------------------------------------------------ data access
def load(sid):
    """summary + consequences + trigger of one scenario, or None if the run has no products yet."""
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
    """hours -> 'H h MM min'"""
    if h is None: return "-"
    m = int(round(h * 60)); return (f"{m // 60} h" if m % 60 == 0 else f"{m // 60} h {m % 60:02d} min") if m >= 60 else f"{m} min"
def mapfile(sid, kind, ext): return os.path.join(MAPS, f"{sid} {kind} {ext}.png")
def load_w(sid):
    """warning-time products (ras_warning.py) of a scenario, or None"""
    p = os.path.join(W2, "04_data", "results", CODE[sid], "warning.json"); return json.load(open(p)) if os.path.exists(p) else None
def wt(h):
    """hours -> '5 min' / '1 h 05 min' / 'not reached'"""
    return "not reached" if h is None else ("< 5 min" if h < 1 / 12 - 1e-6 else hm(h))     # 5 min = the output step
def chart(name): return os.path.join(CH, name)
def w1(rel): return os.path.join(W1FIG, rel)

def peak_pool(s):
    return s.get("max_stage_hw") if s else None

DECISION = os.path.join(W2, "04_data", "dikes_decision.json")
def dikes_decision():
    return json.load(open(DECISION)) if os.path.exists(DECISION) else None
def dropped(sid):
    """S3N and S2N are not run when the S1N/S1D comparison found the dikes immaterial (dispatcher decision, 2026-09-22)"""
    dec = dikes_decision(); return (sid in ("S3N", "S2N") and dec is not None and not dec.get("keep_no_dikes", True)) or sid in DROPPED
def not_run(sid):
    """the table cell of a scenario without products"""
    if sid in DROPPED: return DROPPED[sid].split(":")[0] + ", see chapter 3"      # short form for the results tables; the register carries the reason
    return "not run, see chapter 3" if dropped(sid) else "pending"

def key_rows(sids):
    """one row per scenario for the results tables"""
    rows = []
    for sid in sids:
        s = load(sid)
        if s is None: rows.append([sid, DESC[sid], not_run(sid), "-", "-", "-", "-", "-"]); continue
        rows.append([sid, DESC[sid], n0(s.get("peak_total_flow_m3s")), hm(s.get("peak_time_h")), n2(peak_pool(s)),
                     n1(s.get("inundated_area_km2_gt0.3m")), f"{n0(s.get('max_depth_m'))} / {n1(s.get('max_depth_plain_m'))}", n0(s.get("consequences_par_total"))])
    return rows
KEY_HDR = ["Scenario", "Description", "Peak flow at dam (m³/s)", "Time of peak", "Max pool (m a.s.l.)", "Area > 0.3 m (km²)", "Max depth gorge / plain (m)", "People in flooded area"]

# ------------------------------------------------------------------ the report
def content(d):
    # ============================================================ front matter
    d.H1("Abbreviations and Nomenclature", numbered=False)
    d.P("Terms and short names used in this report.")
    d.TBL(["Term", "Meaning"], [
        ["AIDR", "Australian Institute for Disaster Resilience; its flood hazard classes H1 to H6 are used here"],
        ["Breach", "The opening that forms in the dam when it fails"],
        ["DTM", "Digital terrain model, the ground surface used by the model"],
        ["EAP", "Emergency action plan"],
        ["FSL", f"Full supply level, {F.FSL} m a.s.l., the spillway crest"],
        ["HEC-RAS", "Hydrologic Engineering Center River Analysis System, version 6.6, the hydraulic model"],
        ["Monolith", "One concrete block of the dam between two vertical joints; the dam has 16 of them"],
        ["PAR", "Population at risk: people living in the flooded area"],
        ["PMF, PMP", "Probable maximum flood, probable maximum precipitation"],
        ["Restart file", "A saved state of the model (water levels everywhere) used as the starting point of a run"],
        ["S1, S2, S3", "Sunny-day failure; flood-day failure during the PMF; PMF without failure"],
        ["D, N", "With the downstream training dikes; without them"],
        ["m a.s.l.", "Metres above sea level"],
    ], "Abbreviations and terms.", "abbr", col_w=[1.3, 4.7], font_sz=FS)

    # ============================================================ executive summary
    s1d, s1n, s2d, s2n, s3d, s3n = (load(x) for x in BASE[2:4] + BASE[4:6] + BASE[0:2])
    d.H1("Executive Summary", numbered=False)
    d.P(f"This report presents the dam break analysis of the Wadi Majlas Flood Protection Dam, a {F.HEIGHT_THALWEG:.0f} m high roller-compacted "
        f"concrete gravity dam about {F.DAM_TO_QURAYAT_KM} km upstream of Qurayat. It applies the methodology of the Dam Break Analysis Methodology "
        "Report Rev 00 (September 2026) with the HEC-RAS 6.6 two-dimensional model built for this study. Three scenarios were run with the downstream "
        "training dikes in place, the no-dikes condition was checked on the sunny-day scenario, and eight sensitivity runs bound the breach parameters and the flood.")
    if s1d:
        d.P(f"**Sunny-day failure (S1D).** With the reservoir at the full supply level and no flood, the sudden failure of five monoliths "
            f"(85 m of the dam) releases {n0(s1d.get('volume_through_dam_Mm3'))} Mm³ in about two hours. The peak outflow is "
            f"{n0(s1d.get('peak_total_flow_m3s'))} m³/s, reached {hm((s1d.get('peak_time_h') or 2) - 2.0)} after the failure begins. Water deeper than 0.3 m covers {n1(s1d.get('inundated_area_km2_gt0.3m'))} km² of the coastal plain; the plain is reached "
            f"within {hm(s1d.get('arrival_h_median'))}, the shoreline within {wt(((load_w("S1D") or {}).get("places") or {}).get("Shoreline, 'Outflow Sea' line"))} and the last corner of the flooded area after {hm(s1d.get('arrival_h_max'))}. About {n0(s1d.get('consequences_par_total'))} "
            f"people live in the flooded area, {n0(s1d.get('consequences_par_H4plus'))} of them where the flood is unsafe for people and vehicles or worse"
            + (f"; {n0(w1['people_cum'][0])} of them are reached within 15 minutes of the breach and {n0(w1['people_cum'][1])} within 30." if (w1 := load_w("S1D")) else "."))
    else:
        d.P("**Sunny-day failure (S1D).** Run pending.")
    if s3d:
        d.P(f"**PMF without failure (S3D).** The reservoir peaks at {n2(peak_pool(s3d))} m a.s.l. and the spillway passes {n0(s3d.get('peak_total_flow_m3s'))} m³/s. "
            + ("The dam is not overtopped." if (peak_pool(s3d) or 99) < F.PARAPET else "The parapet is overtopped."))
    else:
        d.P("**PMF without failure (S3D).** Run pending.")
    if s2d and s3d:
        d.P(f"**Flood-day failure (S2D).** The dam is assumed to fail when the reservoir reaches its maximum level during the PMF, "
            f"{hm(s2d.get('trigger_time_h'))} into the storm. The peak outflow rises from {n0(s3d.get('peak_total_flow_m3s'))} m³/s without failure to "
            f"{n0(s2d.get('peak_total_flow_m3s'))} m³/s with failure, and the flooded area from {n1(s3d.get('inundated_area_km2_gt0.3m'))} to "
            f"{n1(s2d.get('inundated_area_km2_gt0.3m'))} km²"
            + (f". The failure wave adds 0.3 m or more to the water already standing on {n0(w2['people_cum'][0])} people within 15 minutes of the breach." if (w2 := load_w("S2D")) else "."))
    else:
        d.P("**Flood-day failure (S2D).** Run pending.")
    if s1d and s1n:
        d.P(f"**Effect of the training dikes.** The dikes were designed for the 200-year wadi flood, not for a dam break. In the sunny-day failure the "
            f"flooded area is {n1(s1d.get('inundated_area_km2_gt0.3m'))} km² with the dikes and {n1(s1n.get('inundated_area_km2_gt0.3m'))} km² without; "
            f"the population at risk is {n0(s1d.get('consequences_par_total'))} and {n0(s1n.get('consequences_par_total'))} respectively.")
    d.P("The results are meant for the emergency action plan and for the design review: the arrival times and hazard maps show where warning "
        "and evacuation are needed first, and the no-failure runs confirm the spillway capacity against the PMF. {{f:glance}} puts the three base "
        "scenarios side by side.")
    if os.path.exists(chart("results_at_a_glance.png")):
        d.FIG(chart("results_at_a_glance.png"), "The base scenarios at a glance: peak flow at the dam, flooded area and people in it.", "glance", width_cm=16)

    # ============================================================ 1 introduction
    d.H1("Introduction")
    d.H2("Purpose and scope")
    d.P("A dam break analysis answers three questions: how fast and how far would the water go if the dam failed, who and what would be in its way, "
        "and how much worse is a failure than the flood the dam is already passing. This report answers them for the Wadi Majlas dam with a "
        "two-dimensional hydraulic model, and gives the numbers that the emergency action plan[[fn: Emergency action plan (EAP): the document that "
        "tells the operator and the authorities what to do, and whom to warn, when the dam is in danger. The arrival times and hazard maps in this "
        "report are its main technical input.]] needs.")
    d.P("The methodology was set out in the Dam Break Analysis Methodology Report Rev 00 (September 2026). This report applies it. Chapter 2 condenses the "
        "method; where the application had to deviate from Rev 00, the deviation and its reason are stated in chapter 4.")
    d.H2("The dam and the valley in brief")
    d.P(f"The dam is a roller-compacted concrete (RCC) gravity dam with a grout-enriched RCC facing, {F.HEIGHT_THALWEG:.0f} m above the wadi bed, {F.CREST_LENGTH:.0f} m long at the crest "
        f"({F.CREST} m a.s.l.), with a {F.PARAPET - F.CREST:.1f} m parapet to {F.PARAPET} m a.s.l. The ungated ogee spillway, {F.SPILL_NET_LENGTH:.0f} m net "
        f"length at {F.SPILL_CREST} m a.s.l., is designed for {F.SPILL_QMAX:,.0f} m³/s. The reservoir holds {F.VOL_FSL_MM3} Mm³ at the full supply level. "
        f"Downstream, the wadi leaves a gorge and crosses the coastal plain of Qurayat, where two training dikes of {F.DIKE_LENGTH_M / 1000:.1f} km "
        f"guide the {F.DIKE_DESIGN_RP}-year flood to the sea.")
    if os.path.exists(os.path.join(MAPS, "Model extent.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(MAPS, "Model extent.png"), "The model: 2D flow area, boundary condition lines, dam connection and training dikes.", "reach", width_cm=22.9, max_h_cm=15.0))

    # ============================================================ 2 methodology as applied
    d.H1("Methodology as Applied")
    d.P("This chapter condenses the methodology report to what was actually done, so that this document can be read alone. The full reasoning, "
        "the review of guidance documents and the comparison of dam types are in Rev 00.")
    d.H2("Failure mode of a concrete gravity dam")
    d.P("A roller-compacted concrete gravity dam does not erode. It fails, if at all, by the sudden sliding or overturning of one or more monoliths, "
        "the blocks between vertical contraction joints, when the water load exceeds what the foundation contact can hold. The breach is therefore "
        "rectangular, vertical-sided, essentially instantaneous, and its width is a whole number of monoliths. The regression equations used for "
        "earth and rockfill dams, which predict an eroding trapezoidal breach over hours, do not apply; the FERC and USACE guidance for concrete "
        "gravity dams is followed instead: breach width up to half the crest length, formation time of a few minutes, and a sensitivity band on both.")
    if os.path.exists(os.path.join(FC, "fc1_process.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc1_process.png"), "The dam break analysis process, from data to emergency-plan inputs.", "fc_process", width_cm=22.9, max_h_cm=15.0))
    d.P("Two hand calculations bound the peak outflow before any model is trusted. The weir equation applied to the fully open breach at the starting "
        "pool gives the upper value:")
    d.EQ(msub(mr("Q"), mr("p")) + mr("=") + mr("C") + mr("B") + msup(mdelim(mr("H") + mr("-") + msub(mr("Z"), mr("b"))), mr("1.5")), "weir",
         [("Q_{p}", "peak outflow through the breach (m³/s)"), ("C", "weir coefficient of the opening, 1.66 m^{0.5}/s in the base case"),
          ("B", "breach width, 85 m in the base case"), ("H", "pool level at failure (m a.s.l.)"), ("Z_{b}", f"breach bottom, {F.BED_AT_DAM} m a.s.l.")])
    d.P("The Ritter solution for the sudden removal of a wall onto a dry bed gives the lower value, because it accounts for the drop of the water "
        "surface at the opening:")
    d.EQ(msub(mr("Q"), mr("p")) + mr("=") + mfrac(mr("8"), mr("27")) + mr("B") + mrad(mr("g")) + msup(mdelim(mr("H") + mr("-") + msub(mr("Z"), mr("b"))), mr("1.5")), "ritter",
         [("g", "gravity, 9.81 m/s²")])
    d.P(f"For the base breach and the full supply level the two give 71,000 and 38,000 m³/s; the modelled sunny-day peak of "
        f"{n0(load('S1D').get('peak_total_flow_m3s')) if have('S1D') else '-'} m³/s lies between them, lower than the weir value because the pool "
        "drops during the six minutes of formation and the tailwater rises in the stilling basin.")
    d.H2("Scenarios and the reference case")
    d.P("Two failure scenarios bracket the question. The sunny-day failure, with the reservoir at the full supply level and no flood, gives the "
        "sharpest wave and the least warning. The flood-day failure assumes the dam fails at the peak of the probable maximum flood, when the load "
        "is highest; the failure moment is read from the no-failure run of the same flood. The no-failure run is also the reference: only what the "
        "failure adds to it counts against the dam. The scenarios and their default conditions are summarised in {{f:fc_matrix}}.")
    d.P("For every consequence measure, the dam's contribution is the difference between the failure run and its no-failure twin:")
    d.EQ(mr("ΔC") + mr("=") + msub(mr("C"), mr("failure")) + mr("-") + msub(mr("C"), mtxt("no failure")), "incr",
         [("ΔC", "the dam's contribution to any consequence measure C: depth, area, people, hazard class"),
          ("C_{failure}, C_{no failure}", "the measure in the failure run and in its no-failure twin")])
    d.H2("Hydraulic model")
    d.P("The flood is routed with HEC-RAS 6.6 in two dimensions over one mesh from the reservoir to the sea, with the dam as a weir connection whose "
        "profile carries the spillway and non-overflow crests and into which the breach is cut. The inflows and the rain come from the HEC-HMS model "
        "of the hydrology study; chapter 4 gives every input as built, and {{f:fc_hecras}} the order in which the model was assembled. The spillway "
        "follows the ogee equation and the solver keeps its time step below the Courant limit:")
    d.EQ(mr("Q") + mr("=") + msub(mr("C"), mr("s")) + mr("L") + msup(mr("H"), mr("1.5")), "ogee",
         [("Q", "spillway discharge (m³/s)"), ("C_{s}", f"discharge coefficient of the ogee, {F.MODEL['connection']['coef']} in the connection"),
          ("L", f"net crest length, {F.SPILL_NET_LENGTH:.0f} m"), ("H", "head above the crest at 84.5 m (m)")])
    d.EQ(mr("Cr") + mr("=") + mfrac(mr("V") + mr("Δt"), mr("Δx")), "courant",
         [("Cr", "Courant number, kept between 0.4 and 0.9 by halving and doubling the step"), ("V", "flow velocity plus wave celerity (m/s)"),
          ("Δt", "time step (s), 0.335 to 42.9 s"), ("Δx", "cell size in the direction of flow (m)")])
    d.H2("Consequences")
    d.P("For each run the model gives, on a 2 m grid, the maximum depth and velocity, their product, the time at which 0.3 m of water first arrives and "
        "the duration above that depth. Depth and velocity are combined into the six Australian (AIDR) flood hazard classes, from H1, safe for people "
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
    d.P("People are counted on the GHS-POP 2025 population grid and properties on the plot layer of the flood-risk study, within the flooded area "
        "and per hazard class:")
    d.EQ(mr("PAR") + mr("=") + mr("Σ") + msub(mr("P"), mr("i")) + mtxt("  for every cell i with ") + msub(mr("D"), mr("i")) + mr(">") + mr("0.3") + mtxt(" m"), "par",
         [("PAR", "population at risk"), ("P_{i}", "people in population cell i (100 m)"), ("D_{i}", "maximum depth at the centre of cell i (m)")])
    d.H2("Sensitivity and checks")
    d.P("The breach width, the formation time, the weir coefficient of the opening and the flood itself are varied one at a time from the base case, "
        "so that each result carries a bound. Whether the no-dikes geometry needed its own flood-day runs was decided by the sunny-day pair:")
    d.EQ(mfrac(mdelim(msub(mr("X"), mr("N")) + mr("-") + msub(mr("X"), mr("D")), "|", "|"), msub(mr("X"), mr("D"))) + mr("<") + mr("5") + mr("%"), "dikes",
         [("X", "flooded area, people in the flooded area and median arrival time"), ("N, D", "without and with the training dikes")])
    d.P("Every run was checked for a clean solver finish and mass conservation before its products were used. {{f:fc_campaign}} shows the sequence "
        "of runs as executed.")
    # the three flowcharts of the chapter sit together at its end (one landscape run), so the text pages stay continuous
    if os.path.exists(os.path.join(FC, "fc5_scenarios.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc5_scenarios.png"), "The three base scenarios and their default conditions.", "fc_matrix", width_cm=22.9, max_h_cm=15.0))
    if os.path.exists(os.path.join(FC, "fc3_hecras.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc3_hecras.png"), "How the HEC-RAS model was assembled.", "fc_hecras", width_cm=22.9, max_h_cm=15.0))
    if os.path.exists(os.path.join(FC, "fc6_campaign.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(FC, "fc6_campaign.png"), "The run campaign as executed, with the dikes decision gate.", "fc_campaign", width_cm=22.9, max_h_cm=15.0))

    # ============================================================ 2 scenarios and runs
    d.H1("Scenarios and Runs")
    d.P("Three scenarios were run, each with the training dikes in place (D) and without them (N). The names used throughout this report are:")
    d.TBL(["Name", "Scenario", "Reservoir at the start", "Inflow", "Failure"], [
        ["S1D, S1N", "Sunny-day failure", f"Full supply level, {F.FSL} m", "None", "Five monoliths at a set time, two hours into the run"],
        ["S2D, S2N", "Flood-day failure", f"Full supply level, {F.FSL} m", "PMF, with rain on the plain", "Five monoliths at the moment the reservoir reaches its maximum level"],
        ["S3D, S3N", "PMF without failure", f"Full supply level, {F.FSL} m", "PMF, with rain on the plain", "None"],
    ], "The scenarios.", "scen", col_w=[0.9, 1.3, 1.5, 1.4, 2.4], font_sz=FS)
    d.P("A sunny-day failure[[fn: Sunny-day failure: a failure with no flood in the river, for example from a foundation problem or an earthquake. "
        "It gives the least warning, because nobody expects a flood.]] gives the largest breach flow relative to the normal flow and the least warning. "
        "The flood-day failure is assumed to happen at the worst moment of the PMF, when the reservoir is at its highest and the load on the dam is "
        "greatest; this is the usual convention for a concrete gravity dam, whose critical case is the peak water load rather than overtopping. "
        "The PMF without failure is the reference that shows what the failure adds.")
    dec = dikes_decision()
    if dec is not None:
        d.H2("Why the no-dikes flood-day runs were not needed")
        rd = dec["relative_differences"]; a, b = dec["S1D"], dec["S1N"]
        d.P("The training dikes were designed for the 200-year wadi flood. Before running the flood-day pair without them, the two sunny-day runs "
            "were compared, because they isolate the dam's contribution with nothing else in the valley. The differences are negligible:")
        d.TBL(["Quantity", "S1D, with dikes", "S1N, without dikes", "Difference"], [
            ["Peak flow at the dam (m³/s)", n0(a["peak_total_flow_m3s"]), n0(b["peak_total_flow_m3s"]), f"{rd['peak_total_flow_m3s']:.1%}"],
            ["Flooded area > 0.3 m (km²)", n1(a["inundated_area_km2_gt0.3m"]), n1(b["inundated_area_km2_gt0.3m"]), f"{rd['inundated_area_km2_gt0.3m']:.1%}"],
            ["People in the flooded area", n0(a["par_total"]), n0(b["par_total"]), f"{rd['par_total']:.1%}"],
            ["Median arrival time on the plain", hm(a["arrival_h_median"]), hm(b["arrival_h_median"]), f"{rd['arrival_h_median']:.1%}"],
        ], "Effect of the training dikes on the sunny-day failure.", "dikes_cmp", col_w=[2.4, 1.3, 1.3, 1.0], font_sz=FS)
        d.P("A wave of this size overtops the dikes within minutes and spreads over the whole plain; the dikes neither contain it nor steer it "
            + ("to a measurable degree. The flood-day pair without dikes (S3N, S2N) was therefore not run, and the with-dikes runs stand for both conditions. "
               "This is a reasoned departure from the methodology report, which had planned both." if not dec["keep_no_dikes"] else
               "in the sunny-day case beyond the threshold of 5 %, so the flood-day pair without dikes was run as planned."))
    d.H2("Sensitivity runs")
    d.P("The sensitivity runs change one breach parameter at a time from the base case: the breach width (three, five, seven and nine monoliths), "
        "the formation time (3, 6 and 18 minutes), the weir coefficient of the breach opening, and the flood (the 10,000-year flood instead of the PMF).")
    d.TBL(["Name", "What is changed from the base case", "Purpose"], [
        ["S1D-W51, S1D-W153", "Breach width 51 and 153 m (three and nine monoliths) instead of 85 m, sunny day", "How much the peak and the flooded area depend on how many monoliths go"],
        ["S2D-W119", "Breach width 119 m (seven monoliths), flood day", "The same question on the flood day, one check"],
        ["S1D-T3m, S1D-T18m", "Formation time 3 min and 18 min instead of 6 min, sunny day", "Whether the speed of the failure matters"],
        ["S1D-C1.44", "Breach weir coefficient 1.44 instead of 1.66, sunny day", "Lower bound of the flow through the opening"],
        ["S3D-F10000, S2D-F10000", "10,000-year flood instead of the PMF, without and with failure", "How the flood-day results change with a smaller flood"],
    ], "The sensitivity runs.", "sens", col_w=[1.8, 2.6, 2.6], font_sz=FS)
    d.P("The breach mechanics are tested on the sunny day, where the dam's contribution stands alone and a run takes an hour. The flood-day runs first "
        "planned for width (51 and 153 m) and formation time were stopped on 23 September once the sunny-day family had answered the question, S2D-W119 "
        "giving the one flood-day check on width, and the machine time went to the 10,000-year pair.")

    # ============================================================ 3 the model as built
    d.H1("The Model as Built")
    M = F.MODEL
    d.H2("Terrain, mesh and roughness")
    d.P(f"The model is one two-dimensional area, '{M['area_name']}', of {M['area_km2']} km² in HEC-RAS 6.6, from the upper reservoir to the shoreline. "
        f"The terrain is the {M['terrain_base']}; the dam body was cut out of it so that the dam connection alone controls the flow. Two terrains and two "
        f"geometries were built, with the training dikes ({M['terrain_dikes']}) and without ({M['terrain_nodikes']}).")
    d.TBL(["Item", "As built"], [
        ["Cells", f"{M['cells_dikes']:,} with dikes, {M['cells_nodikes']:,} without"],
        ["Cell size", f"median {M['cell_size_m']['median']} m, 10 % of cells below {M['cell_size_m']['p10']} m, largest {M['cell_size_m']['max']} m; "
                      f"{M['connection_cells_m'][0]} m along the dam connection, {M['connection_cells_m'][1]} m beyond"],
        ["Breaklines", f"{M['breaklines']} lines at {M['breakline_spacing_m'][0]} to {M['breakline_spacing_m'][1]} m: dike crests, wadi banks, road embankments, dam axis"],
        ["Roughness", "; ".join(f"n = {k}: {v} % of the area" for k, v in M['manning'].items())],
        ["Solver", f"{M['solver']['equation']}, theta {M['solver']['theta']}, eddy viscosity {M['solver']['eddy_viscosity']}, base step {M['solver']['base_step_s']} s adapted on Courant "
                   f"{M['solver']['courant'][0]} to {M['solver']['courant'][1]} (floor {M['solver']['min_step_s']} s), output every {M['solver']['output_min']} min, maps every {M['solver']['mapping_min']} min"],
    ], "The 2D model as built.", "mesh", col_w=[1.2, 5.0], font_sz=FS)
    d.H2("The dam as designed")
    d.P(f"The model represents the dam as finalised in the design review of 21 September 2026. It is a roller-compacted concrete (RCC) gravity dam with a grout-enriched RCC facing on a straight axis, "
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
        ["Crest / parapet top", f"{F.CREST} / {F.PARAPET} m a.s.l.", f"Non-overflow crest of the connection at {F.PARAPET} m: the parapet is credited, so the PMF pool of 96.06 m does not overtop the dam"],
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
    ], "The dam as designed and where each value enters the model (design review, 21 September 2026).", "dam", col_w=[1.4, 2.6, 3.0], font_sz=FS)
    # the drawings carry small lettering: one landscape page each, cropped to the dam (adjacent landscape blocks merge into one section)
    d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(DECKFIG, "dam_elevation_monoliths_crop.png"), f"Upstream elevation of the dam: the {F.N_BLOCKS} monoliths B1 to B17 with their widths, crest {F.CREST} m, parapet {F.PARAPET} m and the foundation at {F.FOUNDATION_LEVEL:.1f} m (design review, September 2026).", "dam_elev", width_cm=22.9, max_h_cm=15.0))
    d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(DECKFIG, "dam_section_nonoverflow_crop.png"), f"Section through a non-overflow block: crest {F.CREST} m, parapet {F.PARAPET} m, galleries at 74.0 and 42.5 m, faces {F.US_SLOPE} and {F.DS_SLOPE} (design review, September 2026).", "dam_sec", width_cm=22.9, max_h_cm=15.0))
    d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(DECKFIG, "dam_section_spillway_crop.png"), f"Section through a spillway block: ogee crest {F.SPILL_CREST} m, stepped chute, stilling basin floor {F.BASIN_FLOOR} m, foundation {F.FOUNDATION_LEVEL:.1f} m (design review, September 2026).", "spill_sec", width_cm=22.9, max_h_cm=15.0))
    d.H2("The dam and the breach")
    d.P("The dam is a weir connection[[fn: SA/2D connection: the HEC-RAS element that links two parts of a 2D area through a "
        "structure. Its profile carries the spillway crest and the non-overflow crest; the breach is cut into it.]] whose profile carries the "
        f"non-overflow crest at {F.PARAPET} m and the ogee at {F.SPILL_CREST} m from station 60 to 260 ({F.SPILL_NET_LENGTH:.0f} m); weir coefficient "
        f"{M['connection']['coef']} ({M['connection']['weir_shape']} option), width {M['connection']['width_m']:.0f} m, submergence limit "
        f"{M['connection']['max_submergence']}. The breach parameters follow the methodology report:")
    d.TBL(["Parameter", "Base value", "Basis"], [
        ["Failure mode", "Sliding of whole monoliths, vertical sides", "Concrete gravity dam; regression equations for earth dams do not apply"],
        ["Breach width", "85 m (five monoliths of 17 m)", "Two spillway bays; FERC/USACE guidance: up to half the crest length"],
        ["Breach bottom", f"{F.BREACH_BOTTOM} m a.s.l.", "Wadi bed at the axis"],
        ["Formation time", "0.1 h (6 min)", "Instantaneous for a concrete dam; the shortest HEC-RAS accepts without instability"],
        ["Weir coefficient", "1.66 (SI)", "HEC-RAS range for a broad crest, 1.44 to 1.66"],
        ["Progression", "Sine wave", "HEC-RAS option for a fast, smooth opening"],
        ["Trigger, sunny day", "Set time, 2 h into the run", "Gives the model two hours to settle on the restart"],
        ["Trigger, flood day", "Set time = moment of maximum pool in the no-failure run", "Failure at the highest load; read from S3D or S3N"],
    ], "Breach parameters of the base case.", "breach", col_w=[1.4, 2.2, 3.4], font_sz=FS)
    d.H2("Boundary conditions")
    B = M["bc"]
    d.P(f"Inflow to the reservoir and the flows of the two side wadis joining below the dam (J11 and the southern catchment of {F.SOUTH_CATCHMENT_KM2} km²) "
        "come from the HEC-HMS model of the hydrology study, basin model 'Basin 1 Res2', re-run with the southern catchment added. The three elements "
        "whose hydrographs are taken are the junction just upstream of the reservoir, J11 and Jsouth. Rain falls directly on the modelled area with the "
        f"same storm, reduced by the areal factor of {B['rain_areal_factor']}. The sunny-day runs have no inflow and no rain.")
    if os.path.exists(os.path.join(MAPS, "HEC-HMS model.png")):
        d.LANDSCAPE(lambda dd: dd.FIG(os.path.join(MAPS, "HEC-HMS model.png"), "The HEC-HMS basin model and the three elements whose hydrographs feed the 2D model.", "hms", width_cm=22.9, max_h_cm=15.0))
    if os.path.exists(chart("results_inputs_hydrographs.png")):
        d.FIG(chart("results_inputs_hydrographs.png"), "The inputs to the flood-day runs: rain on the 2D area and the inflow hydrographs at the three boundary lines, PMF and 10,000-year flood.", "inputs", width_cm=15)
    d.P("The numbers were taken from two workbooks kept with the model inputs: 'Hydrology Data.xlsx' holds the three hydrographs and the rain series "
        "exactly as entered in HEC-RAS for the PMF and the 10,000-year flood; 'FM rainfall 2-PMP.xlsm' holds the 10-minute rainfall patterns per return "
        "period and for the PMP from which those series, with the areal reduction factor, were built.")
    d.TBL(["Boundary", "PMF", "10,000-year flood"], [
        ["Reservoir inflow, 'Majlas Dam' line", f"{B['dam_pmf'][0]:,} m³/s at {B['dam_pmf'][1]} h, {B['dam_pmf'][2]} Mm³", f"{B['dam_10k'][0]:,} m³/s at {B['dam_10k'][1]} h, {B['dam_10k'][2]} Mm³"],
        ["Side wadi J11", f"{B['j11_pmf'][0]:,} m³/s at {B['j11_pmf'][1]} h, {B['j11_pmf'][2]} Mm³", f"{B['j11_10k'][0]:,} m³/s at {B['j11_10k'][1]} h, {B['j11_10k'][2]} Mm³"],
        ["Southern catchment, 'Jsouth' line", f"{B['jsouth_pmf'][0]:,} m³/s at {B['jsouth_pmf'][1]} h, {B['jsouth_pmf'][2]} Mm³", f"{B['jsouth_10k'][0]:,} m³/s at {B['jsouth_10k'][1]} h, {B['jsouth_10k'][2]} Mm³"],
        ["Rain on the 2D area", f"{B['rain_pmp_mm']} mm, peak {B['rain_pmp_peak_mm_10min']} mm in 10 min", f"{B['rain_10k_mm']} mm"],
        ["Coast, 'Outflow Sea' and 'Outflow 2' lines", B["outflow"], "same"],
        ["Sea level", f"Mean higher high water at Qurayyat, {F.TIDE['mhhw_cd']} m above chart datum = {F.SEA_LEVEL} m a.s.l. (chart datum {F.TIDE['z0_m']} m below mean sea level; "
                      f"{F.TIDE['source']}); the shoreline terrain is higher, so the sea does not back water into the model", "same"],
    ], "Boundary conditions of the flood-day runs (times from the start of the storm).", "bc", col_w=[2.0, 2.3, 2.3], font_sz=FS)
    d.H2("Starting the runs: the fill and the restart file")
    Fi = M["fill"]
    d.P("A run needs the reservoir full at the start. Instead of an initial-condition point, each geometry was filled once by a "
        f"{Fi['window_h']}-hour run: {Fi['q_m3s']:,} m³/s for {Fi['hours']} hours with one-hour ramps, {Fi['volume_Mm3']} Mm³, which brings the pool to "
        f"{Fi['pool_m']} m without spilling. The final state was saved as a restart file, and every scenario starts from it. The fills carry the same "
        "rain block as the flood runs, with zero values, because HEC-RAS cannot start a run with rain from a restart written by a run without it.")
    d.H2("Solver and deviations from the methodology")
    d.P("All runs use the shallow-water equations with the Eulerian-Lagrangian scheme (SWE-ELM)[[fn: HEC-RAS offers two full momentum solvers. "
        "SWE-ELM is the faster and more robust one; SWE-EM keeps more of the momentum terms but proved unstable on this mesh at the first spill over the "
        "dry chute.]], an adaptive time step on a Courant number[[fn: Courant number: the distance the water moves in one time step divided by the "
        "cell size. Keeping it below one keeps the solution stable.]] of 0.4 to 0.9, output every minute and maps every five minutes.")
    d.P("The application deviates from Rev 00 in five points, each for a reason found during the runs:")
    d.BULS([
        "Solver: SWE-ELM instead of the SWE-EM named in the methodology, for the stability reason given in the footnote.",
        f"Non-overflow crest: the parapet ({F.PARAPET} m) is credited as the overtopping level, as on the design drawings.",
        "Flood-day trigger: set at the time of maximum pool of the no-failure twin rather than at a fixed level, so that a PMF peaking below the parapet still triggers the failure.",
        "Initial state: fill run and restart file instead of an initial-condition point; the result is the same start.",
        "Flood-day sensitivity runs use a 36-hour window (the breach falls between hour 15 and 20) instead of 60 hours, the sunny-day runs 14 hours (breach at hour 2); the base flood-day runs keep 60 hours.",
    ])

    # ============================================================ 4 results: no failure
    d.H1("Results: the PMF without Failure")
    d.P("The no-failure runs show what the valley faces from the PMF alone, and give the maximum reservoir level and the moment of the failure for the flood-day runs.")
    d.TBL(KEY_HDR,
          key_rows(["S3D", "S3N", "S3D-F10000"]), "PMF without failure: key results.", "s3", col_w=[0.9, 2.0, 1.0, 0.9, 0.9, 0.8, 0.7, 0.9], font_sz=FS)
    if s3d:
        over = (peak_pool(s3d) or 0) - F.CREST
        d.P(f"With the dikes in place the reservoir peaks at {n2(peak_pool(s3d))} m a.s.l., {abs(over):.2f} m {'above' if over > 0 else 'below'} the crest and "
            f"{F.PARAPET - (peak_pool(s3d) or 0):.2f} m below the parapet, and the spillway passes {n0(s3d.get('peak_total_flow_m3s'))} m³/s against a design "
            f"discharge of {F.SPILL_QMAX:,.0f} m³/s.")
    f3 = load("S3D-F10000")
    if f3:
        d.P(f"The 10,000-year flood, run on the same model as a check, peaks at {n2(peak_pool(f3))} m a.s.l., {n2(F.CREST - peak_pool(f3))} m below the crest, "
            f"with {n0(f3.get('peak_total_flow_m3s'))} m³/s over the spillway; it covers {n1(f3.get('inundated_area_km2_gt0.3m'))} km² of the plain with "
            f"{n0(f3.get('consequences_par_total'))} people in it, and reaches the town {hm((load_w('S3D-F10000') or {}).get('places', {}).get('Qurayat, residential centre'))} "
            "after the storm starts, two hours later than the PMF.")
    for sid in ("S3D", "S3N"):
        if os.path.exists(mapfile(sid, "depth", "reach")):
            d.LANDSCAPE(lambda dd, sid=sid: dd.FIG(mapfile(sid, "depth", "reach"), f"{sid}, {DESC[sid]}: maximum depth.", f"map_{sid}_depth", width_cm=22.9, max_h_cm=15.0))
        if os.path.exists(mapfile(sid, "hazard-iso-grey", "town")):     # hazard fill with arrival isochrones (user, 2026-09-23 12:40)
            d.LANDSCAPE(lambda dd, sid=sid: dd.FIG(mapfile(sid, "hazard-iso-grey", "town"), f"{sid}: flood hazard class (AIDR) with the arrival of a 0.3 m rise after the start of the storm, in hours (black earliest), Qurayat.", f"map_{sid}_haz", width_cm=22.9, max_h_cm=15.0))

    # ============================================================ 5 results: sunny day
    d.H1("Results: Sunny-day Failure")
    d.P("The sunny-day runs answer the question the emergency plan asks first: how much water, how fast, and where, when the dam fails with no flood in the wadi.")
    d.TBL(KEY_HDR,
          key_rows(["S1D", "S1N"]), "Sunny-day failure: key results.", "s1", col_w=[0.9, 2.0, 1.0, 0.9, 0.9, 0.8, 0.7, 0.9], font_sz=FS)
    if s1d:
        d.P(f"The breach opens two hours into the run. Within six minutes the opening is {n0(s1d.get('breach_final_width'))} m wide down to the wadi bed, and the "
            f"outflow peaks at {n0(s1d.get('peak_total_flow_m3s'))} m³/s. The reservoir level falls from {n2(peak_pool(s1d))} m to below 40 m a.s.l. within one hour "
            f"and {n0(s1d.get('volume_through_dam_Mm3'))} Mm³ leave the reservoir in about two hours. The wave fills the gorge to more than 40 m depth at the dam, "
            f"reaches the coastal plain within {hm(s1d.get('arrival_h_median'))} of the breach, the shoreline within {wt(((load_w("S1D") or {}).get("places") or {}).get("Shoreline, 'Outflow Sea' line"))} and the last corner of the flooded area after {hm(s1d.get('arrival_h_max'))}. "
            f"In the gorge below the dam the water stands {n0(s1d.get('max_depth_m'))} m deep; on the plain depths reach {n1(s1d.get('max_depth_plain_m'))} m "
            f"and velocities {n1(s1d.get('max_velocity_ms'))} m/s.")
    if os.path.exists(chart("results_dam_hydrographs_base_dikes.png")):
        d.FIG(chart("results_dam_hydrographs_base_dikes.png"), "Flow past the dam, base runs with dikes.", "hyd_d", width_cm=15)
    if os.path.exists(chart("results_pool_levels.png")):
        d.FIG(chart("results_pool_levels.png"), "Reservoir level at the dam, base runs.", "pool", width_cm=15)
    for sid in ("S1D", "S1N"):
        if os.path.exists(mapfile(sid, "hazard-iso-grey", "town")):     # hazard fill with arrival isochrones replaces the arrival and hazard maps (user, 2026-09-23 12:40)
            d.LANDSCAPE(lambda dd, sid=sid: (dd.FIG(mapfile(sid, "depth", "reach"), f"{sid}, {DESC[sid]}: maximum depth.", f"map_{sid}_depth", width_cm=22.9, max_h_cm=15.0),
                                             dd.FIG(mapfile(sid, "hazard-iso-grey", "town"), f"{sid}: flood hazard class (AIDR) with the arrival of a 0.3 m rise after the breach, isochrones black (earliest) to grey, Qurayat.", f"map_{sid}_haz", width_cm=22.9, max_h_cm=15.0)))
        elif os.path.exists(mapfile(sid, "depth", "reach")):
            d.LANDSCAPE(lambda dd, sid=sid: (dd.FIG(mapfile(sid, "depth", "reach"), f"{sid}, {DESC[sid]}: maximum depth.", f"map_{sid}_depth", width_cm=22.9, max_h_cm=15.0),
                                             dd.FIG(mapfile(sid, "arrival", "town"), f"{sid}: arrival time of a 0.3 m depth after the breach, Qurayat.", f"map_{sid}_arr", width_cm=22.9, max_h_cm=15.0),
                                             dd.FIG(mapfile(sid, "hazard", "town"), f"{sid}: flood hazard class (AIDR), Qurayat.", f"map_{sid}_haz", width_cm=22.9, max_h_cm=15.0)))

    # ============================================================ 6 results: flood day
    d.H1("Results: Flood-day Failure")
    d.P("The flood-day runs add the failure to a valley already under the PMF; the difference to the no-failure run of chapter 5 is the dam's contribution.")
    d.TBL(KEY_HDR,
          key_rows(["S2D", "S2N", "S2D-F10000"]), "Flood-day failure: key results.", "s2", col_w=[0.9, 2.0, 1.0, 0.9, 0.9, 0.8, 0.7, 0.9], font_sz=FS)
    if s2d:
        h6_2, h6_3 = s2d.get("hazard_area_km2", {}).get("H6"), (s3d or {}).get("hazard_area_km2", {}).get("H6")
        d.P(f"The failure is triggered {hm(s2d.get('trigger_time_h'))} into the storm, when the reservoir stands at {n2(s2d.get('trigger_max_stage_hw'))} m a.s.l. "
            f"The outflow peaks at {n0(s2d.get('peak_total_flow_m3s'))} m³/s, against {n0(s3d.get('peak_total_flow_m3s')) if s3d else '-'} m³/s over the spillway "
            f"without failure. The flooded area grows only from {n1(s3d.get('inundated_area_km2_gt0.3m')) if s3d else '-'} to {n1(s2d.get('inundated_area_km2_gt0.3m'))} km², "
            f"because the PMF has already covered the plain; what the failure adds is depth and force. The area in the worst hazard class, H6, grows from "
            f"{n1(h6_3)} to {n1(h6_2)} km², and the people in the flooded area from {n0((s3d or {}).get('consequences_par_total'))} to {n0(s2d.get('consequences_par_total'))}. "
            "The plain is under water before the dam fails, so the arrival that matters is that of the failure wave on top of the flood: chapter 9 "
            "times the moment the failure adds 0.3 m to the depth of the no-failure run and counts the people it reaches.")
    f2, f3 = load("S2D-F10000"), load("S3D-F10000")
    if f2 and f3:
        d.P(f"During the 10,000-year flood the same failure, triggered at the {n2(f2.get('trigger_max_stage_hw'))} m pool, peaks at {n0(f2.get('peak_total_flow_m3s'))} m³/s "
            f"against {n0(f3.get('peak_total_flow_m3s'))} m³/s without failure, floods {n1(f2.get('inundated_area_km2_gt0.3m'))} km² with "
            f"{n0(f2.get('consequences_par_total'))} people, and adds 0.3 m to the water standing on {n0((load_w('S2D-F10000') or {}).get('people_cum', [None])[0])} "
            "people within 15 minutes: the smaller flood lowers the peak by a tenth and changes little else.")
    else:
        d.P("Run pending.")
    for sid in ("S2D", "S2N"):
        if os.path.exists(mapfile(sid, "hazard-iso-grey", "town")):
            d.LANDSCAPE(lambda dd, sid=sid: (dd.FIG(mapfile(sid, "depth", "reach"), f"{sid}, {DESC[sid]}: maximum depth.", f"map_{sid}_depth", width_cm=22.9, max_h_cm=15.0),
                                             dd.FIG(mapfile(sid, "hazard-iso-grey", "town"), f"{sid}: flood hazard class (AIDR) with the arrival of the failure wave over the PMF (0.3 m extra depth), isochrones black (earliest) to grey, Qurayat.", f"map_{sid}_haz", width_cm=22.9, max_h_cm=15.0)))
        elif os.path.exists(mapfile(sid, "depth", "reach")):
            d.LANDSCAPE(lambda dd, sid=sid: (dd.FIG(mapfile(sid, "depth", "reach"), f"{sid}, {DESC[sid]}: maximum depth.", f"map_{sid}_depth", width_cm=22.9, max_h_cm=15.0),
                                             dd.FIG(mapfile(sid, "hazard", "town"), f"{sid}: flood hazard class (AIDR), Qurayat.", f"map_{sid}_haz", width_cm=22.9, max_h_cm=15.0)))

    # ============================================================ 7 sensitivity
    d.H1("Sensitivity of the Results to the Breach Parameters")
    d.P("The breach is prescribed, not computed, so its width, speed and discharge coefficient were varied one at a time to see how far the results move.")
    d.TBL(KEY_HDR,
          key_rows(SENS), "Sensitivity runs: key results.", "senstab", col_w=[1.1, 2.0, 1.0, 0.9, 0.9, 0.8, 0.7, 0.9], font_sz=FS)
    if os.path.exists(chart("results_dam_hydrographs_sunny_width.png")):
        d.FIG(chart("results_dam_hydrographs_sunny_width.png"), "Flow past the dam for the sunny-day breach-width runs (51, 85 and 153 m).", "hyd_sw", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_sunny_coef.png")):
        d.FIG(chart("results_dam_hydrographs_sunny_coef.png"), "Flow past the dam for the two breach weir coefficients, sunny day.", "hyd_sc", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_sunny_time.png")):
        d.FIG(chart("results_dam_hydrographs_sunny_time.png"), "Flow past the dam for the three formation times, sunny day (3, 6 and 18 min).", "hyd_st", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_width.png")):
        d.FIG(chart("results_dam_hydrographs_width.png"), "Flow past the dam for the flood-day breach-width check (85 and 119 m).", "hyd_w", width_cm=15)
    if os.path.exists(chart("results_dam_hydrographs_time_flood.png")):
        d.FIG(chart("results_dam_hydrographs_time_flood.png"), "Flow past the dam for the flood-day failure during the PMF and during the 10,000-year flood.", "hyd_f", width_cm=15)
    if os.path.exists(chart("results_peaks_and_areas.png")):
        d.FIG(chart("results_peaks_and_areas.png"), "Peak flow and flooded area of all runs.", "peaks", width_cm=15)
    w51, w153, t3, t18, c144, s1 = load("S1D-W51"), load("S1D-W153"), load("S1D-T3m"), load("S1D-T18m"), load("S1D-C1.44"), load("S1D")
    q = lambda x: n0((x or {}).get("peak_total_flow_m3s"))
    r15 = lambda sid: n0((load_w(sid) or {}).get("people_cum", [None])[0])
    d.P(f"The reading of these runs is in chapter 10. In short: the breach width sets the peak almost in proportion ({q(w51)}, {q(s1)} and {q(w153)} m³/s "
        f"for 51, 85 and 153 m) while the flooded area hardly moves ({n1((w51 or {}).get('inundated_area_km2_gt0.3m'))} to "
        f"{n1((w153 or {}).get('inundated_area_km2_gt0.3m'))} km²), because the plain is wide and flat. The formation time changes the peak by about a "
        f"tenth either way ({q(t3)} m³/s in 3 minutes, {q(t18)} in 18) and neither the extent nor the people in it, but it does change the first quarter "
        f"hour: {r15('S1D-T3m')} people are reached within 15 minutes of a 3-minute breach, {r15('S1D')} with 6 minutes and {r15('S1D-T18m')} with 18. "
        f"The lower weir coefficient trims the peak by {n0(100 * (1 - (c144 or {}).get('peak_total_flow_m3s', 0) / max((s1 or {}).get('peak_total_flow_m3s', 1), 1)))} %.")

    # ============================================================ 8 consequences
    d.H1("Consequences")
    d.P("People and land use in the flooded area were counted on the population grid[[fn: GHS-POP 2025, a global population grid of 100 m cells "
        "from the European Commission; the count is the sum of the cells whose centre lies in water deeper than 0.3 m.]] and the plot layer of the "
        "flood-risk study. The hazard classes follow the Australian flood hazard curves (AIDR), which combine depth and velocity into six classes "
        "from H1, safe for people and vehicles, to H6, where buildings fail.")
    rows = []
    for sid in BASE + SENS:
        s = load(sid)
        if s is None: continue
        hz = s.get("hazard_area_km2", {})
        rows.append([sid, n0(s.get("consequences_par_total")), n0(s.get("consequences_par_H4plus")), n0(s.get("consequences_plots_total")),
                     n0(s.get("consequences_plots_Residential")), n1(hz.get("H1", 0) + hz.get("H2", 0) + hz.get("H3", 0)), n1(hz.get("H4", 0)), n1(hz.get("H5", 0)), n1(hz.get("H6", 0))])
    if rows:
        d.TBL(["Scenario", "People in flooded area", "of whom in H4 or worse", "Plots touched", "of which residential", "H1 to H3 (km²)", "H4 (km²)", "H5 (km²)", "H6 (km²)"],
              rows, "People, plots and hazard classes per scenario.", "cons", col_w=[1.1, 0.9, 0.9, 0.8, 0.9, 0.8, 0.7, 0.7, 0.7], font_sz=FS)
    else:
        d.P("Run products pending.")
    if os.path.exists(chart("results_people_by_hazard.png")):
        d.FIG(chart("results_people_by_hazard.png"), "People in the flooded area by hazard class, per scenario.", "people_hz", width_cm=15)
    # ---- warning time (user, 2026-09-23 06:30): the hazard maps make the PMF look as bad as a failure; what separates them is time
    d.H2("Warning time: who is reached, and when")
    d.P("The hazard maps alone make the PMF without failure look almost as bad as the failure: similar area, similar classes. What separates them "
        "is time. The sunny-day wave reaches the town within minutes of the breach; the PMF takes hours to build up, and its rain and side "
        "wadis wet the plain long before the reservoir spills. This section puts the scenarios on the clock that matters for the emergency plan.")
    d.P("Each scenario is timed from its own trigger: a failure from the moment the breach opens, the PMF without failure from the start of the "
        "storm. A place counts as reached when the water there rises 0.3 m above what was there before the trigger. For the flood-day failure the "
        "plain is already under the PMF when the dam goes, so it is timed against the no-failure run at the same instant: the moment the failure "
        "makes the water 0.3 m deeper than the flood alone would. The model gives travel times; the warning time available to people is shorter "
        "by the time it takes to detect the failure and to spread the alarm, which depend on the dam's instrumentation and the authorities' "
        "procedures and are not set by this study.")
    W = {sid: load_w(sid) for sid in BASE + SENS}; W = {k: v for k, v in W.items() if v}
    fails = [sid for sid in ("S1D", "S1N", "S1D-W51", "S1D-W153", "S1D-C1.44", "S1D-T3m", "S1D-T18m", "S2D", "S2D-W119", "S2D-F10000") if sid in W]
    pmfs = [sid for sid in ("S3D", "S3D-F10000") if sid in W]
    PLACES = ["Gorge exit, start of the fan", "Head of the training dikes", "Qurayat, residential centre", "Shoreline, 'Outflow Sea' line", "Southern outlet, 'Outflow 2' line"]
    if W:
        pl_cols = [sid for sid in ("S1D", "S1N", "S1D-W51", "S1D-W153", "S2D", "S2D-W119", "S3D") if sid in W]
        d.P("{{t:places}} gives the time at which the rise reaches five places along the wadi, from the gorge exit to the shore; the flood-day "
            "columns are the failure wave over the PMF, the S3D column counts from the start of the storm.")
        d.TBL(["Place"] + pl_cols, [[name] + [wt(W[sid]["places"].get(name)) for sid in pl_cols] for name in PLACES],
              "Arrival of a 0.3 m rise at five places: failures timed from the breach, S3D from the start of the storm.", "places",
              col_w=[2.0] + [0.9] * len(pl_cols), font_sz=FS)
    if fails:
        b = W[fails[0]]["bands_h"]; hdr = ["Scenario"] + [f"within {hm(x)}" for x in b[:7]] + ["Total"]
        rows = []
        for sid in fails:
            w = W[sid]; rows.append([f"{sid}, people"] + [n0(v) for v in w["people_cum"][:7]] + [n0(w["people_total"])])
            rows.append([f"{sid}, plots"] + [n0(v) for v in w["plots_cum"][:7]] + [n0(w["plots_total"])])
        d.P("{{t:bands_fail}} counts, for the failures, the people and the plots reached within each time after the breach; the last column "
            "is everyone in the flooded area, whether or not the rise reaches 0.3 m. {{f:warn}} draws the same counts as curves.")
        d.TBL(hdr, rows, "People and plots reached within a given time after the breach (cumulative).", "bands_fail", col_w=[1.4] + [0.8] * 8, font_sz=FS)
    if pmfs:
        b = W[pmfs[0]]["bands_h"]; hdr = ["Scenario"] + [f"within {x:g} h" for x in b[:6]] + ["Total"]
        rows = []
        for sid in pmfs:
            w = W[sid]; rows.append([f"{sid}, people"] + [n0(v) for v in w["people_cum"][:6]] + [n0(w["people_total"])])
            rows.append([f"{sid}, plots"] + [n0(v) for v in w["plots_cum"][:6]] + [n0(w["plots_total"])])
        d.P("{{t:bands_pmf}} does the same for the flood without failure, in hours from the start of the storm.")
        d.TBL(hdr, rows, "People and plots reached within a given time after the start of the storm, no failure (cumulative).", "bands_pmf", col_w=[1.4] + [0.8] * 7, font_sz=FS)
    if os.path.exists(chart("results_people_vs_time.png")):
        d.FIG(chart("results_people_vs_time.png"), "People reached against time: failures from the breach (left), the PMF without failure from the start of the storm (right).", "warn", width_cm=15)
    mx = [sid for sid in ("S1D", "S2D") if sid in W]
    if mx:
        b = W[mx[0]]["bands_h"]; grp = ["H1-H3", "H4", "H5", "H6"]
        hdr = ["Reached within"] + [f"{sid} {g}" for sid in mx for g in grp]
        rows = []
        for i, x in enumerate(b):
            key = str(x); rows.append([hm(x) if i == 0 else f"{hm(b[i - 1])} to {hm(x)}"] + [n0(W[sid]["matrix"][key][g]) for sid in mx for g in grp])
        rows.append(["later"] + [n0(W[sid]["matrix"]["later"][g]) for sid in mx for g in grp])
        while len(rows) > 1 and all(v in ("0", "-") for v in rows[-1][1:]): rows.pop()      # trailing intervals nobody is reached in
        d.P("{{t:matrix}} splits the people reached in each interval by the hazard class they end up in, the two inputs a life-safety "
            "estimate needs: how little warning, and how severe the flood. H4 and worse is unsafe for people on foot.")
        d.TBL(hdr, rows, "People newly reached in each interval after the breach, by final hazard class: sunny-day and flood-day failure.", "matrix",
              col_w=[1.3] + [0.7] * (4 * len(mx)), font_sz=FS)
    for sid in ("S1D", "S2D", "S3D"):
        if os.path.exists(mapfile(sid, "population", "town")):
            d.LANDSCAPE(lambda dd, sid=sid: dd.FIG(mapfile(sid, "population", "town"), f"{sid}: people per 100 m cell (GHS-POP 2025) with the flooded area outlined.", f"map_{sid}_pop", width_cm=22.9, max_h_cm=15.0))
    if os.path.exists(mapfile("S2D", "wave", "town")) and not os.path.exists(mapfile("S2D", "hazard-iso-grey", "town")):
        d.LANDSCAPE(lambda dd: dd.FIG(mapfile("S2D", "wave", "town"), "S2D: arrival of the failure wave over the PMF, the time after the breach at which the water is 0.3 m deeper than without failure.", "map_S2D_wave", width_cm=22.9, max_h_cm=15.0))

    # ============================================================ 9 discussion
    d.H1("Discussion")
    d.H2("What the failure adds to the flood")
    d.P("The flood-day runs are read against the no-failure twins: the difference in depth, arrival time and hazard class is the effect of the dam, "
        "and only that difference belongs to the dam-safety classification. The sunny-day runs stand alone: there is no flood to compare with, and "
        "everything in the flooded area is the dam's doing.")
    d.H2("The training dikes")
    d.P(f"The dikes were designed to pass the {F.DIKE_DESIGN_RP}-year wadi flood. A dam break wave is one to two orders of magnitude larger; the maps "
        "show it overtopping them within minutes. The dike runs and the no-dike runs are both reported so that the design review can judge whether the "
        "dikes change where the water goes, not whether they contain it.")
    d.H2("Limits of the analysis")
    d.BULS([
        "The breach is prescribed, not computed: its width and speed are assumptions bounded by the sensitivity runs.",
        "The terrain of the plain is the 5 m drone survey; buildings are not resolved, so depths in the town are those of an open plain with the town's roughness.",
        "The population grid is a 2025 estimate at 100 m; the plot layer is the flood-risk study layer.",
        f"The sea level is fixed at mean higher high water, {F.SEA_LEVEL:.2f} m a.s.l.; a storm surge coinciding with the PMF was not modelled.",
    ])

    # ============================================================ 10 conclusions
    d.H1("Conclusions and Recommendations")
    items = []
    if s1d: items.append(f"A sunny-day failure of five monoliths releases {n0(s1d.get('volume_through_dam_Mm3'))} Mm³ with a peak of {n0(s1d.get('peak_total_flow_m3s'))} m³/s; "
                         f"the coastal plain is reached within {hm(s1d.get('arrival_h_median'))} and {n0(s1d.get('consequences_par_total'))} people live in the flooded area. "
                         "Warning must therefore come from the dam, before the failure, not from the flood.")
    if s3d: items.append(f"The PMF without failure peaks at {n2(peak_pool(s3d))} m a.s.l. with {n0(s3d.get('peak_total_flow_m3s'))} m³/s over the spillway"
                         + ("; the dam is not overtopped." if (peak_pool(s3d) or 99) < F.PARAPET else "; the parapet is overtopped."))
    if s2d and s3d: items.append(f"A failure at the peak of the PMF raises the peak flow from {n0(s3d.get('peak_total_flow_m3s'))} to {n0(s2d.get('peak_total_flow_m3s'))} m³/s "
                                 f"and the flooded area only from {n1(s3d.get('inundated_area_km2_gt0.3m'))} to {n1(s2d.get('inundated_area_km2_gt0.3m'))} km²; "
                                 f"the plain is already under the PMF, so the dam adds depth and force rather than extent (people in the flooded area "
                                 f"{n0(s3d.get('consequences_par_total'))} against {n0(s2d.get('consequences_par_total'))}).")
    if (w1 := load_w("S1D")): items.append(f"Time, not extent, separates the scenarios: the sunny-day wave reaches {n0(w1['people_cum'][0])} people within 15 minutes of the breach "
                                           f"and {n0(w1['people_cum'][3])} within an hour, while the PMF without failure takes hours to build up. Warning must therefore come from "
                                           "the dam's own monitoring, and the plan should use the arrival bands of chapter 9 as its warning zones.")
    items += ["The emergency action plan should use the hazard maps for evacuation routes and shelters.",
              "The training dikes should not be relied on in the plan: they are overtopped by every failure scenario.",
              "The breach width is the parameter that matters for the peak; the formation time matters for the first quarter hour of warning; "
              "the sensitivity runs bound the results and should be quoted with them."]
    d.BULS(items)

    # ============================================================ references
    d.H1("References", numbered=False)
    d.BULS([
        "Renardet S.A. & Partners (2026). Wadi Majlas Flood Protection Dam, Dam Break Analysis Methodology Report, Rev 00.",
        "Renardet S.A. & Partners (2026). Wadi Majlas Hydrology Report.",
        "US Army Corps of Engineers (2024). HEC-RAS 6.6 User's Manual and 2D Modeling User's Manual. Hydrologic Engineering Center, Davis.",
        "FERC (2014). Engineering Guidelines for the Evaluation of Hydropower Projects, Chapter 2, Selecting and Accommodating Inflow Design Floods for Dams.",
        "USACE (2014). Using HEC-RAS for Dam Break Studies, TD-39. Hydrologic Engineering Center.",
        "AIDR (2017). Guideline 7-3: Flood Hazard. Australian Institute for Disaster Resilience.",
        "ICOLD (2020). Bulletin 111, Dam Break Flood Analysis, Review and Recommendations.",
    ])

    # ============================================================ appendices
    d.H1("Appendix A: Run Register", numbered=False)
    d.P("One line per HEC-RAS plan: the scenario it computes, the solver's own completion status, the wall-clock time and the largest Courant number "
        "reached. The base runs had the 32-thread workstation to themselves; from the sensitivity phase on, three runs shared it, so their times are not comparable.")
    def run_time(code, s):
        t = s.get("computation_time", "-") or "-"
        if "*" not in t: return t.strip()
        # HEC-RAS writes '::**' into the HDF summary for long runs; take the dispatcher's END line (minutes) instead
        for line in reversed(open(os.path.join(W2, "04_data", "run_sequence.log"), encoding="utf-8").read().splitlines()):
            m = re.search(rf"END\s+{code}\s+ok=True (\d+) min", line)
            if m: mins = int(m.group(1)); return f"{mins // 60:02d}:{mins % 60:02d}:00"
        return "-"
    rows = []
    for sid in ["Fill", "FillN"] + BASE + SENS:
        s = load(sid) if sid not in ("Fill", "FillN") else None
        code = CODE[sid]
        if sid in ("Fill", "FillN"): rows.append([sid, code, "restart file written", "-", "-"]); continue
        if s is None: rows.append([sid, code, DROPPED.get(sid, "not run: dikes immaterial (chapter 3)" if dropped(sid) else "pending"), "-", "-"]); continue
        rows.append([sid, code, s.get("solution", "-"), run_time(code, s), n2(s.get("max_courant"))])
    d.TBL(["Scenario", "HEC-RAS plan", "Solver status", "Run time", "Max Courant"], rows, "Run register.", "reg", col_w=[1.2, 1.0, 2.2, 1.0, 1.0], font_sz=FS)
    d.H1("Appendix B: Model Files", numbered=False)
    d.P("Where the model, the results and the figures are kept, for whoever picks the study up next.")
    d.BULS([
        "HEC-RAS project 'Majlas' in the study folder: geometries 'Dam Breack' (dikes) and 'Dan Breack - without dikess' (no dikes); flow files u26 to u31; plans p27 to p43 and p48, named after the scenarios.",
        "Results per scenario in W2/04_data/results/<plan>/: summary.json, connection.csv (flow, pool, breach), boundary series, rasters of maximum depth, velocity, depth times velocity, arrival time, duration and AIDR hazard class (2 m, EPSG:32640).",
        "Maps in W2/02_figures/maps/results/, charts in W2/02_figures/charts/, the QGIS project W2/03_maps/Majlas_DamBreak_W2.qgz with the layouts.",
    ])
