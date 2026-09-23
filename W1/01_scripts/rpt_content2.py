# -*- coding: utf-8 -*-
"""Report content, part 2: chapters 7 to 12, references and appendices."""
import math
import data_facts as F
from build_report import mr, mtxt, mfrac, msup, msub, mrad, mdelim

def n(x, dp=0):
    return f"{x:,.{dp}f}"

def part2(d):
    ch7_model(d)
    ch8_maps(d)
    ch9_consequences(d)
    ch10_sensitivity_qa(d)
    ch11_deliverables(d)
    ch12_conclusions(d)
    references(d)
    appendix_a(d)
    appendix_b(d)
    appendix_c(d)
    appendix_d(d)

# ====================================================================== 7 Hydraulic model
def ch7_model(d):
    d.H1("Hydraulic Model")
    d.H2("Software and type of model")
    d.P("The flood wave is computed with HEC-RAS, version 6.6, in two dimensions. The existing models of the scheme are in the same version, the "
        "software is free and documented, and its dam break tools are the ones the international guidance is written around. A 2D model is required "
        "rather than a 1D model[[fn:A 1D model computes one water level and one velocity per cross-section across the whole valley. A 2D model divides "
        "the ground into cells and computes depth and velocity in each, so it can show water spreading over a floodplain, splitting around a town and "
        "returning to the wadi. For a dam break wave entering an open coastal plain, only the 2D model gives usable maps.]] because below the gorge the "
        "wave spreads over a plain several kilometres wide and through a town, and the maps must show where the water goes, not only how high it stands.")
    d.P("The model solves the full shallow water equations[[fn:The shallow water equations are the equations of mass and momentum for water whose "
        "depth is small compared with its extent. HEC-RAS offers a simplified form, the diffusion wave, that ignores the inertia of the water. The "
        "inertia is what carries a dam break wave, so the diffusion wave must not be used for the failure runs.]] in every failure run. The diffusion "
        "wave option is used only to warm up the reservoir before the breach and, if needed, to speed up the no-failure run once it has been checked "
        "against the full equations.")
    d.H2("Layout of the model")
    d.P("The model has two 2D flow areas joined by one connection ({{f:layout}}). The reservoir area covers the valley from the dam to the upstream end "
        f"of the pool at the PMF level, on the 2 m terrain. The downstream area is the existing {F.DS_2D_AREA_KM2} km² area of the flood protection model, "
        "extended to the shoreline and refined near the dam. The connection is the dam: it carries the non-overflow crest, the spillway, the piers "
        "and the breach. Modelling the reservoir as a 2D area rather than as a storage area with a volume curve is the choice recommended for "
        "sudden failures, because it reproduces the drawdown wave that runs up the reservoir and limits the outflow in the first minutes; a storage-area "
        "run is kept as a sensitivity check. The catchment-wide model of the hydrology study is not used, because its 5 m cells and its size make the "
        "failure runs too slow, and the inflow it would provide is already available as hydrographs.")
    d.LANDSCAPE(lambda d: d.FIG("flowcharts/fc3_hecras.png", "Order in which the HEC-RAS 2D dam break model is prepared, built, run and checked.", "layout", width_cm=22.9, max_h_cm=15.5))
    d.H2("Terrain")
    d.P("One terrain is built for the whole model from the sources in {{t:terrain}}, with the more accurate source taking priority where two overlap. "
        "The design surfaces are burnt into the ground so that the dam, the stilling basin, the dikes, the wadi crossings and the reservoir bed are "
        "as designed, not as the survey found them. The dam itself is then cut out of the terrain along the connection, because the connection "
        "represents it. In the no-dikes runs the dike surfaces are left out.")
    d.TBL(["Priority", "Source", "Resolution", "Covers", "Status"], [
        ["1", "Dam-site topographic survey", "5 cm", "Dam site and gorge", "To be supplied by the design team"],
        ["2", "Design surfaces: dam, spillway, stilling basin, bottom outlet chute, dikes, roads, wadi bank cuts", "CAD", "Where designed", "To be supplied as CAD or DTM"],
        ["3", "Drone survey of the dam and reservoir area", "2 m", "Dam and reservoir", "To be supplied"],
        ["4", "NSA DTM of the downstream reach used in the existing model", "5 m", "Downstream 2D area", "In hand"],
        ["5", "NSA national DSM", "2 m / 5 m", "Everything else, including the coast", "In hand"],
    ], "Terrain sources and their priority in the merged terrain.", "terrain", col_w=[0.6, 2.6, 0.8, 1.2, 1.4], font_sz=15)
    d.H2("Land cover and roughness")
    d.P("Roughness[[fn:Roughness is the resistance the ground offers to the flow, expressed by Manning's n. Higher n means slower and deeper water. "
        "It is the parameter with the widest accepted range, so it is always varied in the sensitivity runs.]] is assigned by land-cover class from "
        "the flood-risk study land-use layer and the existing model, with the values in {{t:manning}}. The base values are those of the existing "
        "downstream model where they exist, so that the dam break results can be compared with the flood protection results on the same basis.")
    d.TBL(["Land cover", "Manning's n, base", "Range for sensitivity", "Where"], [
        ["Wadi bed, gravel and cobbles", "0.035", "0.030 to 0.045", "Active channel above and below the dam"],
        ["Floodplain, bare or sparse scrub", "0.040", "0.035 to 0.050", "Plain between the gorge and the town"],
        ["Agriculture and date gardens", "0.080", "0.060 to 0.100", "Plots classed agricultural"],
        ["Residential and commercial blocks", "0.120", "0.080 to 0.200", "Built plots; buildings not cut into the terrain"],
        ["Roads and paved surfaces", "0.018", "0.016 to 0.022", "Coast road, town roads"],
        ["Concrete structures", "0.015", "0.013 to 0.017", "Spillway chute, stilling basin, dikes with riprap 0.035"],
        ["Reservoir bed, rock and gravel", "0.035", "0.030 to 0.045", "Reservoir 2D area"],
        ["Sea and lagoon", "0.025", "0.020 to 0.030", "Shoreline strip"],
    ], "Manning's n by land-cover class.", "manning", col_w=[1.8, 1.0, 1.2, 2.0])
    d.H2("Mesh")
    d.P("The mesh is built from the existing downstream mesh and a new reservoir mesh. Cell size follows the need: small where the flow changes fast, "
        "larger where it is uniform. Breaklines[[fn:A breakline is a line along which the model aligns the faces of its cells, so that a dike, a road "
        "embankment or a wadi bank is represented as a sharp edge instead of a ramp smeared over a cell. Water then stays behind it until it truly overtops.]] "
        "are placed along the dikes, the wadi banks, the road embankments and the coast road. The dam connection line is itself a breakline.")
    d.TBL(["Zone", "Cell size", "Reason"], [
        ["Reservoir, main body", "30 to 50 m", "Uniform, deep water; volume must match the curve within 2 percent"],
        ["Reservoir, last 1 km to the dam", "10 m", "Drawdown wave and approach flow to the breach"],
        ["Dam and stilling basin", "5 m", "Breach outflow, jet and hydraulic jump"],
        ["Gorge and plain to the town", "10 to 15 m", "Wave front and spreading"],
        ["Town and dikes", "10 m, breaklines on all dikes and roads", "Flow around blocks, along streets and over the dikes"],
        ["Coastal strip and sea", "20 to 30 m", "Outflow to the sea"],
    ], "Mesh cell sizes by zone.", "mesh", col_w=[1.6, 1.6, 2.8])
    d.H2("The dam as a 2D connection")
    d.P("The dam is entered as a connection between the two 2D areas[[fn:In HEC-RAS a connection, called an SA/2D area connection, is a line structure "
        "between two areas with a weir profile along it, optional culverts and gates, and a breach. Flow over the weir is computed from the head on "
        "each side at every time step, so the spillway, the crest and the breach all discharge according to the water levels the model computes.]]. "
        f"Its weir profile is the crest of the dam: {F.CREST} m along the non-overflow blocks, {F.SPILL_CREST} m over the five spillway bays, and the "
        "pier tops between them. The ogee bays use the ogee weir option with the design head from the spillway design; the non-overflow crest uses the "
        "broad-crested option. {{t:conn}} lists the entries. The bottom outlet is not entered, because it is closed.")
    d.TBL(["HEC-RAS entry", "Value", "How it is obtained"], [
        ["Connection alignment", "Straight axis, 312 m, from the design drawings", "Design team CAD"],
        ["Weir profile, non-overflow blocks", f"{F.CREST} m a.s.l.", "Crest level; the parapet is not credited"],
        ["Weir profile, spillway bays", f"{F.SPILL_CREST} m over 5 × {F.SPILL_BAY_WIDTH:.0f} m", "Ogee crest level and bay widths"],
        ["Weir profile, piers", f"{F.PARAPET} m over 4 × {F.SPILL_PIER_THK:.0f} m", "Pier tops"],
        ["Weir shape and coefficient, spillway", "Ogee; design head from the spillway design; C about 2.1 to 2.2 m^{0.5}/s", "Spillway design; checked against the rating of Chapter 2"],
        ["Weir shape and coefficient, crest", "Broad crested; 1.44 to 1.66 m^{0.5}/s", "HEC-RAS range for gravity dams"],
        ["Weir width", f"{F.CREST_WIDTH:.0f} m", "Crest width"],
        ["Breach method", "User entered data", "Chapter 6"],
        ["Breach centre station", "Centre of the spillway section", "Chapter 6"],
        ["Final bottom width", f"{2*F.SPILL_BAY_PITCH:.0f} m base; {F.SPILL_BAY_PITCH:.0f} and {0.5*F.CREST_LENGTH:.0f} m in sensitivity", "Chapter 6"],
        ["Final bottom elevation", f"{F.BED_AT_DAM} m a.s.l.", "Chapter 6"],
        ["Side slopes", "0 H:1V", "Chapter 6"],
        ["Breach weir coefficient", f"{F.BREACH_WEIR_C_RANGE_SI[1]} m^{0.5}/s", "Chapter 6"],
        ["Formation time", f"{F.BREACH_TIME_BASE} h base; {F.BREACH_TIME_RANGE[0]} and {F.BREACH_TIME_RANGE[1]} h in sensitivity", "Chapter 6"],
        ["Failure mode", "Overtopping (the option that opens from the top down); piping is not used", "Chapter 6"],
        ["Trigger", "Set time (sunny day); water surface elevation (flood day)", "Chapter 5"],
        ["Breach progression", "Linear", "Chapter 6"],
    ], "Entries for the dam connection in HEC-RAS.", "conn", col_w=[1.6, 2.2, 1.8], font_sz=15)
    d.H2("Boundary conditions")
    d.TBL(["Boundary", "Type", "Sunny day", "Flood day and no failure"], [
        ["Reservoir, upstream end", "Flow hydrograph", "None (steady pool)", "PMF inflow hydrograph from HEC-HMS, 5-minute step"],
        ["Downstream tributaries", "Flow hydrographs at the HEC-HMS junctions below the dam", "None", "Local PMF runoff of the downstream sub-catchments"],
        ["Sea", "Stage hydrograph", "Highest astronomical tide, constant", "Same; mean sea level in sensitivity"],
        ["Open land edges", "Normal depth", "Slope from the terrain", "Same"],
    ], "Boundary conditions of the model.", "bc", col_w=[1.3, 1.5, 1.3, 1.9])
    d.H2("Initial conditions")
    d.P(f"The reservoir starts full. The sunny-day runs set the initial water surface of the reservoir area to {F.FSL} m and hold it for a two-hour "
        "warm-up before the breach, which lets any small waves from the start of the computation die away. The flood-day and no-failure runs start "
        f"at {F.FSL} m with the PMF hydrograph and let the pool rise with the flood; the failure is then triggered by the pool level. The downstream "
        "area starts dry except for the sea. A restart file is written at the end of the warm-up so that the sensitivity runs can start from the same state.")
    d.H2("Computation settings")
    d.P("{{t:comp}} gives the settings. The time step is adaptive and limited by the Courant number[[fn:The Courant number is the distance a wave travels "
        "in one time step divided by the cell size. If it is above 1 the wave crosses more than one cell per step and the solution can become unstable "
        "or lose the peak. HEC-RAS can halve and double the time step to keep it in range.]], so that the model keeps a short step while the wave "
        "front passes and a longer one afterwards:")
    d.EQ(mr("Cr") + mr("=") + mfrac(mr("V") + mr("Δt"), mr("Δx")) + mr("≤") + mr("1"), "courant",
         [("Cr", "Courant number"), ("V", "flow velocity plus wave celerity (m/s)"), ("Δt", "time step (s)"), ("Δx", "cell size in the direction of flow (m)")])
    d.TBL(["Setting", "Value", "Reason"], [
        ["Equation set", "Shallow water equations, Eulerian-Eulerian (SWE-EM)", "Momentum conserving; recommended for rapidly varying flow"],
        ["Time step", "Adaptive; maximum Courant 1.0; halve above, double below 0.5; initial 1 s", "Stability at the wave front"],
        ["Implicit weighting (theta)", "1.0", "Stability for the breach"],
        ["Water surface tolerance", "0.003 m", "Convergence"],
        ["Volume tolerance", "0.003 m", "Convergence"],
        ["Maximum iterations", "20", "Convergence at the breach"],
        ["Turbulence", "Conservative, mixing coefficients default", "Not decisive; noted"],
        ["Hydrograph output interval", "10 s at the dam connection and at reference lines", "Peak capture"],
        ["Mapping output interval", "1 minute for the first two hours after the breach, 5 minutes after", "Arrival time maps"],
        ["Run duration", "Sunny day: warm-up plus 12 h; flood day and no failure: 60 h", "Full passage of the wave to the sea"],
    ], "Computation settings for the failure runs.", "comp", col_w=[1.5, 2.5, 2.0])
    d.H2("Reservoir routing check before the failure runs")
    d.P("The no-failure PMF run is made first and checked against the design. The spillway discharge of the model at the PMF pool must match the "
        f"rating of the spillway design and the capacity of {n(F.SPILL_QMAX)} m³/s within 5 percent, the peak pool must match the routed maximum water "
        "level given by the design team within 0.2 m, and the reservoir volume of the 2D area at full supply level must match the elevation-volume "
        "curve within 2 percent. The rating follows the ogee equation:")
    d.EQ(mr("Q") + mr("=") + mr("C") + mr("L") + msup(mr("H"), mr("1.5")), "ogee",
         [("Q", "spillway discharge (m³/s)"), ("C", f"discharge coefficient of the ogee, {F.OGEE_C_LOW} to {F.OGEE_C_HIGH} m^{0.5}/s near the design head"),
          ("L", f"net crest length, {F.SPILL_NET_LENGTH:.0f} m"), ("H", "head above the crest (m)")])
    d.P("Only when these three checks pass are the failure runs started. Any difference is resolved with the design team, not adjusted in the model.")
    d.H2("Stability and volume checks on every run")
    d.P("Every run is checked for numerical trouble before its results are used. The checks are listed in Chapter 10; the first of them is the volume "
        "balance, which HEC-RAS reports as the volume accounting error:")
    d.EQ(msub(mr("ε"), mr("V")) + mr("=") + mfrac(mdelim(msub(mr("V"), mr("in")) + mr("-") + msub(mr("V"), mr("out")) + mr("-") + mr("ΔS")), msub(mr("V"), mr("in"))) + mr("×") + mr("100"), "volerr",
         [("ε_{V}", "volume error (percent), accepted if below 1"), ("V_{in}", "volume that entered the model"), ("V_{out}", "volume that left through the boundaries"), ("ΔS", "change of volume stored in the model")])

