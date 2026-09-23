# -*- coding: utf-8 -*-
"""Report content, part 1: front matter and chapters 1 to 6. Part 2 (chapters 7 to 12, references, appendices) is in rpt_content2.py.
All numbers come from data_facts.py (F). Inline markup: **bold**, _{sub}, ^{sup}, [[fn: footnote]], {{f:key}} {{t:key}} {{e:key}}.
"""
import data_facts as F
from build_report import mr, mtxt, mfrac, msup, msub, mrad, mdelim
from rpt_content2 import part2

def n(x, dp=0):
    return f"{x:,.{dp}f}"

def content(d):
    front_matter(d)
    ch1_introduction(d)
    ch2_dam_and_setting(d)
    ch3_standards(d)
    ch4_dam_types(d)
    ch5_scenarios(d)
    ch6_breach_parameters(d)
    part2(d)

# ====================================================================== front matter
def front_matter(d):
    d.H1("Abbreviations and Nomenclature", numbered=False)
    d.P("The following abbreviations, symbols and units are used throughout this report.")
    d.TBL(["Term", "Meaning"], [
        ["2D", "Two-dimensional. A model that computes flow depth and velocity over a grid of cells covering the ground, not only along a line."],
        ["AIDR", "Australian Institute for Disaster Resilience, publisher of the flood hazard classes H1 to H6 used in this study."],
        ["ANCOLD", "Australian National Committee on Large Dams, whose 2012 guideline gives the consequence categories for dams."],
        ["D×V", "Depth multiplied by velocity (m²/s), the usual measure of how dangerous flowing water is to people and buildings."],
        ["DTM / DSM", "Digital terrain model (bare ground) / digital surface model (ground plus buildings and trees)."],
        ["EAP", "Emergency action plan: the document that says who does what when the dam is in danger."],
        ["EAV", "Elevation-area-volume relationship of the reservoir."],
        ["EWS", "Early warning system."],
        ["FEMA", "Federal Emergency Management Agency (United States), publisher of the federal dam-safety guidelines."],
        ["FERC", "Federal Energy Regulatory Commission (United States), whose engineering guidelines give breach parameters by dam type."],
        ["FSL", f"Full supply level, {F.FSL} m a.s.l.; the spillway crest level."],
        ["GERCC", "Grout-enriched roller-compacted concrete, the watertight facing of the dam."],
        ["GHS-POP", "Global Human Settlement population grid (European Commission), 100 m cells, 2025 edition."],
        ["HEC-RAS", "River Analysis System of the US Army Corps of Engineers Hydrologic Engineering Center; the hydraulic model used."],
        ["ICOLD", "International Commission on Large Dams."],
        ["IDF", "Inflow design flood: the flood the dam must pass safely; here the PMF."],
        ["LOL", "Loss of life (estimated number of fatalities)."],
        ["MAFWR", "Ministry of Agriculture, Fisheries Wealth and Water Resources, the Client."],
        ["MWL", f"Maximum water level in the reservoir during the inflow design flood ({F.MWL_TABLE} m in the design table, {F.PMF_LEVEL} m on the dam section)."],
        ["NSA", "National Survey Authority of Oman, source of the 2 m and 5 m national terrain models."],
        ["PAR", "Population at risk: the people inside the flooded area."],
        ["PMF / PMP", "Probable maximum flood / probable maximum precipitation."],
        ["RCC", "Roller-compacted concrete."],
        ["RCEM", "Reclamation Consequence Estimating Methodology (US Bureau of Reclamation, 2015) for loss-of-life estimates."],
        ["SWE", "Shallow water equations, the full set of flow equations solved by the 2D model."],
        ["USACE / USBR", "US Army Corps of Engineers / US Bureau of Reclamation."],
        ["m a.s.l.", "Metres above sea level (project datum)."],
        ["Mm³", "Million cubic metres."],
        ["m³/s", "Cubic metres per second."],
    ], "Abbreviations and nomenclature.", "abbr", col_w=[1, 4], font_sz=16)

    d.H1("Executive Summary", numbered=False)
    d.P(f"This report sets out how the dam break analysis of the Wadi Majlas Flood Protection Dam will be carried out. It is a methodology, "
        f"not a result: it fixes the failure scenarios, the breach parameters, the hydraulic model, the maps, the consequence estimates and "
        f"the quality checks before any model is run, so that the Client can approve the basis first and the later results cannot be questioned on method.")
    d.P(f"The dam, as finalised in the design review of September 2026, is a roller-compacted concrete (RCC) gravity dam, {F.HEIGHT_THALWEG} m above the wadi bed and "
        f"{F.CREST_LENGTH:.0f} m long at the crest, with a free ogee spillway {F.SPILL_NET_LENGTH:.0f} m wide on the dam body and a "
        f"{F.VOL_FSL_MM3} Mm³ reservoir at full supply level. Qurayat town starts about {F.DAM_TO_QURAYAT_KM} km downstream.")
    d.P("The single most important decision in this report follows from the dam type. A concrete gravity dam does not fail the way an earth or "
        "rockfill dam fails. An embankment is eroded away by the water over hours, and its breach size and timing are estimated with regression "
        "equations fitted to past embankment failures. A gravity dam fails when one or more of its blocks, called monoliths, slide or overturn "
        "on the foundation. That happens within minutes, the opening has vertical sides, and its width is a whole number of blocks. The regression "
        "equations used in earlier studies of embankment dams in Oman therefore do not apply here, and this methodology replaces them with the "
        "monolith-based approach of the United States federal guidance for concrete dams, with the number of failed blocks varied to cover the uncertainty.")
    d.P("Three scenarios are analysed, each with and without the downstream training dikes: a sunny-day failure with the reservoir at full supply level "
        f"({F.FSL} m) and no flood; a flood-day failure at the peak pool of the probable maximum flood ({F.PMF_LEVEL} m); and the probable maximum "
        "flood passing the dam without failure, which is the baseline needed to separate the damage caused by the dam failing from the damage the "
        "flood would have caused anyway. Sensitivity runs vary the breach width, the breach time, the ground roughness, the mesh size, the sea level and the starting pool.")
    d.P("The flood is simulated in HEC-RAS 2D with the full shallow water equations, on a model that covers the reservoir, the dam and the wadi down to "
        "the Gulf of Oman. The dam is represented as a connection between the reservoir and the downstream area, carrying the crest, the spillway and the "
        "breach. The existing HEC-RAS model of the downstream reach, built for the flood protection design, is reused and extended.")
    d.P("The outputs are maps of maximum depth, velocity, depth times velocity, arrival time and duration, the AIDR hazard classes H1 to H6 already used "
        "in the flood-risk study of the scheme, and for each scenario the population at risk, an estimate of loss of life by the USBR method, and the "
        "economic damage. From these the dam receives a consequence category and a hazard class, and the emergency action plan receives its warning times and evacuation maps.")
    d.P("Four items are needed from the design team before the model is built: the monolith joint layout with block widths, the routed maximum water level "
        f"during the PMF ({F.MWL_TABLE} or {F.PMF_LEVEL} m), the elevation-area-volume table for the straight axis, and the design surfaces of the dam, "
        "stilling basin and dikes. {{t:glance}} summarises the analysis at a glance.")
    d.TBL(["Item", "Decision in this methodology"], [
        ["Dam type and failure model", "RCC gravity dam; failure by sliding of whole monoliths at the foundation; breach with vertical sides formed in about 0.1 h"],
        ["Breach width", f"Base case two spillway bays ({2*F.SPILL_BAY_PITCH:.0f} m); lower case one bay ({F.SPILL_BAY_PITCH:.0f} m); upper case half the crest length ({0.5*F.CREST_LENGTH:.0f} m)"],
        ["Scenarios", f"Sunny day at FSL {F.FSL} m; flood day at the PMF pool {F.PMF_LEVEL} m; PMF without failure (baseline); each with and without the dikes"],
        ["Hydraulic model", "HEC-RAS 2D, version 6.6, full shallow water equations, reservoir and downstream 2D areas joined by the dam connection, sea boundary"],
        ["Terrain", "5 cm dam-site survey, 2 m drone DTM, 5 m NSA DTM and the design surfaces of dam, basin and dikes, merged in that order of priority"],
        ["Map products", "Maximum depth, velocity, D×V, arrival time, duration, AIDR hazard class H1 to H6, incremental depth; 2 m rasters; map series in the project layout"],
        ["Consequences", "Population at risk from GHS-POP 2025; loss of life by USBR RCEM (2015); damage with the flood-risk study curves; incremental over the no-failure case"],
        ["Classification", "ANCOLD (2012) consequence category and FEMA hazard potential class"],
        ["Sensitivity", "Breach width, breach time, roughness, mesh size, sea level, starting pool"],
        ["Quality checks", "Volume balance, hand check of the peak outflow, stability, comparison of the no-failure routing with the design review"],
    ], "The dam break analysis at a glance.", "glance", col_w=[1.2, 3.8])