# ====================================================================== 8 Maps and hazard
def ch8_maps(d):
    d.H1("Inundation Maps and Hazard Classification")
    d.H2("Products")
    d.P("Each run produces the rasters in {{t:outputs}} at 2 m resolution, the resolution used in the flood-risk study, so that the two sets of maps "
        "can be overlaid. All are read from the HEC-RAS results in RAS Mapper and exported to the project GIS, where the maps are laid out in the "
        "same template as the other maps of the project (Appendix C).")
    d.TBL(["Product", "Definition", "Use"], [
        ["Maximum depth", "Highest water depth reached in each cell during the run", "Inundation extent, damage"],
        ["Maximum velocity", "Highest velocity reached in each cell", "Hazard, scour"],
        ["Maximum depth × velocity", "Highest value of the product in each cell", "Hazard class, loss of life"],
        ["Arrival time", "Time from the start of the breach to a depth of 0.3 m in the cell", "Warning time, evacuation"],
        ["Time to peak", "Time from the start of the breach to the maximum depth", "Evacuation"],
        ["Duration", "Time during which the depth exceeds 0.3 m", "Recovery, access"],
        ["Hazard class", "AIDR class H1 to H6 from depth and depth × velocity", "Danger to people, vehicles and buildings"],
        ["Incremental depth", "Maximum depth of the failure run minus that of the no-failure run", "Classification; area affected by the dam alone"],
        ["Breach hydrograph", "Outflow through the dam connection against time", "Peak, volume, comparison with the hand check"],
        ["Reference-line hydrographs", "Flow and level at the gorge exit, the town entry, the coast road and the shoreline", "Arrival and peak times at the places that matter"],
    ], "Map and time-series products of each run.", "outputs", col_w=[1.4, 2.8, 1.8])
    d.H2("Hazard classes")
    d.P("The danger of flowing water to people, vehicles and buildings is classified with the six classes of the Australian guideline, which are "
        "defined by depth, velocity and their product ({{f:hazard}}, {{t:haz}}). The same classes were used in the flood-risk study of the scheme, so "
        "the dam break hazard maps can be read against the flood hazard maps already delivered. HEC-RAS computes the classes directly in RAS Mapper.")
    d.EQ(mr("D") + mr("×") + mr("V") + mr("=") + mr("depth") + mr("×") + mr("velocity"), "dv",
         [("D", "depth (m)"), ("V", "velocity (m/s)"), ("D × V", "product (m²/s), the measure of the force on a person or a wall")])
    d.TBL(["Class", "D × V limit (m²/s)", "Depth limit (m)", "Velocity limit (m/s)", "Meaning"], [
        ["H1", f"{F.HAZ['H1'][0]}", f"{F.HAZ['H1'][1]}", f"{F.HAZ['H1'][2]}", "Generally safe for people, vehicles and buildings"],
        ["H2", f"{F.HAZ['H2'][0]}", f"{F.HAZ['H2'][1]}", f"{F.HAZ['H2'][2]}", "Unsafe for small vehicles"],
        ["H3", f"{F.HAZ['H3'][0]}", f"{F.HAZ['H3'][1]}", f"{F.HAZ['H3'][2]}", "Unsafe for vehicles, children and the elderly"],
        ["H4", f"{F.HAZ['H4'][0]}", f"{F.HAZ['H4'][1]}", f"{F.HAZ['H4'][2]}", "Unsafe for people and vehicles"],
        ["H5", f"{F.HAZ['H5'][0]}", f"{F.HAZ['H5'][1]}", f"{F.HAZ['H5'][2]}", "Unsafe for people and vehicles; buildings vulnerable to structural damage"],
        ["H6", "above 4.0", "-", "-", "Unsafe for everything; buildings fail"],
    ], "Flood hazard classes H1 to H6 (AIDR Guideline 7-3, 2017; Smith, Davey and Cox, 2014). A cell takes the highest class that any of the three limits gives.", "haz", col_w=[0.6, 1.0, 0.9, 1.0, 2.5])
    d.FIG("charts/chart_hazard_classes.png", "Flood hazard classes H1 to H6 in the depth-velocity plane.", "hazard", width_cm=15.0)
    d.H2("Map series")
    d.P("For each of the six base runs a general map of the whole reach at 1:60,000 and a map series of the town at 1:10,000 are produced for maximum "
        "depth, hazard class and arrival time, together with an incremental depth map for the flood-day run. Sensitivity runs are reported by their "
        "breach hydrographs and by summary maps of the envelope of the maximum depth. The maps carry the scenario, the run identifier, the breach "
        "parameters and the date of the model in their information box, so that a map can never be separated from the assumptions behind it.")
    d.H2("Incremental maps")
    d.P("The incremental depth map is the flood-day result minus the no-failure result, cell by cell. Where the increment is below 0.6 m the dam failure "
        "adds little to the flood that would have occurred anyway; the 0.6 m threshold is the value the FEMA guidance uses to decide whether a failure "
        "changes the hazard to people at a location. The area above the threshold is the area for which the dam, rather than the flood, is responsible, "
        "and it is the area the classification looks at.")

# ====================================================================== 9 Consequences
def ch9_consequences(d):
    d.H1("Consequences and Dam Classification")
    d.P("The maps say where the water goes. This chapter turns them into numbers that the Client can act on: how many people are in the way, how many "
        "might not survive, what the damage is, and what category the dam falls into ({{f:conseq}}).")
    d.LANDSCAPE(lambda d: d.FIG("flowcharts/fc4_consequence.png", "From the model results to people at risk, loss of life, damage and the dam category.", "conseq", width_cm=22.9, max_h_cm=15.5))
    d.H2("Population at risk")
    d.P("The population at risk of a run is the number of people inside its inundation extent. It is counted by overlaying the 2025 GHS-POP grid, "
        "which gives residents per 100 m cell, on the maximum depth raster, and summing the cells with a depth above 0.3 m. The count is made for the "
        "whole extent and for each hazard class, and separately for the incremental area of the flood-day run. The grid gives night-time residents; "
        "a daytime count, with schools, markets and the coast road traffic, will be made where the land-use layer identifies such uses, and both are reported.")
    d.H2("Loss of life")
    d.P("Loss of life is estimated with the Reclamation Consequence Estimating Methodology (USBR, 2015), the current empirical method used by the "
        "United States federal agencies. It assigns a fatality rate to each part of the population at risk from two things: how severe the flood is "
        "where those people are, measured by depth times velocity, and how much warning they had. The rate is read from the RCEM curves, which were "
        "fitted to sixty historical dam failures and floods, and multiplied by the people exposed:")
    d.EQ(mr("LOL") + mr("=") + mr("Σ") + msub(mr("PAR"), mr("i")) + mr("×") + msub(mr("f"), mr("i")), "lol",
         [("LOL", "estimated loss of life"), ("PAR_{i}", "population at risk in zone i"), ("f_{i}", "fatality rate for the flood severity and warning time of zone i (RCEM curves, 2015)")])
    d.P("The warning time is the time between the moment people are told to leave and the arrival of the water. It depends on when the failure is "
        "noticed, how long the authorities take to issue the warning, and the arrival time from the maps. {{t:warn}} gives the cases analysed. The "
        "sunny-day case is run with no warning, because a sudden failure gives none unless a warning system exists, and with the warning an early "
        "warning system would give; the difference is the benefit of that system, which the Client needs to decide its specification.")
    d.TBL(["Case", "Scenario", "Warning assumed", "Basis"], [
        ["W0", "Sunny day", "None: people learn of the flood when they see it", "Sudden failure, no monitoring"],
        ["W1", "Sunny day", "15 minutes at the town entry", "Dam instrumentation alarm relayed by an early warning system"],
        ["W2", "Flood day", "One hour", "The PMF is a known cyclone event; the dam is watched and the town is already on alert"],
        ["W3", "Flood day", "Three hours", "Early warning system and an evacuation order issued during the storm"],
    ], "Warning-time cases for the loss-of-life estimate.", "warn", col_w=[0.5, 1.0, 2.2, 2.3])
    d.H2("Economic damage")
    d.P("Direct damage to buildings and plots is computed with the depth-damage curves and the land-use classes of the flood-risk study of the scheme, "
        "applied to the maximum depth of each run. This keeps the dam break damage on the same basis as the flood damage already reported, so that "
        "the two can be compared. Damage to the dam itself, to the dikes and to roads and utilities is listed but not valued, because the values "
        "belong to the emergency planning rather than to the classification.")
    d.H2("Critical infrastructure and services")
    d.P("The inundation extent of each run is intersected with the roads, the wadi crossings, the coast road, the power lines, the water and sewer "
        "networks, the schools, the health facilities and the mosques identified in the land-use and infrastructure layers, and the result is a list "
        "with the depth, the hazard class and the arrival time at each. The list is the input the emergency action plan needs to name shelters and routes.")
    d.H2("Incremental consequences")
    d.P("For the flood-day scenario the consequences are reported twice: in total and as the increment over the no-failure run.")
    d.EQ(mr("ΔC") + mr("=") + msub(mr("C"), mr("failure")) + mr("-") + msub(mr("C"), mr("no failure")), "incr",
         [("ΔC", "incremental consequence, for people at risk, loss of life or damage"), ("C_{failure}", "consequence of the flood-day run"), ("C_{no failure}", "consequence of the PMF passing the dam intact")])
    d.P("The sunny-day consequences are incremental by definition, because without the failure there is no flood.")
    d.H2("Consequence category and hazard class of the dam")
    d.P("The dam is classified in two systems, because the Client's counterparts use both. The ANCOLD guideline (2012) combines the population at risk "
        "with the severity of damage and loss into seven categories from Low to Extreme ({{t:ancold}}). The FEMA hazard potential classification has "
        "three classes, and a dam whose failure would probably cause loss of life is High. The classification is made on the sunny-day and the "
        "incremental flood-day results, and the higher of the two governs.")
    d.TBL(["Population at risk", "Severity: Minor", "Severity: Medium", "Severity: Major", "Severity: Catastrophic"], [
        ["Less than 1", "Very Low", "Low", "Significant", "High C"],
        ["1 to 10", "Significant (Low if less than 5)", "Significant", "High C", "High B"],
        ["10 to 100", "High C", "High C", "High B", "High A"],
        ["100 to 1,000", "High B", "High B", "High A", "Extreme"],
        ["More than 1,000", "High A", "High A", "Extreme", "Extreme"],
    ], "Consequence categories for dams (ANCOLD, 2012). Severity of damage and loss is assessed on the infrastructure, business, community and environmental effects.", "ancold", col_w=[1.3, 1.2, 1.2, 1.2, 1.3], font_sz=15)
    d.H2("Inputs to the emergency plan and the warning system")
    d.P("The analysis report will hand to the emergency action plan: the arrival-time maps and the times at the named places; the evacuation routes "
        "that stay dry or in class H1 for the longest; the shelters outside the H4 and higher areas; and the difference in loss of life between the "
        "warning cases, which is the case for the early warning system and sets the reaction time it must achieve.")