# ====================================================================== 1 Introduction
def ch1_introduction(d):
    d.H1("Introduction")
    d.H2("Purpose of this report")
    d.P("The Ministry of Agriculture, Fisheries Wealth and Water Resources is building a flood protection dam on Wadi Majlas, upstream of Qurayat in "
        "Muscat Governorate. Renardet S.A. & Partners is the consultant for the design review and supervision. The scope of services includes a dam "
        "break analysis[[fn:A dam break analysis is a study that assumes the dam fails, computes the flood wave that leaves the reservoir, follows it "
        "downstream with a hydraulic model, and reports where the water goes, how deep and fast it is, when it arrives, and who and what is in its path. "
        "It does not say whether the dam will fail; it says what would happen if it did.]] whose results feed the dam classification, the emergency "
        "action plan and the early warning system.")
    d.P("This report is the methodology for that analysis. It is issued before the analysis so that the Client can approve the basis: the scenarios, "
        "the breach parameters, the model, the maps, the consequence method and the checks. Once approved, it becomes the reference for the analysis "
        "report that follows, and any later change to the basis will be recorded against it.")
    d.H2("Why a methodology comes first")
    d.P("Two features of this project make an agreed methodology more important than usual. First, the dam is a concrete gravity dam, while most "
        "dam break studies in the region, and the standard software guidance, are written around embankment dams. The failure mechanism and the "
        "breach parameters are different, and a study that applied embankment rules to a gravity dam would give the wrong size of flood and the wrong "
        "warning times. Second, the dam stands only about 2 km upstream of Qurayat, so the consequences of the choice of parameters are large, and "
        "the parameters must be set and defended in the open rather than left to the modeller.")
    d.H2("What changes from earlier practice")
    d.P("Earlier dam break studies for the Client, such as the Al Dreez dam study of 2025, followed the HEC-RAS guidance for estimating breach "
        "parameters and analysed a sunny-day and a rainy-day scenario for a rockfill dam. That approach is sound for an embankment dam. "
        "{{t:changes}} lists what is kept from that practice and what is changed here, and why.")
    d.TBL(["Item", "Earlier practice (embankment dams)", "This methodology (RCC gravity dam)", "Reason"], [
        ["Breach shape and size", "Trapezoid from regression equations (Froehlich, MacDonald, Von Thun, Xu and Zhang)", "Rectangular opening equal to whole monoliths, vertical sides; width set from the block layout", "Regression equations were fitted to earth and rockfill failures and do not apply to concrete dams"],
        ["Breach time", "0.5 to several hours from the equations", "About 0.1 h (6 minutes), range 0.05 to 0.3 h", "A sliding monolith leaves the dam in minutes; the federal guidance gives 0.1 to 0.5 h for gravity dams"],
        ["Sunny-day cause", "Piping through the embankment", "Sliding of blocks on the foundation, for example after an earthquake or a loss of uplift control", "There is no soil to pipe through an RCC body"],
        ["Flood-day cause", "Overtopping and erosion of the embankment", "Failure of blocks at the highest pool of the PMF, while the spillway is running", "RCC gravity dams tolerate overtopping; the loading on the foundation is what matters"],
        ["Scenarios", "Sunny day and rainy day", "Sunny day, flood day and the PMF without failure; each with and without the dikes", "The no-failure run is needed to compute the incremental effect of the failure, which decides the classification"],
        ["Model", "HEC-RAS 2D", "HEC-RAS 2D, full shallow water equations, reservoir modelled in 2D", "Kept; the reservoir in 2D reproduces the sudden drawdown of an instant breach"],
        ["Consequences", "Inundation and hazard maps", "Maps plus population at risk, loss of life, damage, consequence category", "Required for the classification, the emergency plan and the warning system"],
        ["Sensitivity", "Largest breach width from the equations", "Named runs on width, time, roughness, mesh, sea level, pool", "The uncertainty must be shown, not hidden in one conservative value"],
    ], "What is kept and what changes from the earlier dam break practice.", "changes", col_w=[1.0, 1.6, 1.8, 1.8], font_sz=15)
    d.H2("How to read this report")
    d.P("Chapter 2 describes the dam, the reservoir, the reach downstream and the data in hand. Chapter 3 lists the standards followed and how they rank. "
        "Chapter 4 explains the kinds of dams, how each kind breaks, and which rules apply to Majlas. Chapter 5 defines the failure scenarios and "
        "Chapter 6 the breach parameters. Chapter 7 is the hydraulic model, written as a step-by-step guide for HEC-RAS, and Chapter 8 the maps and "
        "hazard classes. Chapter 9 covers the consequences and the dam classification, Chapter 10 the sensitivity runs and quality checks, Chapter 11 "
        "the deliverables, the work steps and the data still needed, and Chapter 12 the conclusions. Technical terms are explained in footnotes where "
        "they first appear, so that the main text stays readable.")
    d.H2("Scope and limits")
    d.BULS([
        "The analysis assumes the dam fails. It does not assess the probability of failure and it is not a structural or geotechnical check of the design.",
        "The upstream Haifaz dam is not included as a cascade failure. Its catchment is 40 km² against 571 km² for Majlas, and the Majlas reservoir stores the "
        f"whole 200-year flood of {F.DESIGN_FLOODS[5][4]} Mm³ below the spillway crest, so the volume released by a Haifaz failure would be absorbed without raising the Majlas pool to a dangerous level.",
        "The bottom outlet is assumed closed in all scenarios. Its capacity of 120 m³/s is less than one percent of the breach flows and does not change the results.",
        "Results will be presented as depths, velocities, times and counts, with their sensitivity. They are estimates for planning and classification, not predictions of a particular event.",
    ])

# ====================================================================== 2 Dam and setting
def ch2_dam_and_setting(d):
    d.H1("The Dam, the Reservoir and the Reach Downstream")
    d.H2("The scheme")
    d.P(f"Wadi Majlas drains {F.CATCHMENT_KM2} km² of the eastern Hajar mountains and reaches the Gulf of Oman at Qurayat. The flood protection scheme "
        "has three parts: the Majlas dam in the gorge upstream of the town, the smaller Haifaz dam on a side catchment further upstream, and about "
        f"{n(F.DIKE_LENGTH_M)} m of training dikes and bank protection through the town, sized for the 200-year flood. {{f:map1}} shows the catchments, "
        "the reservoir and the reach to the sea.")
    d.LANDSCAPE(lambda d: d.FIG("maps/Map 01 Location and catchments.png", "Wadi Majlas dam: catchments, reservoir and the reach down to Qurayat and the sea.", "map1", width_cm=22.9, max_h_cm=15.5))
    d.H2("The dam as finalised")
    d.P(f"The design review changed the dam from the original curved axis to a straight axis {F.AXIS_SHIFT_M} m further downstream, where the bedrock is "
        f"shallower and of better quality ({{f:axis}}). The dam is a roller-compacted concrete gravity dam with a grout-enriched RCC facing[[fn:Roller-compacted concrete is a dry concrete placed in "
        "thin layers and compacted with rollers, like a road base. It is used for gravity dams because it is fast and economical to place. The grout-enriched "
        "facing is the same concrete made richer in cement mortar at the upstream face so that it is watertight.]], "
        f"{F.HEIGHT_THALWEG} m high above the wadi bed and {F.HEIGHT_FOUNDATION} m above the foundation level of {F.FOUNDATION_LEVEL} m a.s.l. "
        f"The crest is at {F.CREST} m with a parapet to {F.PARAPET} m, {F.CREST_WIDTH:.0f} m wide and {F.CREST_LENGTH:.0f} m long. "
        f"The upstream face is nearly vertical ({F.US_SLOPE}) and the downstream face slopes at {F.DS_SLOPE}. {{t:dam}} lists the characteristics "
        "used in this study, all taken from the design review presentation of 21 September 2026, and {{f:section}} and {{f:plan}} show the section and the general plan.")
    d.TBL(["Characteristic", "Value", "Source"], [
        ["Dam type", F.DAM_TYPE, "Design review"],
        ["Crest level / parapet top", f"{F.CREST} / {F.PARAPET} m a.s.l.", "Design review"],
        ["Crest width / crest length", f"{F.CREST_WIDTH:.0f} m / {F.CREST_LENGTH:.0f} m", "Design review"],
        ["Height above wadi bed / above foundation", f"{F.HEIGHT_THALWEG} m / {F.HEIGHT_FOUNDATION} m", "Design review"],
        ["Foundation level", f"{F.FOUNDATION_LEVEL} m a.s.l.", "Design review"],
        ["Wadi bed at the axis", f"{F.BED_AT_DAM} m a.s.l. (crest minus height above bed)", "Derived"],
        ["Upstream / downstream face", f"{F.US_SLOPE} / {F.DS_SLOPE}", "Design review"],
        ["Blocks (monoliths)", f"{F.N_BLOCKS} blocks B1 to B17 on the general plan; widths to be supplied", "Design review drawing"],
        ["Axis", f"Straight, {F.AXIS_SHIFT_M} m downstream of the original arch axis", "Design review"],
        ["Foundation treatment", "Grout curtain 60 m deep, drainage curtain, consolidation grouting, galleries at three levels", "Design review"],
    ], "Characteristics of the Majlas dam used in this study.", "dam", col_w=[1.6, 2.4, 1.0])
    d.FIG("deck/dam_section_levels.jpg", f"Section through the spillway blocks with the full supply level ({F.FSL} m) and the PMF level ({F.PMF_LEVEL} m) marked (design review, September 2026).", "section", width_cm=15.0)
    d.FIG("deck/dam_general_plan.jpg", "General plan of the dam, spillway, stilling basin and bottom outlet on the straight axis (design review, September 2026).", "plan", width_cm=15.0)
    d.FIG("deck/axis_shift.jpg", f"Original arch axis and the updated straight axis, {F.AXIS_SHIFT_M} m downstream (design review, September 2026).", "axis", width_cm=11.0)
    d.H2("Spillway and bottom outlet")
    d.P(f"The spillway is a free overflow ogee[[fn:An ogee is a spillway crest shaped like the underside of a falling sheet of water, so that the flow "
        f"leaves the crest smoothly. Free overflow means there are no gates: water passes as soon as the reservoir rises above the crest.]] at {F.SPILL_CREST} m, "
        f"on the dam body, with {F.SPILL_BAYS} bays of {F.SPILL_BAY_WIDTH:.0f} m separated by {F.SPILL_PIERS} piers of {F.SPILL_PIER_THK:.0f} m, "
        f"a net length of {F.SPILL_NET_LENGTH:.0f} m and a gross length of {F.SPILL_GROSS_LENGTH:.0f} m. The flow runs down a stepped chute with "
        f"aerators into a USBR Type II stilling basin {F.BASIN_LENGTH:.0f} m long with its floor at {F.BASIN_FLOOR} m ({{f:spillview}}). The design capacity "
        f"is {n(F.SPILL_QMAX)} m³/s. {{f:rating}} shows the rating curve[[fn:The rating curve of a spillway is the relation between the reservoir level "
        f"and the discharge over the crest. For a free ogee it follows Q = C L H^{1.5}, where L is the net length and H the head above the crest.]] that "
        f"reproduces this capacity, which the hydraulic model must match in the no-failure run.")
    d.P(f"The bottom outlet uses the left diversion culvert. A single steel pipe of {F.BO_DIAMETER} m diameter takes water from intakes at "
        f"{F.BO_INTAKES[0]:.0f} and {F.BO_INTAKES[1]:.0f} m through a gate chamber at the downstream toe, and discharges up to {F.BO_QMAX:.0f} m³/s "
        f"onto a trajectory chute into the stilling basin ({{f:bo}}). {{t:spill}} lists the values used.")
    d.TBL(["Characteristic", "Value"], [
        ["Spillway type", F.SPILL_TYPE],
        ["Crest level", f"{F.SPILL_CREST} m a.s.l. (= FSL)"],
        ["Bays / piers", f"{F.SPILL_BAYS} × {F.SPILL_BAY_WIDTH:.0f} m / {F.SPILL_PIERS} × {F.SPILL_PIER_THK:.0f} m"],
        ["Net / gross length", f"{F.SPILL_NET_LENGTH:.0f} m / {F.SPILL_GROSS_LENGTH:.0f} m"],
        ["Design capacity", f"{n(F.SPILL_QMAX)} m³/s"],
        ["Unit discharge, design flood / PMF", f"{F.UNIT_Q_DESIGN} / {F.UNIT_Q_PMF} m²/s"],
        ["Stilling basin", f"{F.BASIN_TYPE}, {F.BASIN_LENGTH:.0f} m long, floor at {F.BASIN_FLOOR} m a.s.l."],
        ["Bottom outlet", f"One steel pipe {F.BO_DIAMETER} m, intakes at {F.BO_INTAKES[0]:.0f} and {F.BO_INTAKES[1]:.0f} m, {F.BO_QMAX:.0f} m³/s"],
        ["Bottom outlet gates", F.BO_GATES],
        ["Diversion (construction)", "Two 6.0 × 6.5 m culverts, cofferdam crest 37.0 m; plugged after construction"],
    ], "Spillway and bottom outlet characteristics used in this study (design review, September 2026).", "spill", col_w=[1.5, 3.5])
    d.FIG("deck/spillway_downstream_view.jpg", "Downstream view of the spillway: five bays, four piers, stepped chute and stilling basin (design review, September 2026).", "spillview", width_cm=15.0)
    d.FIG("deck/bottom_outlet_section.jpg", "Section through the bottom outlet in the left diversion culvert (design review, September 2026).", "bo", width_cm=15.0)
    d.FIG("charts/chart_spillway_rating.png", f"Spillway rating curve for the free ogee, Q = C L H^{1.5} with L = {F.SPILL_NET_LENGTH:.0f} m and C between {F.OGEE_C_LOW} and {F.OGEE_C_HIGH} m^{0.5}/s; the design capacity of {n(F.SPILL_QMAX)} m³/s is reached near the PMF pool.", "rating", width_cm=15.0)
    d.H2("Reservoir")
    d.P(f"At the full supply level of {F.FSL} m the reservoir holds {F.VOL_FSL_MM3} Mm³ and at the maximum water level about {F.VOL_MWL_MM3} Mm³ "
        f"({{f:resplan}}). The elevation-area-volume curves in hand ({{f:eav}}) were derived for the original axis; the straight axis lies {F.AXIS_SHIFT_M} m "
        f"downstream and adds a small volume, so the design team is asked to supply the curve for the final axis. The curve matters twice in this study: "
        "it sets how much water is behind the dam when it fails, and it sets how fast the pool drops while the breach flows. {{t:res}} gives the levels used.")
    d.P(f"Two values are quoted in the design review for the highest pool during the PMF: {F.MWL_TABLE} m in the characteristics table and {F.PMF_LEVEL} m "
        f"on the dam section, which is also the parapet top. This methodology uses {F.PMF_LEVEL} m for the flood-day scenario until the design team "
        f"confirms the routed value. Either way the PMF pool stands about 1.2 m above the non-overflow crest at {F.CREST} m and is held only by the "
        "parapet wall. A parapet is a wave wall, not a retaining element, and international practice does not credit it in dam break work; this "
        "methodology therefore treats the crest as overtopped during the PMF in the no-failure run, and runs a sensitivity case in which the parapet holds.")
    d.TBL(["Level", "Elevation (m a.s.l.)", "Storage (Mm³)", "Use in this study"], [
        ["Wadi bed at the dam", f"{F.BED_AT_DAM}", "0", "Breach bottom"],
        ["Bottom outlet intakes", f"{F.BO_INTAKES[0]:.0f} and {F.BO_INTAKES[1]:.0f}", "-", "Closed in all scenarios"],
        ["Full supply level (spillway crest)", f"{F.FSL}", f"{F.VOL_FSL_MM3}", "Sunny-day pool"],
        ["Dam crest", f"{F.CREST}", "-", "About 1.2 m below the PMF pool; parapet not credited"],
        ["PMF pool (parapet top)", f"{F.PMF_LEVEL}", f"about {F.VOL_MWL_MM3}", "Flood-day pool"],
    ], "Reservoir levels and volumes used in this study.", "res", col_w=[1.8, 1.2, 1.0, 1.6])
    d.FIG("deck/reservoir_plan.jpg", "Reservoir at full supply level (design review, September 2026).", "resplan", width_cm=15.0)
    d.FIG("charts/chart_reservoir_eav.png", f"Reservoir elevation-storage and elevation-area curves (original axis, hydrology report) with the levels used in this study.", "eav", width_cm=15.0)
    d.H2("Design floods")
    d.P(f"The hydrology report and the design review give the inflow floods at the dam ({{t:floods}}, {{f:floods}}). The reservoir stores the whole "
        f"200-year flood of {F.DESIGN_FLOODS[5][4]} Mm³ below the spillway crest. The PMF, with a peak of {n(F.DESIGN_FLOODS[-1][3])} m³/s and a volume of "
        f"{F.DESIGN_FLOODS[-1][4]} Mm³, is the inflow design flood[[fn:The inflow design flood is the largest flood the dam is designed to pass safely. "
        "For a dam whose failure could cause loss of life, international practice takes it as the probable maximum flood, the flood from the largest "
        "rainfall that is physically possible over the catchment.]] and drives the flood-day scenario. {{f:hydrographs}} shows the hydrograph shapes: "
        f"the PMF peaks about {F.PMF_TIME_TO_PEAK_H:.0f} hours into the 48-hour storm, which fixes when the flood-day failure is triggered.")
    d.TBL(["Return period", "24-h rainfall (mm)", "Peak inflow (m³/s)", "Volume (Mm³)"],
          [[r[0], f"{r[2]:.1f}", n(r[3]), f"{r[4]:.1f}"] for r in F.DESIGN_FLOODS] + [[h[0], f"{h[1]:.1f}", n(h[2]), f"{h[3]:.1f}"] for h in F.HISTORIC],
          "Design floods at the Majlas dam and the two largest recorded cyclones (design review, September 2026).", "floods", col_w=[1.4, 1.2, 1.2, 1.0], bold_rows=(5, 11))
    d.FIG("charts/chart_design_floods.png", "Peak inflow and flood volume at the Majlas dam by return period.", "floods", width_cm=15.0)
    d.FIG("charts/chart_inflow_hydrographs.png", "Inflow hydrographs to the Majlas reservoir for the 200-, 1,000- and 10,000-year floods and the PMF (hydrology report).", "hydrographs", width_cm=15.0)
    d.H2("Downstream: Qurayat and the protection works")
    d.P(f"Below the dam the wadi leaves the gorge, crosses about 2 km of open floodplain and enters Qurayat, where it is confined by {n(F.DIKE_LENGTH_M)} m of "
        f"training dikes and bank protection sized for the 200-year flood ({{f:dsworks}}). The town holds {n(F.LU_PLOTS['Residential'])} residential, "
        f"{n(F.LU_PLOTS['Commercial'])} commercial, {n(F.LU_PLOTS['Agricultural'])} agricultural and {F.LU_PLOTS['Industrial']} industrial plots in the "
        "flood-risk study land-use layer, with the coast road, the wadi crossings and the utilities of the town in the path of the wadi. {{f:map4}} shows the plots and the 2025 population grid.")
    d.FIG("deck/downstream_works.jpg", "Downstream protection works: training dikes, bank protection and wadi crossings (design review, September 2026).", "dsworks", width_cm=15.0)
    d.LANDSCAPE(lambda d: d.FIG("maps/Map 04 Population and land use at Qurayat.png", "Qurayat below the dam: use of each plot, the 2025 population grid and the downstream protection works.", "map4", width_cm=22.9, max_h_cm=15.5))
    d.H2("Data in hand")
    d.P("The study starts from a substantial base of data and models produced for the hydrology, the flood protection design and the flood-risk study "
        "({{t:data}}). The existing HEC-RAS 2D model of the downstream reach, with its terrain, land cover and dikes, is the starting point of the "
        "dam break model ({{f:map2}}), and the terrain coverage is shown in {{f:map3}}.")
    d.TBL(["Dataset", "Source and resolution", "Use in this study"], [
        ["National terrain model", "NSA DSM, 2 m and 5 m grids, whole catchment and coast", "Base terrain of the reservoir and downstream areas"],
        ["Dam site survey", "Design review: 2 m DTM of the dam and reservoir, 5 cm at the dam site", "Priority terrain at the dam and the gorge (files to be supplied)"],
        ["Design surfaces", "Design review CAD: dam, spillway, stilling basin, dikes, roads", "Burnt into the terrain (files to be supplied)"],
        ["Existing HEC-RAS models", f"HEC-RAS {F.RAS_VERSIONS}; downstream 2D area of {F.DS_2D_AREA_KM2} km² and {n(F.DS_2D_CELLS)} cells; catchment-wide 2D area of {n(F.FULL_2D_CELLS)} cells", "Downstream mesh, land cover and dikes reused; mesh refined near the dam"],
        ["Design floods and hydrographs", "Hydrology report and HEC-HMS model, 5-minute step", "Inflow to the reservoir for the flood-day and no-failure runs"],
        ["Reservoir curves", "Hydrology report, original axis", "Check of the 2D reservoir volume; to be replaced by the final-axis curve"],
        ["Land use", "Flood-risk study cadastral plots with use class", "Damage and asset counts"],
        ["Population", F.POP_GRID, "Population at risk and loss of life"],
        ["Depth-damage curves", "Flood-risk study, Oman-calibrated JRC functions", "Economic damage"],
        ["Flood hazard method", "AIDR H1 to H6, as in the flood-risk study", "Hazard maps"],
    ], "Data and models available at the start of the analysis.", "data", col_w=[1.3, 2.4, 1.8])
    d.LANDSCAPE(lambda d: (d.FIG("maps/Map 02 Study reach and model extent.png", "Study reach: the existing HEC-RAS 2D area of the downstream reach and the proposed dam break model extent from the reservoir to the sea.", "map2", width_cm=22.9, max_h_cm=15.5),
                           d.PAGEBREAK(),
                           d.FIG("maps/Map 03 Terrain and data coverage.png", "Terrain in hand: hillshade and extent of the NSA 5 m terrain of the existing downstream model; the 2 m national DSM covers the whole area.", "map3", width_cm=22.9, max_h_cm=15.5)))