# ====================================================================== 10 Sensitivity and QA
def ch10_sensitivity_qa(d):
    d.H1("Sensitivity, Uncertainty and Quality Checks")
    d.H2("What is varied and why")
    d.P("The breach parameters are the least certain input of the study, followed by the roughness and the sea level. Rather than take a single "
        "conservative value for each, which piles conservatism on conservatism and hides how much each one matters, the base case is run with the best "
        "estimates and each parameter is then varied on its own ({{t:sens}}). Each sensitivity run changes one thing from the base run it is compared with.")
    d.TBL(["Parameter", "Base", "Low", "High", "Runs", "What it tests"], [
        ["Breach width", f"{2*F.SPILL_BAY_PITCH:.0f} m", f"{F.SPILL_BAY_PITCH:.0f} m", f"{3*F.SPILL_BAY_PITCH:.0f} and {0.5*F.CREST_LENGTH:.0f} m", "S1-D, S2-D", "Peak outflow and extent"],
        ["Formation time", f"{F.BREACH_TIME_BASE} h", f"{F.BREACH_TIME_RANGE[1]} h", f"{F.BREACH_TIME_RANGE[0]} h", "S1-D, S2-D", "Peak and arrival time"],
        ["Breach weir coefficient", f"{F.BREACH_WEIR_C_RANGE_SI[1]}", f"{F.BREACH_WEIR_C_RANGE_SI[0]}", "-", "S1-D", "Peak"],
        ["Roughness", "Table values", "Low end of range", "High end of range", "S1-D, S2-D", "Depth, velocity, arrival time in the town"],
        ["Mesh size", "Chapter 7", "-", "Halved in the town and at the dam", "S1-D", "Numerical convergence"],
        ["Sea level", "Highest astronomical tide", "Mean sea level", "-", "S2-D", "Levels in the coastal part of the town"],
        ["Starting pool, sunny day", f"{F.FSL} m", "Bottom outlet intake plus 10 m", "-", "S1-D", "Reservoir level at the time of a failure"],
        ["Failure timing, flood day", "At the pool of " + str(F.PMF_LEVEL) + " m", "-", "2 h after the peak", "S2-D", "Coincidence of breach and flood"],
        ["Inflow flood, flood day", "PMF", "10,000-year", "-", "S2-D", "Choice of the design flood"],
        ["Reservoir representation", "2D area", "Storage area with the volume curve", "-", "S1-D", "Drawdown effect on the peak"],
        ["Parapet wall", "Not credited", "Credited to 96.7 m", "-", "S3-D", "Overflow of the crest during the PMF"],
        ["Dikes", "In place / removed", "-", "-", "All", "Already part of the base runs"],
    ], "Sensitivity runs.", "sens", col_w=[1.3, 1.0, 1.0, 1.2, 0.8, 1.5], font_sz=15)
    d.H2("How the uncertainty is reported")
    d.P("Each result is reported as its base value with the range from the sensitivity runs: the peak outflow, the arrival time at the town entry, "
        "the maximum depth at named places, the population at risk and the loss of life. The maps of the base case are the deliverable maps; the "
        "envelope of the maximum depth over all runs is given as one additional map, so that the emergency plan can see the worst extent without "
        "the base maps being made pessimistic.")
    d.H2("Quality checks")
    d.P("Every run passes the checks of {{t:qa}} before its results are used. A run that fails a check is corrected and rerun; the check log is delivered with the analysis report.")
    d.TBL(["Check", "Criterion", "When"], [
        ["Reservoir volume", "2D area volume at FSL within 2 percent of the elevation-volume curve", "Once, before the runs"],
        ["Spillway rating", "Model discharge at the PMF pool within 5 percent of the design rating", "No-failure run"],
        ["Routed pool", "Peak pool within 0.2 m of the design team's routed level", "No-failure run"],
        ["Volume balance", "Volume accounting error below 1 percent", "Every run"],
        ["Stability", "No oscillation of the breach hydrograph; no cells with iteration warnings at the peak; smooth arrival-time map", "Every run"],
        ["Time step", "Courant number at the wave front at or below 1; result unchanged when the maximum Courant is halved", "Base runs"],
        ["Mesh", "Peak depth at the town entry changes by less than 5 percent when the mesh is halved", "S1-D"],
        ["Peak outflow", "Between the Ritter and the weir hand estimates of Chapter 6, or the difference explained", "Every failure run"],
        ["Continuity to the sea", "All water reaches the sea boundary or is stored on land; no water lost at the open edges", "Every run"],
        ["Consequence counts", "Population and plot counts reproduced by an independent overlay in QGIS", "Every base run"],
        ["Documentation", "Plan, geometry and unsteady file names, parameters and dates recorded in the run register", "Every run"],
    ], "Quality checks applied to every model run.", "qa", col_w=[1.2, 3.4, 1.4])
    d.H2("Review")
    d.P("The model set-up and the base runs are reviewed by a senior engineer who did not build the model, against this methodology, before the "
        "sensitivity runs are made. The analysis report records the review and the changes it caused.")