# ====================================================================== 3 Standards
def ch3_standards(d):
    d.H1("Standards and Guidance Followed")
    d.H2("Position in Oman")
    d.P("The Consultant is not aware of a published Omani standard that prescribes how a dam break analysis is to be carried out. The Client's "
        "requirements therefore rank first, and where they are silent this methodology follows the international guidance listed in {{t:std}}, "
        "in the order given. The choice favours documents that are public, current, and written for regulators rather than for one software.")
    d.H2("Documents and their use")
    d.TBL(["Rank", "Document", "Used for"], [
        ["1", "Client requirements and the scope of services", "Scenarios to report, deliverables, map formats"],
        ["2", "FEMA P-946 (2013), Federal Guidelines for Inundation Mapping of Flood Risks Associated with Dam Incidents and Failures", "Overall procedure, scenarios, map content, incremental approach"],
        ["3", "USACE HEC, Using HEC-RAS for Dam Break Studies, TD-39 (Brunner, 2014) and the HEC-RAS 6.x reference and user manuals", "Model set-up, breach parameters for concrete dams, breach coefficients, checks"],
        ["4", "FERC Engineering Guidelines, Chapter 2 (1993) and USACE guidance as tabulated in the HEC-RAS reference", "Breach width, side slopes and formation time for concrete gravity dams"],
        ["5", "USBR RCEM (2015), Reclamation Consequence Estimating Methodology, and USBR/USACE Best Practices in Dam and Levee Safety Risk Analysis (2019)", "Loss-of-life estimate; failure modes of concrete gravity dams"],
        ["6", "ANCOLD (2012), Guidelines on the Consequence Categories for Dams", "Consequence category of the dam"],
        ["7", "AIDR Guideline 7-3 (2017) and Smith, Davey and Cox (2014)", "Flood hazard classes H1 to H6"],
        ["8", "ICOLD Bulletin 111 (1998), Dam-Break Flood Analysis", "General principles and review of methods"],
        ["9", "Froehlich (2008), Wahl (1998, 2004), Xu and Zhang (2009), Von Thun and Gillette (1990), MacDonald and Langridge-Monopolis (1984)", "Embankment breach equations, reported for reference only"],
    ], "Standards and guidance followed, in order of precedence.", "std", col_w=[0.5, 3.0, 2.0])
    d.H2("What the international practice has in common")
    d.P("The documents differ in detail but agree on five points, and this methodology is built on them.")
    d.BULS([
        "The failure scenarios cover a failure with no flood (sunny day) and a failure during the inflow design flood (flood day), and the design flood is also run without failure so that the effect of the dam failing can be separated from the effect of the flood.",
        "The breach is described by its shape, size and formation time, chosen for the dam type, and the uncertainty in these values is shown by sensitivity runs rather than by a single conservative guess.",
        "The flood wave is routed with an unsteady hydraulic model; for a wide floodplain and a town in the path, a 2D model with the full flow equations.",
        "The results are maps of depth, velocity, arrival time and hazard at a scale useful for emergency planning, plus the population and assets in the flooded area.",
        "The consequences, and in particular the incremental loss of life, decide the hazard or consequence category of the dam, which in turn sets the design flood, the surveillance and the emergency planning requirements.",
    ])

# ====================================================================== 4 Kinds of dams
def ch4_dam_types(d):
    d.H1("Kinds of Dams and How Each One Breaks")
    d.H2("Why the dam type comes first")
    d.P("The size of a dam break flood depends more on how fast the opening forms and how wide it is than on anything else in the analysis. Those two "
        "things are set by what the dam is made of. This chapter describes the main kinds of dams, how each kind fails, and how its breach is "
        "represented in a model, and then states which rules apply to Majlas. {{f:damtypes}} summarises the chapter.")
    d.LANDSCAPE(lambda d: d.FIG("flowcharts/fc2_damtype.png", "How the dam type decides the way the breach is modelled, and the path that applies to the Wadi Majlas dam.", "damtypes", width_cm=22.9, max_h_cm=15.5))
    d.H2("Embankment dams")
    d.P("Earthfill and rockfill dams are built of compacted soil or rock, made watertight by a clay core, a concrete or asphalt face, or a geomembrane. "
        "They fail by erosion. Either water flows over the crest and eats into the downstream face until a channel cuts through (overtopping), or "
        "water finds a path through or under the dam, carries soil with it, and the path grows into a tunnel that collapses (piping)[[fn:Piping is "
        "internal erosion: seepage water washes fine particles out of the soil along a path, the path widens into a pipe, and the material above it "
        "falls in. It is the second most common cause of embankment failure after overtopping.]]. In both cases the opening grows over tens of "
        "minutes to several hours, its sides slope, and its final width depends on the height of the dam and the volume of water behind it. "
        "Because so many embankments have failed, there are statistical relations between the dam and reservoir size and the breach width and time. "
        "These are the regression equations[[fn:A regression equation is a formula fitted to a set of recorded cases so that it reproduces them on "
        "average. Froehlich (2008), for example, fitted 74 embankment failures. Such an equation is only valid for dams like those in the data set.]] "
        "of Froehlich, MacDonald and Langridge-Monopolis, Von Thun and Gillette, and Xu and Zhang, and they are the standard tool for embankment dams. "
        "The earlier Al Dreez study used them correctly for a geomembrane-faced rockfill dam.")
    d.H2("Concrete gravity dams")
    d.P("A concrete gravity dam holds the water back by its own weight. It is built as a row of separate blocks, called monoliths[[fn:A monolith is one "
        "block of the dam between two vertical contraction joints. A concrete dam is cast as a row of such blocks, typically 15 to 25 m wide, so that "
        "the concrete can shrink and move a little without cracking. Waterstops in the joints keep the reservoir water out.]], each standing on the "
        "foundation. Concrete does not erode in the time a flood lasts, so a gravity dam does not breach by erosion and it can be overtopped without "
        "failing, provided the foundation at the toe is not washed out. It fails when the forces on a block exceed what the foundation can hold: "
        "the block slides forward on its base or on a weak layer in the rock, or it overturns. This can be triggered by an earthquake, by excessive "
        "water pressure under the base if the drains are blocked, by a weak seam or fault in the foundation, or by scour at the toe during a large flood. "
        "Once a block moves it leaves the dam almost at once, and its neighbours may follow. The opening is therefore rectangular with vertical sides, "
        "its width is a whole number of monoliths, and it forms in minutes. The United States federal guidance gives a breach width that is usually "
        "not more than half the crest length, vertical sides, and a formation time of 0.1 to 0.5 hour (USACE) or 0.1 to 0.3 hour (FERC). The "
        "regression equations of the previous section do not apply, and the HEC-RAS reference says so explicitly. Roller-compacted concrete dams are "
        "gravity dams in every respect that matters here; the placement method does not change how they fail.")
    d.H2("Concrete arch dams")
    d.P("An arch dam is a thin curved wall that carries the water load sideways into the valley walls. If an abutment gives way the whole arch loses "
        "its support and most or all of the dam goes at once, as at Malpasset in 1959. The guidance therefore takes the breach as 80 to 100 percent of "
        "the crest length, with sides following the valley walls, formed in 0.1 hour or less. The original Majlas design was an arch; had it been kept, "
        "the breach would have been taken as the whole dam.")
    d.H2("Buttress and composite dams")
    d.P("A buttress dam is a sloping slab or a row of arches held up by concrete buttresses. It fails when one or more buttresses fail, and the breach "
        "is the width of the failed buttresses, near instant. Composite dams, with a concrete section in the river and embankment wings, are analysed "
        "section by section: the concrete part with the gravity or arch rules and the wings with the embankment rules, and the worse case governs.")
    d.H2("Summary of the rules by dam type")
    d.TBL(["Dam type", "How it fails", "Breach width", "Side slopes", "Formation time", "Source"], [
        ["Earthfill / rockfill", "Erosion by overtopping or piping", "From regression equations; typically 1 to 5 times the height", "0.5 to 1.4 H:1V", "0.5 to several hours", "Froehlich 2008, Wahl 1998, HEC-RAS reference"],
        ["Concrete gravity (including RCC)", "Monoliths slide or overturn on the foundation", "Whole monoliths; usually not more than 0.5 of the crest length", "Vertical", "0.1 to 0.5 h (USACE), 0.1 to 0.3 h (FERC)", "FERC 1993, USACE 1980 and 2007, HEC-RAS reference"],
        ["Concrete arch", "Abutment or foundation failure; whole arch goes", "0.8 to 1.0 of the crest length", "Valley wall slope", "0.1 h or less", "FERC 1993, USACE, HEC-RAS reference"],
        ["Buttress", "Buttresses fail", "Width of the failed buttresses", "Vertical", "Near instant", "FERC 1993"],
    ], "Breach rules by dam type.", "damtypes", col_w=[1.1, 1.4, 1.5, 0.8, 1.1, 1.3], font_sz=15)
    d.H2("Which rules apply to Majlas")
    d.P(f"The Majlas dam is an RCC gravity dam. The concrete gravity rules apply: the breach is one or more whole monoliths with vertical sides, formed "
        "in about 0.1 hour, and its width is set from the block layout, not from an equation. The grout-enriched facing and the alluvium under the "
        "central blocks do not change the class of the dam; they change which blocks are most likely to move, which is why the failure is placed at "
        "the deepest section. Chapter 6 sets the values.")
    d.H2("Failure modes screened for Majlas")
    d.P("Before choosing scenarios, the ways in which this particular dam could release its reservoir were listed and screened ({{t:modes}}). "
        "The screening decides which physical mechanism each scenario represents; it does not rate the likelihood of any of them.")
    d.TBL(["Mode", "Credible for Majlas?", "Why", "Covered by"], [
        ["Sliding of monoliths on the foundation, normal pool", "Yes", "Deep alluvium and a fault-controlled limestone foundation; an earthquake or a loss of drainage could trigger it", "Sunny-day scenario"],
        ["Sliding or overturning of monoliths at the PMF pool", "Yes", "Highest water load and uplift; the pool stands about 1.2 m above the crest, held by the parapet", "Flood-day scenario"],
        ["Scour of the foundation at the toe during the PMF", "Yes, as a trigger", "Unit discharge of 85 m²/s over the stepped chute; the stilling basin protects the toe but the abutment contact is the weak point", "Flood-day scenario (same breach)"],
        ["Overtopping erosion of the dam body", "No", "RCC does not erode during a flood; gravity dams are overtoppable", "-"],
        ["Piping through the dam body", "No", "There is no soil in the body; the facing is watertight concrete", "-"],
        ["Internal erosion of the alluvium under the cut-off", "As a precursor only", "It would weaken the foundation and lead to sliding, which is the sunny-day case", "Sunny-day scenario"],
        ["Spillway gate failure", "Not applicable", "The spillway is ungated", "-"],
        ["Bottom outlet failure", "No dam failure", "A gate or pipe failure releases at most 120 m³/s", "-"],
        ["Cascade failure of the Haifaz dam", "Excluded", "Small catchment; the Majlas reservoir absorbs the volume below the spillway crest", "-"],
    ], "Failure modes screened for the Majlas dam.", "modes", col_w=[1.5, 0.8, 2.2, 1.0], font_sz=15)