# ====================================================================== 11 Deliverables and programme
def ch11_deliverables(d):
    d.H1("Deliverables, Work Steps and Data Needed")
    d.H2("Deliverables")
    d.TBL(["Deliverable", "Content", "Format"], [
        ["Dam break analysis report", "Method as approved here, model, results of all runs, consequences, classification, recommendations", "Word and PDF, in this report format"],
        ["Map atlas", "General maps and map series of depth, hazard and arrival time for the six base runs, incremental map, envelope map", "PDF, A3, and the QGIS project with all layouts"],
        ["Rasters and vectors", "Maximum depth, velocity, D×V, arrival time, duration, hazard class for every run; inundation extents; reference-line hydrographs", "GeoTIFF and shapefile, EPSG:32640"],
        ["HEC-RAS model", "Project with terrain, geometry, plans and results of every run, and the run register", "HEC-RAS 6.6 project folder"],
        ["Consequence tables", "Population at risk, loss of life, damage and infrastructure lists per run and per warning case", "Excel"],
        ["Emergency planning inputs", "Arrival times at named places, evacuation routes, shelter locations, warning-time benefit", "Chapter of the report and GIS layers"],
        ["Animations", "Depth against time for the sunny-day and flood-day base runs", "MP4"],
    ], "Deliverables of the dam break analysis.", "deliv", col_w=[1.3, 3.0, 1.7])
    d.H2("Work steps and programme")
    d.P("{{f:process}} shows the ten steps of the analysis and {{f:programme}} an indicative programme of about twelve weeks from the approval of this "
        "methodology and receipt of the data, of which the first two weeks depend on the design team.")
    d.LANDSCAPE(lambda d: d.FIG("flowcharts/fc1_process.png", "The ten steps of the dam break analysis.", "process", width_cm=22.9, max_h_cm=15.5))
    d.FIG("charts/chart_programme.png", "Indicative programme of the analysis, in weeks from the approval of this methodology.", "programme", width_cm=15.0)
    d.H2("Data still needed")
    d.P("{{t:datareq}} lists the data that this methodology depends on and that are not yet in hand. Appendix D repeats the list as a register to be "
        "returned by the design team.")
    d.TBL(["Item", "Needed for", "From", "Priority"], [
        ["Monolith joint layout with block widths and stations", "Breach width in whole blocks", "Dam design", "Highest"],
        [f"Routed maximum water level during the PMF ({F.MWL_TABLE} or {F.PMF_LEVEL} m) and the routing calculation", "Flood-day pool, routing check", "Dam design / hydraulics", "Highest"],
        ["Elevation-area-volume table for the straight axis", "Reservoir volume check", "Dam design", "High"],
        ["Design surfaces of dam, spillway, stilling basin, bottom outlet chute, dikes, wadi crossings and roads", "Terrain", "Dam design / roads", "High"],
        ["Dam-site survey (5 cm) and drone DTM (2 m) files", "Terrain", "Survey", "High"],
        ["Spillway rating curve and design head of the ogee", "Dam connection", "Hydraulics", "High"],
        ["Tide levels at Qurayat (highest astronomical tide, mean sea level)", "Sea boundary", "National tide tables", "Medium"],
        ["Infrastructure layers: roads, utilities, schools, health facilities, mosques", "Consequences", "Municipality / project GIS", "Medium"],
        ["Daytime population indicators (schools, markets, workplaces)", "Daytime population at risk", "Municipality", "Medium"],
        ["Foundation and abutment failure mode notes from the dam safety review", "Confirmation of the failure location", "Geotechnics", "Medium"],
    ], "Data needed from the project team before the model is built.", "datareq", col_w=[2.4, 1.5, 1.2, 0.8], font_sz=15)
    d.H2("Decisions requested from the Client")
    d.BULS([
        "Approval of the three scenarios and of the with-and-without-dikes pairing.",
        f"Approval of the breach parameters of Chapter 6, in particular the base width of two spillway bays ({2*F.SPILL_BAY_PITCH:.0f} m) and the formation time of {F.BREACH_TIME_BASE} h.",
        "Confirmation that the parapet wall is not to be credited in the no-failure run.",
        "Confirmation of the warning-time cases of Chapter 9, which decide the benefit shown for the early warning system.",
        "Confirmation that the ANCOLD (2012) and FEMA classifications are the ones to report.",
    ])