# ====================================================================== 5 Scenarios
def ch5_scenarios(d):
    d.H1("Failure Scenarios and Load Cases")
    d.H2("The three scenarios")
    d.P("Each scenario is a combination of a reservoir level, an inflow and a decision on whether the dam fails. Three are analysed.")
    d.BULS([
        f"**Sunny day (S1).** The reservoir stands at the full supply level of {F.FSL} m with no flood in the wadi[[fn:The sunny-day scenario is the "
        "failure that comes without warning from the weather: on a dry day, for example after an earthquake. It gives the shortest warning time and, "
        "because the wadi downstream is dry, the clearest picture of the flood caused by the dam alone.]]. The dam fails and the reservoir empties through "
        "the breach. This scenario gives the shortest warning time and the flood that is entirely due to the dam.",
        f"**Flood day (S2).** The PMF enters the reservoir, the spillway runs at full capacity, the pool reaches {F.PMF_LEVEL} m and the dam fails at that "
        "moment[[fn:The flood-day scenario, also called the rainy-day or hydrologic scenario, is a failure during the largest flood. The flood wave "
        "from the breach adds to a wadi that is already in flood, so the water levels downstream are the highest of all scenarios.]]. This scenario "
        "gives the highest flood levels downstream.",
        f"**PMF without failure (S3).** The same flood passes the dam through the spillway and over the crest, and the dam holds. This is not a failure "
        "scenario; it is the baseline that shows what the flood would do anyway. The difference between S2 and S3 is the incremental effect of the "
        "failure[[fn:The incremental effect is what the dam failure adds to the flooding that would have happened without it. Dam classification in "
        "FEMA and ANCOLD practice rests on this increment, because a dam is not blamed for a flood it did not cause.]], which decides the classification.",
    ])
    d.H2("Why the flood-day case uses the probable maximum flood")
    d.P(f"The reservoir stores every flood up to the 200-year event below the spillway crest, so smaller floods cannot load the dam beyond its normal "
        f"pool. The PMF is the inflow design flood of a dam whose failure could cause loss of life, and its routed pool of {F.PMF_LEVEL} m gives the "
        "largest water load and the highest starting level for a breach. Running the flood-day case with a smaller flood would understate the consequences "
        "and would not match the design basis of the spillway. The 10,000-year flood will be run as a sensitivity case to show how much of the flood-day "
        "result depends on the choice of the PMF.")
    d.H2("When the dam fails")
    d.P(f"In the sunny-day scenario the failure is triggered by time: the model runs with a steady pool at {F.FSL} m for a warm-up period of about two hours "
        "to let the reservoir settle, and the breach starts at the end of it. In the flood-day scenario the failure is triggered by the pool level: the "
        f"breach starts when the reservoir first reaches {F.PMF_LEVEL} m, which is close to the peak of the inflow. A failure at the exact peak is the "
        "standard assumption because it maximises the outflow; the sensitivity runs include a failure two hours after the peak, when the pool is still "
        "high but the inflow is falling, to show the effect.")
    d.H2("Downstream condition: with and without the dikes")
    d.P("The training dikes through Qurayat are designed for the 200-year flood and will be overwhelmed by a breach wave many times larger. They "
        "still matter: for the first minutes they hold the water in the channel and change where it first spills, and they may fail when overtopped. "
        "Every scenario is run twice, with the dikes in the terrain and without them, and both results are reported. The with-dikes case represents "
        "the scheme as built; the without-dikes case represents the condition before construction and the case of the dikes failing early. The dikes "
        "are not breached in the model; the difference between the two runs brackets the effect.")
    d.H2("Other conditions fixed for all runs")
    d.BULS([
        "The bottom outlet is closed and the groundwater conveyance pipes are ignored; their discharge is negligible against the breach flow.",
        "The downstream boundary at the Gulf of Oman is held at the highest astronomical tide for Qurayat, to be taken from the national tide tables; a mean sea level case is run as a sensitivity.",
        "The wadi downstream is dry at the start of the sunny-day run, and carries the local runoff of the PMF storm in the flood-day and no-failure runs, taken from the HEC-HMS model at the junctions below the dam.",
        "The reservoir is at its design geometry; sedimentation over the life of the dam is not included, because it reduces the stored volume and would reduce the breach flood.",
    ])
    d.H2("The runs")
    d.P("{{t:runs}} lists the six base runs. The sensitivity runs are defined in Chapter 10.")
    d.TBL(["Run", "Scenario", "Starting pool (m a.s.l.)", "Inflow", "Dam", "Dikes", "Purpose"], [
        ["S1-D", "Sunny day", f"{F.FSL}", "None", "Fails at end of warm-up", "In place", "Dam-only flood, shortest warning"],
        ["S1-N", "Sunny day", f"{F.FSL}", "None", "Fails at end of warm-up", "Removed", "Same, before the dikes are built or after they fail"],
        ["S2-D", "Flood day", f"{F.PMF_LEVEL} at failure", "PMF", f"Fails when the pool reaches {F.PMF_LEVEL} m", "In place", "Highest flood levels"],
        ["S2-N", "Flood day", f"{F.PMF_LEVEL} at failure", "PMF", "Same", "Removed", "Same, without the dikes"],
        ["S3-D", "PMF, no failure", "Rises with the flood", "PMF", "Holds; spillway and crest overflow", "In place", "Baseline for the incremental effect; routing check"],
        ["S3-N", "PMF, no failure", "Rises with the flood", "PMF", "Holds", "Removed", "Baseline without the dikes"],
    ], "Base runs of the dam break analysis.", "runs", col_w=[0.6, 0.9, 1.0, 0.6, 1.5, 0.7, 1.7], font_sz=15)