# ====================================================================== 12 Conclusions
def ch12_conclusions(d):
    d.H1("Conclusions and Recommendations")
    d.P("The Wadi Majlas dam is a concrete gravity dam, and its dam break analysis must follow the rules for concrete gravity dams: a breach of whole "
        "monoliths with vertical sides, formed in minutes, with the number of failed blocks varied to cover the uncertainty. The regression equations "
        "written for embankment dams, used in earlier studies for the Client, do not apply and would give a slower, smaller flood and a longer warning "
        "time than the dam can justify.")
    d.P("Three scenarios cover what the dam can do: a sunny-day failure at full supply level, a flood-day failure at the peak pool of the probable "
        "maximum flood, and the probable maximum flood passing the dam intact. Each is run with and without the downstream dikes. The flood is "
        "computed in HEC-RAS 2D with the full shallow water equations on a model that runs from the reservoir to the sea, built on the existing "
        "model of the downstream reach. The results are maps of depth, velocity, arrival time and hazard, the population at risk, an estimate of "
        "loss of life for stated warning times, the damage, and the consequence category of the dam.")
    d.P("The Consultant recommends that the Client approves this methodology as the basis of the analysis, and that the design team supplies the four "
        "items on which the model depends: the monolith layout, the routed maximum water level, the reservoir curve for the straight axis, and the "
        "design surfaces. With these in hand the analysis can be completed in about twelve weeks.")
    d.P("Two points deserve the Client's attention now rather than at the end. The parapet wall at 96.7 m is the only thing between the PMF pool and "
        "the crest at 95.5 m; this methodology does not credit it, and the design team may wish to confirm the freeboard basis. And the sunny-day "
        "case with no warning will give the largest loss of life of the study; the difference between it and the case with fifteen minutes of warning "
        "is the strongest argument for the early warning system, and the Client may wish to decide the scope of that system on this evidence.")

# ====================================================================== References
def references(d):
    d.H1("References")
    refs = [
        "Australian Institute for Disaster Resilience (2017). Guideline 7-3: Flood Hazard. Australian Disaster Resilience Handbook Collection, Melbourne.",
        "Australian National Committee on Large Dams (2012). Guidelines on the Consequence Categories for Dams. ANCOLD, October 2012.",
        "Brunner, G.W. (2014). Using HEC-RAS for Dam Break Studies. Training Document TD-39, Hydrologic Engineering Center, US Army Corps of Engineers, Davis, California.",
        "Federal Emergency Management Agency (2013). Federal Guidelines for Inundation Mapping of Flood Risks Associated with Dam Incidents and Failures. FEMA P-946, first edition, July 2013.",
        "Federal Energy Regulatory Commission (1993). Engineering Guidelines for the Evaluation of Hydropower Projects, Chapter 2: Selecting and Accommodating Inflow Design Floods for Dams. FERC, Washington DC.",
        "Froehlich, D.C. (1995). Embankment dam breach parameters revisited. Water Resources Engineering, Proceedings of the 1995 ASCE Conference, 887-891.",
        "Froehlich, D.C. (2008). Embankment dam breach parameters and their uncertainties. Journal of Hydraulic Engineering, 134(12), 1708-1721.",
        "Graham, W.J. (1999). A Procedure for Estimating Loss of Life Caused by Dam Failure. Report DSO-99-06, US Bureau of Reclamation, Denver.",
        "International Commission on Large Dams (1998). Dam-Break Flood Analysis: Review and Recommendations. Bulletin 111, ICOLD, Paris.",
        "MacDonald, T.C. and Langridge-Monopolis, J. (1984). Breaching characteristics of dam failures. Journal of Hydraulic Engineering, 110(5), 567-586.",
        "Renardet S.A. & Partners (2026). Wadi Majlas Flood Protection Dam, Hydrology Report, Rev 00, July 2026. For the Ministry of Agriculture, Fisheries Wealth and Water Resources.",
        "Renardet S.A. & Partners (2026). Majlas Dam Design Review Report. For the Ministry of Agriculture, Fisheries Wealth and Water Resources.",
        "Renardet S.A. & Partners (2026). Wadi Majlas Dam Design Review and Tender Documents, presentation to the Client, 21 September 2026.",
        "Renardet S.A. & Partners (2026). Wadi Majlas Flood Protection Scheme, Techno-Economical Assessment Report (flood hazard, damage and cost-benefit).",
        "Ritter, A. (1892). Die Fortpflanzung der Wasserwellen. Zeitschrift des Vereines Deutscher Ingenieure, 36(33), 947-954.",
        "Smith, G.P., Davey, E.K. and Cox, R.J. (2014). Flood Hazard. Technical Report 2014/07, Water Research Laboratory, University of New South Wales.",
        "US Army Corps of Engineers (2024). HEC-RAS River Analysis System, 1D Hydraulic Reference Manual and 2D Modeling User's Manual, version 6.x. Hydrologic Engineering Center, Davis, California.",
        "US Bureau of Reclamation (2015). RCEM: Reclamation Consequence Estimating Methodology, Guidelines for Estimating Life Loss for Dam Safety Risk Analysis (interim). USBR, Denver.",
        "US Bureau of Reclamation and US Army Corps of Engineers (2019). Best Practices in Dam and Levee Safety Risk Analysis. Chapters on consequences of dam failure and on concrete gravity structures.",
        "Von Thun, J.L. and Gillette, D.R. (1990). Guidance on breach parameters. Unpublished internal document, US Bureau of Reclamation, Denver.",
        "Wahl, T.L. (1998). Prediction of Embankment Dam Breach Parameters: A Literature Review and Needs Assessment. Report DSO-98-004, US Bureau of Reclamation, Denver.",
        "Wahl, T.L. (2004). Uncertainty of predictions of embankment dam breach parameters. Journal of Hydraulic Engineering, 130(5), 389-397.",
        "Xu, Y. and Zhang, L.M. (2009). Breaching parameters for earth and rockfill dams. Journal of Geotechnical and Geoenvironmental Engineering, 135(12), 1957-1970.",
    ]
    for r in refs:
        d.P(r)