# ====================================================================== 6 Breach parameters
def ch6_breach_parameters(d):
    d.H1("Breach Parameters for the RCC Gravity Dam")
    d.H2("What the model needs")
    d.P("HEC-RAS describes a breach with a short list of numbers. Each is explained below, because the choice of each one is a decision of this methodology "
        "and not a software default.")
    d.BULS([
        "**Location.** The station along the dam axis at which the opening is centred.",
        "**Bottom elevation.** The level of the floor of the opening once it is fully formed.",
        "**Bottom width.** The width of the opening at its floor.",
        "**Side slopes.** The slope of the two sides of the opening, given as horizontal to vertical; zero means vertical sides.",
        "**Formation time.** The time from the start of the opening to its full size[[fn:In HEC-RAS the formation time starts when water begins to leave "
        "through the opening and ends when the opening has reached its full size. It is not the time to empty the reservoir, which the model computes.]].",
        "**Progression.** How the opening grows during the formation time: at a constant rate (linear) or slowly at first and fast in the middle (sine curve).",
        "**Trigger.** What starts the breach: a clock time, a pool elevation, or a pool elevation held for a duration.",
        "**Weir coefficient.** The coefficient in the weir equation that converts the head over the breach floor into a discharge[[fn:Flow through the "
        "breach is computed as flow over a broad-crested weir, Q = C B H^{1.5}, with C the weir coefficient in m^{0.5}/s, B the width and H the head above "
        "the breach floor. HEC-RAS quotes C in US units; the values in this report are converted to metric.]].",
    ])
    d.H2("How each parameter is set for Majlas")
    d.P("**Location.** At the deepest part of the dam, which is the spillway section over the wadi bed. The blocks there carry the highest water load, "
        "stand on the alluvium-filled channel, and their loss releases water from the lowest level. Failure of an abutment block would release less water "
        "from a higher floor and is bounded by the central case.")
    d.P(f"**Bottom elevation.** The wadi bed at the axis, {F.BED_AT_DAM} m a.s.l. The foundation is excavated to {F.FOUNDATION_LEVEL} m, but the failed "
        "blocks slide onto ground that stands at 23 to 30 m, and the stilling basin and rockfill downstream remain in place, so the water cannot leave "
        "below the natural bed. Taking the bed rather than the foundation level is the standard practice and is slightly conservative for the peak, "
        "because a lower floor would drown the outflow in its own tailwater.")
    d.P(f"**Width.** A whole number of blocks. The spillway bays are {F.SPILL_BAY_WIDTH:.0f} m wide between {F.SPILL_PIER_THK:.0f} m piers, so one bay "
        f"with its pier is {F.SPILL_BAY_PITCH:.0f} m. The base case takes two bays, {2*F.SPILL_BAY_PITCH:.0f} m, which is 0.28 of the crest length "
        f"and within the federal ceiling of half the crest. The lower case takes one bay, {F.SPILL_BAY_PITCH:.0f} m, and the upper case half the crest "
        f"length, {0.5*F.CREST_LENGTH:.0f} m, which is the ceiling itself. A three-bay case of {3*F.SPILL_BAY_PITCH:.0f} m is run to show the trend. "
        "When the design team supplies the joint layout the widths will be rounded to the actual blocks.")
    d.P("**Side slopes.** Vertical. The sides of the opening are the contraction joints of the blocks that remain.")
    d.P(f"**Formation time.** {F.BREACH_TIME_BASE} hour, 6 minutes, in the base case, with {F.BREACH_TIME_RANGE[0]} and {F.BREACH_TIME_RANGE[1]} hour as "
        "the sensitivity range. The federal guidance gives 0.1 to 0.5 hour (USACE) and 0.1 to 0.3 hour (FERC) for gravity dams; the short end is used "
        "because a sliding block clears the dam in the time the water needs to push it, and a longer time only lowers the peak.")
    d.P("**Progression.** Linear. The sine curve models the slow start of an erosion breach and is not appropriate for a block that moves as a unit ({{f:progress}}).")
    d.P(f"**Trigger.** Clock time at the end of the warm-up in the sunny-day runs; pool elevation of {F.PMF_LEVEL} m in the flood-day runs.")
    d.P(f"**Weir coefficient.** {F.BREACH_WEIR_C_RANGE_SI[0]} to {F.BREACH_WEIR_C_RANGE_SI[1]} m^{0.5}/s, the HEC-RAS range for concrete gravity dams "
        "(2.6 to 3.0 in US units); the upper value is used in the base case because the opening has a sharp, clean edge.")
    d.P("{{t:breach}} collects the values and {{t:guidance}} the guidance they come from.")
    d.TBL(["Parameter", "Base case", "Lower case", "Upper case", "Basis"], [
        ["Location", "Centre of the spillway section", "Same", "Same", "Deepest blocks, highest load"],
        ["Bottom elevation", f"{F.BED_AT_DAM} m a.s.l.", "Same", "Same", "Wadi bed at the axis"],
        ["Bottom width", f"{2*F.SPILL_BAY_PITCH:.0f} m (two bays)", f"{F.SPILL_BAY_PITCH:.0f} m (one bay)", f"{0.5*F.CREST_LENGTH:.0f} m (half the crest)", "Block layout; federal ceiling of 0.5 L"],
        ["Side slopes", "Vertical (0 H:1V)", "Same", "Same", "Contraction joints"],
        ["Formation time", f"{F.BREACH_TIME_BASE} h", f"{F.BREACH_TIME_RANGE[1]} h", f"{F.BREACH_TIME_RANGE[0]} h", "USACE 0.1 to 0.5 h; FERC 0.1 to 0.3 h"],
        ["Progression", "Linear", "Same", "Same", "Block moves as a unit"],
        ["Trigger, sunny day", "Clock time, end of 2 h warm-up", "Same", "Same", "Steady pool"],
        ["Trigger, flood day", f"Pool at {F.PMF_LEVEL} m", "Same", "Pool at peak, plus a run 2 h after the peak", "Highest load"],
        ["Weir coefficient", f"{F.BREACH_WEIR_C_RANGE_SI[1]} m^{0.5}/s", f"{F.BREACH_WEIR_C_RANGE_SI[0]} m^{0.5}/s", f"{F.BREACH_WEIR_C_RANGE_SI[1]} m^{0.5}/s", "HEC-RAS range for gravity dams"],
    ], "Breach parameters for the Majlas dam.", "breach", col_w=[1.2, 1.4, 1.2, 1.4, 1.6], font_sz=15)
    d.TBL(["Dam type", "Average breach width", "Side slopes", "Failure time (h)", "Agency"], [
        ["Concrete gravity", "Usually not more than 0.5 L, multiple monoliths", "Vertical", "0.1 to 0.5", "USACE 1980 and 2007"],
        ["Concrete gravity", "Usually not more than 0.5 L, multiple monoliths", "Vertical", "0.1 to 0.3", "FERC"],
        ["Concrete gravity", "Usually not more than 0.5 L, multiple monoliths", "Vertical", "0.1 to 0.2", "NWS"],
        ["Concrete arch", "0.8 L to L, or the entire dam", "0 to the valley walls", "0.1 or less", "USACE, FERC, NWS"],
    ], "Federal agency guidance on breach parameters for concrete dams (HEC-RAS 1D Technical Reference, Estimating breach parameters; L = crest length).", "guidance", col_w=[1.0, 2.0, 1.0, 0.9, 1.1], font_sz=15)
    d.FIG("charts/chart_breach_progression.png", f"Growth of the opening during the formation time: linear progression, used here, against the sine progression used for erosion breaches (base case {F.BREACH_TIME_BASE} h).", "progress", width_cm=15.0)
    d.H2("Hand check of the peak outflow")
    d.P("Before any model is run, the order of magnitude of the peak outflow is fixed by two hand calculations, and the model result must fall between "
        "them or be explained. The first is the weir equation applied to the full opening at the starting pool, before the reservoir has dropped:")
    d.EQ(msub(mr("Q"), mr("p")) + mr("=") + mr("C") + mr("B") + msup(mdelim(mr("H") + mr("-") + msub(mr("Z"), mr("b"))), mr("1.5")), "weir",
         [("Q_{p}", "peak outflow through the breach (m³/s)"), ("C", f"weir coefficient, {F.BREACH_WEIR_C} m^{0.5}/s for the check"),
          ("B", "breach width (m)"), ("H", "starting pool level (m a.s.l.)"), ("Z_{b}", f"breach bottom, {F.BED_AT_DAM} m a.s.l.")])
    d.P("The second is the classical solution for the sudden removal of a wall from a reservoir onto a dry bed (Ritter, 1892), which gives a lower value "
        "because it accounts for the drop of the water surface at the opening:")
    d.EQ(msub(mr("Q"), mr("p")) + mr("=") + mfrac(mr("8"), mr("27")) + mr("B") + mrad(mr("g")) + msup(mdelim(mr("H") + mr("-") + msub(mr("Z"), mr("b"))), mr("1.5")), "ritter",
         [("g", "gravity, 9.81 m/s²"), ("B, H, Z_{b}", "as in equation {{e:weir}}")])
    d.P(f"{{f:peakcheck}} shows both for the four widths and the two pools. For the base case of {2*F.SPILL_BAY_PITCH:.0f} m the first-minute peak lies "
        "between about 38,000 and 71,000 m³/s on a sunny day and between 50,000 and 93,000 m³/s on a flood day. These are check values only: the modelled "
        "peak will be lower because the pool drops during the six minutes of formation and the tailwater rises in the stilling basin, and it will be "
        "reported against these bounds in the analysis report.")
    d.FIG("charts/chart_breach_peak_check.png", "Hand check of the peak outflow the moment the breach is fully open, for the four breach widths and the two starting pools; weir equation and Ritter solution.", "peakcheck", width_cm=15.0)
    d.H2("Why the regression equations are not used")
    d.P("The Froehlich, MacDonald, Von Thun and Xu and Zhang equations are reported in Appendix A for completeness, with the values they would give for "
        "Majlas. They are not used, for three reasons. They were fitted to embankment failures, and the HEC-RAS reference states that they do not apply to "
        "concrete dams. They give formation times of one to several hours, which for a concrete dam would understate the peak by a large factor and "
        "overstate the warning time. And their sloping sides have no physical meaning between two contraction joints. Their only use here is to show the "
        "reader how different the answer would have been.")