# ====================================================================== Appendices
def appendix_a(d):
    d.H1("Appendix A - Embankment Breach Equations, for Reference Only", numbered=False)
    d.P("The equations below are the standard tools for embankment dams. They are reported here so that the reader can see what they would give for "
        "Majlas and why they are not used for a concrete gravity dam (Chapter 6). The values are computed for the sunny-day pool: a volume of "
        f"{F.VOL_FSL_MM3} Mm³ and a height of water above the breach floor of {F.FSL - F.BED_AT_DAM:.1f} m.")
    Vw = F.VOL_FSL_MM3 * 1e6; hb = F.FSL - F.BED_AT_DAM; g = 9.81
    B_p = 0.27 * 1.0 * Vw ** 0.32 * hb ** 0.04; B_o = 0.27 * 1.3 * Vw ** 0.32 * hb ** 0.04
    tf = 63.2 * math.sqrt(Vw / (g * hb ** 2)) / 3600
    d.SUB("Froehlich (2008)")
    d.EQ(msub(mr("B"), mr("avg")) + mr("=") + mr("0.27") + msub(mr("k"), mr("o")) + msup(msub(mr("V"), mr("w")), mr("0.32")) + msup(msub(mr("h"), mr("b")), mr("0.04")), "fro_b",
         [("B_{avg}", "average breach width (m)"), ("k_{o}", "1.3 for overtopping, 1.0 for piping"), ("V_{w}", "volume of water above the breach floor at failure (m³)"), ("h_{b}", "height of the breach (m)")])
    d.EQ(msub(mr("t"), mr("f")) + mr("=") + mr("63.2") + mrad(mfrac(msub(mr("V"), mr("w")), mr("g") + msup(msub(mr("h"), mr("b")), mr("2")))), "fro_t",
         [("t_{f}", "formation time (s)"), ("g", "9.81 m/s²")])
    d.P(f"For Majlas these give an average width of {B_p:,.0f} m (piping) to {B_o:,.0f} m (overtopping) and a formation time of {tf:.2f} hours, with side "
        "slopes of 0.7 (piping) to 1.0 (overtopping) horizontal to vertical. The width is of the same order as the upper case of Chapter 6, but the "
        f"time is about {tf/F.BREACH_TIME_BASE:.0f} times longer than the concrete dam value, which is why the equation would understate the peak.")
    d.SUB("MacDonald and Langridge-Monopolis (1984)")
    Ver = 0.0261 * (Vw * hb) ** 0.769; tf2 = 0.0179 * Ver ** 0.364
    d.EQ(msub(mr("V"), mr("er")) + mr("=") + mr("0.0261") + msup(mdelim(msub(mr("V"), mr("out")) + msub(mr("h"), mr("w"))), mr("0.769")), "mlm_v",
         [("V_{er}", "volume of embankment eroded (m³), earthfill dams"), ("V_{out}", "volume of water released (m³)"), ("h_{w}", "depth of water above the breach floor (m)")])
    d.EQ(msub(mr("t"), mr("f")) + mr("=") + mr("0.0179") + msup(msub(mr("V"), mr("er")), mr("0.364")), "mlm_t", [("t_{f}", "formation time (h)")])
    d.P(f"For Majlas: an eroded volume of about {Ver/1e6:.2f} Mm³ and a formation time of {tf2:.1f} hours. The breach width follows from the eroded volume and the dam section, and has no meaning for a concrete dam.")
    d.SUB("Von Thun and Gillette (1990)")
    Bv = 2.5 * hb + 54.9; tv1 = 0.015 * hb; tv2 = 0.020 * hb + 0.25
    d.EQ(mr("B") + mr("=") + mr("2.5") + msub(mr("h"), mr("w")) + mr("+") + msub(mr("C"), mr("b")), "vtg_b",
         [("B", "average breach width (m)"), ("h_{w}", "depth of water above the breach floor (m)"), ("C_{b}", "54.9 m for reservoirs larger than 12.3 Mm³")])
    d.P(f"With a formation time of 0.015 h_w for easily eroded material and 0.020 h_w + 0.25 for erosion-resistant material. For Majlas: a width of "
        f"{Bv:,.0f} m and a time of {tv1:.2f} to {tv2:.2f} hours.")
    d.SUB("Xu and Zhang (2009)")
    d.P("Xu and Zhang fitted multiplicative equations to 182 earth and rockfill failures in which the breach width, depth and time depend on the dam "
        "height, the reservoir shape, the dam type (corewall, concrete face, homogeneous), the failure mode and the erodibility of the fill. The "
        "erodibility term dominates the result and cannot be defined for a concrete dam. The equations are not evaluated here.")
    d.TBL(["Equation", "Fitted to", "Width for Majlas (m)", "Time for Majlas (h)", "Applicable to a gravity dam?"], [
        ["Froehlich (2008)", "74 embankment failures", f"{B_p:,.0f} to {B_o:,.0f}", f"{tf:.2f}", "No"],
        ["MacDonald and Langridge-Monopolis (1984)", "42 embankment failures", "From eroded volume", f"{tf2:.1f}", "No"],
        ["Von Thun and Gillette (1990)", "57 embankment failures", f"{Bv:,.0f}", f"{tv1:.2f} to {tv2:.2f}", "No"],
        ["Xu and Zhang (2009)", "182 earth and rockfill failures", "Not evaluated", "Not evaluated", "No"],
        ["Federal guidance for concrete gravity dams (Chapter 6)", "Concrete dam case histories", f"{F.SPILL_BAY_PITCH:.0f} to {0.5*F.CREST_LENGTH:.0f}", f"{F.BREACH_TIME_RANGE[0]} to {F.BREACH_TIME_RANGE[1]}", "Yes"],
    ], "Embankment breach equations evaluated for the Majlas sunny-day pool, against the values adopted.", "appA", col_w=[1.8, 1.3, 1.0, 1.0, 0.9], font_sz=15)

def appendix_b(d):
    d.H1("Appendix B - HEC-RAS Input Sheet", numbered=False)
    d.P("This sheet lists every input the modeller must set in HEC-RAS 6.6 for the base runs, where it is entered, and where its value comes from. "
        "It is the checklist for building the model and for the review of Chapter 10.")
    d.TBL(["Where in HEC-RAS", "Input", "Value or source"], [
        ["RAS Mapper > Terrains", "Merged terrain", "Chapter 7, Table of terrain sources; priority order as listed"],
        ["RAS Mapper > Map Layers > Land Cover", "Land cover layer and Manning's n table", "Chapter 7, Manning's n table"],
        ["Geometry > 2D Flow Areas", "Reservoir area; downstream area; cell sizes; refinement regions; breaklines", "Chapter 7, mesh table"],
        ["Geometry > 2D Flow Areas > Land cover override", "Roughness override where the layer is wrong", "Only with a note in the run register"],
        ["Geometry > SA/2D Area Connections", "Connection along the dam axis; weir profile; weir shape and coefficients; weir width", "Chapter 7, dam connection table"],
        ["Geometry > Reference Lines", "Gorge exit, town entry, coast road, shoreline", "Chapter 8"],
        ["Unsteady Flow > Boundary Conditions", "PMF flow hydrograph at the reservoir; tributary hydrographs; sea stage; normal depth edges", "Chapter 7, boundary condition table; hydrographs from HEC-HMS"],
        ["Unsteady Flow > Initial Conditions", f"Reservoir 2D area initial water surface {F.FSL} m; downstream dry; sea at tide level", "Chapter 7"],
        ["Plan > Breach (plan data)", "Breach method: user entered; centre station; final bottom width; final bottom elevation; side slopes; weir coefficient; formation time; failure mode; trigger; progression", "Chapter 6 table of breach parameters"],
        ["Plan > Computation Options and Tolerances > 2D", "Equation set SWE-EM; theta 1.0; tolerances 0.003 m; iterations 20; turbulence default", "Chapter 7, computation settings"],
        ["Plan > Unsteady Computation Options > Advanced Time Step", "Adaptive on Courant; maximum 1.0; halve above, double below 0.5; initial 1 s", "Chapter 7"],
        ["Plan > Simulation time window", "Sunny day: 2 h warm-up + 12 h; flood day: 60 h", "Chapter 7"],
        ["Plan > Output options", "Hydrograph interval 10 s; mapping interval 1 min then 5 min; detailed output", "Chapter 7"],
        ["Plan > Restart file", "Write at the end of the warm-up; read for sensitivity runs", "Chapter 7"],
        ["RAS Mapper > Results", "Max depth, velocity, D×V, arrival time (0.3 m), duration, hazard (AIDR); export GeoTIFF 2 m", "Chapter 8"],
    ], "HEC-RAS input sheet for the base runs.", "appB", col_w=[1.7, 2.6, 1.7], font_sz=15)

def appendix_c(d):
    d.H1("Appendix C - Map Layout and Symbology", numbered=False)
    d.P("All maps of the analysis use the print layout of the project GIS: A4 landscape at 300 dpi, title and subtitle at the top left, legend at the "
        "left, north arrow and scale bar at the top right, and an information table at the bottom right that carries the run identifier, the scenario, "
        "the breach parameters and the model date. The four maps of this report were produced from that layout and are saved in the QGIS project "
        "of the working folder for reuse. {{t:sym}} fixes the symbology so that every map of the study reads the same way.")
    d.TBL(["Layer", "Symbology"], [
        ["Maximum depth", "Sequential blues in classes 0.3, 0.5, 1.0, 2.0, 4.0, 8.0 m and above; below 0.3 m not shown"],
        ["Hazard class", "H1 to H6 in the six-step blue ramp of the flood-risk study, from light to dark"],
        ["Arrival time", "Classes 0-15, 15-30, 30-60, 60-120, 120-240 minutes and above, from red to yellow to green"],
        ["Velocity", "Sequential oranges in classes 0.5, 1.0, 2.0, 4.0 m/s and above"],
        ["Incremental depth", "Diverging: blue where the failure adds depth above 0.6 m, grey below"],
        ["Dam axis", "Red line, 1.6 mm"],
        ["Dikes", "Orange line, 1.1 mm"],
        ["Land use", "Residential pink, commercial yellow, industrial violet, agricultural green"],
        ["Population grid", "Blue classes 1-5, 5-20, 20-50, 50-100, over 100 persons per cell"],
        ["Base map", "Satellite image; hillshade of the terrain for the reach maps"],
    ], "Symbology of the map series.", "sym", col_w=[1.4, 4.6])

def appendix_d(d):
    d.H1("Appendix D - Data Request Register", numbered=False)
    d.P("The register below is to be returned by the design team with the file names and dates of the items supplied.")
    d.TBL(["No.", "Item", "Format requested", "Needed by", "Supplied (file, date)"], [
        ["1", "Monolith joint layout: stations and widths of blocks B1 to B17", "Drawing or table", "Week 1", ""],
        ["2", f"Routed maximum water level during the PMF and the routing calculation ({F.MWL_TABLE} or {F.PMF_LEVEL} m)", "Table and note", "Week 1", ""],
        ["3", "Elevation-area-volume table for the straight axis", "Excel", "Week 1", ""],
        ["4", "Design surfaces: dam, spillway, stilling basin, bottom outlet chute, dikes, wadi crossings, roads", "DWG or DTM, EPSG:32640", "Week 2", ""],
        ["5", "Dam-site survey (5 cm) and drone DTM (2 m)", "GeoTIFF, EPSG:32640", "Week 2", ""],
        ["6", "Spillway rating curve and ogee design head", "Table", "Week 2", ""],
        ["7", "Tide levels at Qurayat: highest astronomical tide, mean sea level", "Note with source", "Week 3", ""],
        ["8", "Infrastructure layers: roads, utilities, schools, health facilities, mosques", "Shapefile", "Week 4", ""],
        ["9", "Daytime population indicators", "Table or shapefile", "Week 4", ""],
        ["10", "Foundation and abutment failure mode notes", "Note", "Week 3", ""],
    ], "Data request register.", "appD", col_w=[0.4, 2.8, 1.3, 0.8, 1.2], font_sz=15)
