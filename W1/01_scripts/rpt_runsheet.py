# -*- coding: utf-8 -*-
"""HEC-RAS run sheet: the short companion to the methodology report. Values and actions only. Numbers from data_facts.py."""
import data_facts as F

FS = 14   # table font, half-points (7 pt)

def content(d):
    d.H1("HEC-RAS Run Sheet - Wadi Majlas Dam Break Analysis", numbered=False)
    d.P("Companion to the Dam Break Analysis Methodology Report Rev 00 (September 2026). Values only; the reasoning is in Rev 00, chapter given in brackets. "
        f"Units: m, m a.s.l., m³/s, h. Project CRS EPSG:32640. HEC-RAS 6.6, SI units. Levels: wadi bed {F.BED_AT_DAM}, FSL {F.FSL}, crest {F.CREST}, parapet {F.PARAPET}, PMF pool {F.PMF_LEVEL}.")

    # ------------------------------------------------------------ 1 what to write down
    d.H2("What to write down")
    d.TBL(["Run register column", "Entry"], [
        ["Run ID", "S1-D, S1-N, S2-D, S2-N, S3-D, S3-N; sensitivity SW1, SW2, SW3, ST1, ST2, SC1, SN1, SN2, SM1, SS1, SP1, SF1, SI1, SR1, SPW1"],
        ["HEC-RAS files", "Project Majlas_DamBreak.prj; plan = Run ID; geometry G_Dikes or G_NoDikes; unsteady U_S1 (no inflow), U_PMF, U_10000; terrain T_Dikes or T_NoDikes"],
        ["Inputs", "Start pool; inflow file; breach width, bottom, time, coefficient, trigger; sea level; dikes; mesh version; Manning table version"],
        ["Run", "Date, modeller, HEC-RAS version, run time, restart file used"],
        ["Checks", "Volume error %; max Courant; cells with iteration warnings; peak within hand-check bounds (Y/N); reviewer initials"],
    ], "Run register.", "reg", col_w=[1.2, 4.8], font_sz=FS)
    d.TBL(["Value to record from every run", "Where"], [
        ["Breach peak outflow and its time; breach volume", "Connection hydrograph (10 s output)"],
        ["Reservoir level at breach start, at peak outflow, 1 h and 6 h after", "Reservoir 2D area stage at the dam"],
        ["Peak flow, peak level, arrival time (depth 0.3 m), time to peak", "Reference lines: gorge exit, town entry, coast road, shoreline"],
        ["Maximum depth, velocity, D×V at 10 named points in the town", "RAS Mapper point values"],
        ["Inundated area above 0.3 m (km²); people in it; plots in it", "Max depth raster > 0.3 m, overlay GHS-POP and land-use"],
        ["Volume accounting error; max Courant; iteration warnings; run time", "Computation log, HDF summary"],
        ["Exported rasters (2 m GeoTIFF)", "Max depth, max velocity, max D×V, arrival time 0.3 m, duration > 0.3 m, hazard AIDR; incremental depth for S2 (S2 minus S3)"],
    ], "Results to record.", "rec", col_w=[3.0, 3.0], font_sz=FS)

    # ------------------------------------------------------------ 2 model set-up
    d.H2("Model set-up")
    d.TBL(["Step", "Do this", "Value"], [
        ["Terrain", "RAS Mapper > Terrains > New; stack in this order, top has priority", "1 dam-site survey 5 cm; 2 design surfaces (dam, spillway, basin, chute, dikes, crossings, roads); 3 drone DTM 2 m; 4 NSA 5 m (existing DS model); 5 NSA 2 m"],
        ["Two terrains", "Repeat without the dike surfaces", "T_Dikes; T_NoDikes"],
        ["Dam in terrain", "Cut the dam body out along the axis (terrain modification, channel) so the connection alone represents it", "Bed at axis {0} m".format(F.BED_AT_DAM)],
        ["Land cover", "Map Layers > Land Cover from the land-use layer; Manning table", "See table below"],
        ["Reservoir 2D area", "New 2D area from the dam to the upstream end of the {0} m pool plus 200 m margin".format(F.PMF_LEVEL), "Cells 30 to 50 m; 10 m in the last 1 km; check volume at FSL = {0} Mm³ ± 2 %".format(F.VOL_FSL_MM3)],
        ["Downstream 2D area", "Reuse 'DS Protection' from the flood-protection model; extend to the shoreline; add the sea strip", "Cells 10 to 15 m plain; 5 m dam and basin; 10 m town; 20 to 30 m coast"],
        ["Breaklines", "Dikes (both crests), wadi banks, road embankments, coast road, dam axis, basin walls", "Cell size along breakline = zone value; enforce"],
        ["Refinement regions", "Dam and basin 5 m; town 10 m", "-"],
        ["Reference lines", "Gorge exit, town entry, coast road, shoreline", "Named as listed"],
        ["Boundary condition lines", "Reservoir inflow (upstream end); tributary inflows at HEC-HMS junctions J10, J11, J12; sea (stage); open land edges (normal depth)", "-"],
    ], "Geometry.", "geo", col_w=[1.0, 2.8, 2.2], font_sz=FS)
    d.TBL(["Land cover", "n base", "n low", "n high"], [
        ["Wadi bed, gravel", "0.035", "0.030", "0.045"], ["Floodplain, bare or scrub", "0.040", "0.035", "0.050"],
        ["Agriculture, date gardens", "0.080", "0.060", "0.100"], ["Residential and commercial blocks", "0.120", "0.080", "0.200"],
        ["Roads, paved", "0.018", "0.016", "0.022"], ["Concrete (spillway, basin)", "0.015", "0.013", "0.017"],
        ["Riprap on dikes", "0.035", "0.030", "0.040"], ["Reservoir bed", "0.035", "0.030", "0.045"], ["Sea, lagoon", "0.025", "0.020", "0.030"],
    ], "Manning's n.", "man", col_w=[3.0, 1.0, 1.0, 1.0], font_sz=FS)
    d.TBL(["SA/2D connection field", "Entry"], [
        ["Alignment", "Straight dam axis, {0:.0f} m, drawn from the design CAD (indicative shapefile in 04_data/gis until the CAD arrives)".format(F.CREST_LENGTH)],
        ["Weir profile (station, elevation)", "Left non-overflow blocks: {0}; spillway section {1:.0f} m gross: 5 bays × {2:.0f} m at {3} with 4 piers × {4:.0f} m at {5}; right non-overflow blocks: {0}. Block stations from the joint layout when received; until then left 0-50 m, spillway 50-262 m, right 262-312 m".format(F.CREST, F.SPILL_GROSS_LENGTH, F.SPILL_BAY_WIDTH, F.SPILL_CREST, F.SPILL_PIER_THK, F.PARAPET)],
        ["Weir width", "{0:.0f} m".format(F.CREST_WIDTH)],
        ["Weir shape, non-overflow blocks", "Broad crested; coefficient {0} (SI)".format(F.BREACH_WEIR_C_RANGE_SI[1])],
        ["Weir shape, spillway bays", "Ogee; spillway approach height {0:.1f} m; design energy head from the spillway design (request); resulting C about 2.1 to 2.2 (SI)".format(F.SPILL_CREST - F.BED_AT_DAM)],
        ["Culverts, gates", "None (bottom outlet closed)"],
        ["Check", "No-failure run S3-D: discharge at pool {0} m = {1:,.0f} m³/s ± 5 %".format(F.PMF_LEVEL, F.SPILL_QMAX)],
    ], "Dam connection.", "conn", col_w=[1.6, 4.4], font_sz=FS)
    d.TBL(["Plan > Breach (plan data)", "Base", "Lower", "Upper", "Other sensitivity"], [
        ["Breach this structure", "On (S1, S2)", "On", "On", "Off in S3"],
        ["Breach method", "User entered data", "-", "-", "-"],
        ["Center station", "Centre of the spillway section", "-", "-", "-"],
        ["Final bottom width (m)", "{0:.0f}".format(2 * F.SPILL_BAY_PITCH), "{0:.0f}".format(F.SPILL_BAY_PITCH), "{0:.0f}".format(0.5 * F.CREST_LENGTH), "{0:.0f} (three bays)".format(3 * F.SPILL_BAY_PITCH)],
        ["Final bottom elevation (m)", "{0}".format(F.BREACH_BOTTOM), "-", "-", "-"],
        ["Left and right side slopes (H:V)", "0", "0", "0", "-"],
        ["Breach weir coefficient (SI)", "{0}".format(F.BREACH_WEIR_C_RANGE_SI[1]), "{0}".format(F.BREACH_WEIR_C_RANGE_SI[0]), "{0}".format(F.BREACH_WEIR_C_RANGE_SI[1]), "-"],
        ["Full formation time (h)", "{0}".format(F.BREACH_TIME_BASE), "{0}".format(F.BREACH_TIME_RANGE[1]), "{0}".format(F.BREACH_TIME_RANGE[0]), "-"],
        ["Failure mode", "Overtopping", "-", "-", "-"],
        ["Trigger, S1 (sunny day)", "Set time = simulation start + 2 h", "-", "-", "-"],
        ["Trigger, S2 (flood day)", "WS elevation = {0} m".format(F.PMF_LEVEL), "-", "-", "SF1: set time = time of max pool in S3-D + 2 h"],
        ["Breach progression", "Linear", "-", "-", "-"],
    ], "Breach entries.", "br", col_w=[1.7, 1.4, 0.8, 0.9, 1.5], font_sz=FS)

    # ------------------------------------------------------------ 3 scenarios
    d.H2("Scenarios and water levels")
    d.TBL(["Run", "Geometry / terrain", "Reservoir initial WSE (m)", "Inflow BC", "Tributaries J10-J12", "Breach", "Sea stage", "Window"], [
        ["S1-D", "G_Dikes / T_Dikes", "{0}".format(F.FSL), "None", "None", "On; set time +2 h; 86 m; 0.1 h", "HAT, constant", "0 to 14 h; warm-up 2 h; restart written at 2 h"],
        ["S1-N", "G_NoDikes / T_NoDikes", "{0}".format(F.FSL), "None", "None", "Same as S1-D", "HAT", "Same"],
        ["S2-D", "G_Dikes / T_Dikes", "{0}".format(F.FSL), "PMF hydrograph, 5-min, 48 h", "PMF local runoff", "On; WS elev {0} m; 86 m; 0.1 h".format(F.PMF_LEVEL), "HAT", "0 to 60 h"],
        ["S2-N", "G_NoDikes / T_NoDikes", "{0}".format(F.FSL), "PMF", "PMF", "Same as S2-D", "HAT", "0 to 60 h"],
        ["S3-D", "G_Dikes / T_Dikes", "{0}".format(F.FSL), "PMF", "PMF", "Off", "HAT", "0 to 60 h; run first; checks before S1/S2"],
        ["S3-N", "G_NoDikes / T_NoDikes", "{0}".format(F.FSL), "PMF", "PMF", "Off", "HAT", "0 to 60 h"],
    ], "Base runs.", "runs", col_w=[0.5, 1.1, 0.8, 1.0, 0.8, 1.4, 0.6, 1.3], font_sz=FS)
    d.TBL(["Level", "m a.s.l.", "Used as"], [
        ["Wadi bed at the axis; breach bottom", "{0}".format(F.BED_AT_DAM), "Final bottom elevation"],
        ["Bottom outlet intakes", "{0:.0f} and {1:.0f}".format(*F.BO_INTAKES), "Closed; SP1 starts the pool at {0:.0f}".format(F.BO_INTAKES[0] + 10)],
        ["FSL = ogee crest", "{0}".format(F.FSL), "Initial WSE of every run; spillway weir elevation"],
        ["Non-overflow crest", "{0}".format(F.CREST), "Weir elevation of the blocks"],
        ["Parapet top and pier top", "{0}".format(F.PARAPET), "Pier elevation; SPW1 uses it for the blocks too"],
        ["PMF pool (to be confirmed: {0} in the design table)".format(F.MWL_TABLE), "{0}".format(F.PMF_LEVEL), "Breach trigger in S2; check level of S3 ± 0.2 m"],
        ["Sea: highest astronomical tide (HAT)", "from tide tables", "Sea stage, all base runs"],
        ["Sea: mean sea level", "0.0", "SS1"],
        ["Spillway capacity", "{0:,.0f} m³/s".format(F.SPILL_QMAX), "S3-D discharge at the PMF pool ± 5 %"],
    ], "Water levels.", "lev", col_w=[2.6, 1.2, 2.2], font_sz=FS)
    d.TBL(["ID", "Copy of", "Change", "Value"], [
        ["SW1", "S1-D, S2-D", "Final bottom width", "{0:.0f} m".format(F.SPILL_BAY_PITCH)],
        ["SW2", "S1-D, S2-D", "Final bottom width", "{0:.0f} m".format(3 * F.SPILL_BAY_PITCH)],
        ["SW3", "S1-D, S2-D", "Final bottom width", "{0:.0f} m".format(0.5 * F.CREST_LENGTH)],
        ["ST1", "S1-D, S2-D", "Formation time", "{0} h".format(F.BREACH_TIME_RANGE[1])],
        ["ST2", "S1-D, S2-D", "Formation time", "{0} h".format(F.BREACH_TIME_RANGE[0])],
        ["SC1", "S1-D", "Breach weir coefficient", "{0}".format(F.BREACH_WEIR_C_RANGE_SI[0])],
        ["SN1", "S1-D, S2-D", "Manning table", "n low column"],
        ["SN2", "S1-D, S2-D", "Manning table", "n high column"],
        ["SM1", "S1-D", "Mesh", "Half the cell size at the dam and in the town"],
        ["SS1", "S2-D", "Sea stage", "Mean sea level 0.0"],
        ["SP1", "S1-D", "Reservoir initial WSE", "{0:.0f} m".format(F.BO_INTAKES[0] + 10)],
        ["SF1", "S2-D", "Trigger", "Set time = time of max pool in S3-D + 2 h"],
        ["SI1", "S2-D", "Inflow", "10,000-year hydrograph"],
        ["SR1", "S1-D", "Reservoir", "Storage area with the elevation-volume curve instead of the 2D area"],
        ["SPW1", "S3-D", "Weir profile", "Non-overflow blocks at {0} m (parapet credited)".format(F.PARAPET)],
    ], "Sensitivity runs.", "sens", col_w=[0.6, 1.1, 1.6, 2.7], font_sz=FS)

    # ------------------------------------------------------------ 4 computation, outputs, checks
    d.H2("Computation, outputs and checks")
    d.TBL(["Where", "Setting", "Value"], [
        ["Unsteady Flow > Boundary Conditions", "Reservoir BC line", "Flow hydrograph: PMF (S2, S3), 10,000-yr (SI1), none (S1)"],
        ["", "Tributary BC lines J10, J11, J12", "Flow hydrographs from HEC-HMS (PMF local runoff); none in S1"],
        ["", "Sea BC line", "Stage hydrograph, constant HAT (SS1: 0.0)"],
        ["", "Open land edges", "Normal depth, friction slope from the terrain at the edge"],
        ["Unsteady Flow > Initial Conditions", "Reservoir 2D area", "Initial WSE {0} m (SP1: {1:.0f} m); downstream area dry".format(F.FSL, F.BO_INTAKES[0] + 10)],
        ["Plan > Computation Options > 2D", "Equation set", "Shallow Water Equations, Eulerian-Eulerian (SWE-EM)"],
        ["", "Theta (implicit weighting)", "1.0"],
        ["", "Water surface tolerance / volume tolerance", "0.003 m / 0.003 m"],
        ["", "Maximum iterations", "20"],
        ["", "Turbulence", "Conservative, default coefficients"],
        ["Plan > Advanced Time Step", "Time step", "Adaptive on Courant: max 1.0, halve above; min 0.5, double below; initial 1 s"],
        ["Plan > Simulation window", "S1", "0 to 14 h (breach at 2 h)"],
        ["", "S2, S3", "0 to 60 h"],
        ["Plan > Output", "Hydrograph output interval", "10 s"],
        ["", "Mapping output interval", "1 min for 2 h after the breach, then 5 min"],
        ["", "Detailed output; restart file", "On; write restart at 2 h in S1-D and reuse for S1 sensitivity runs"],
        ["RAS Mapper > Results", "Export", "Max depth, max velocity, max D×V, arrival time (0.3 m), duration (> 0.3 m), hazard AIDR; GeoTIFF 2 m, EPSG:32640"],
    ], "Computation and output settings.", "comp", col_w=[1.7, 1.8, 2.5], font_sz=FS)
    d.TBL(["Check", "Pass if", "Run"], [
        ["Reservoir volume", "2D area volume at {0} m within 2 % of the elevation-volume curve".format(F.FSL), "Before any run"],
        ["Spillway rating", "S3-D discharge at the PMF pool within 5 % of {0:,.0f} m³/s".format(F.SPILL_QMAX), "S3-D"],
        ["Routed pool", "S3-D peak pool within 0.2 m of the design team's value", "S3-D"],
        ["Volume error", "Below 1 %", "Every run"],
        ["Stability", "No oscillation in the breach hydrograph; no iteration warnings at the peak; smooth arrival-time map", "Every run"],
        ["Time step", "Result unchanged when max Courant is halved", "S1-D, S2-D"],
        ["Mesh", "Peak depth at the town entry changes less than 5 % in SM1", "SM1"],
        ["Peak outflow", "Between the Ritter and the weir hand values: S1 base 38,000 to 71,000; S2 base 50,000 to 93,000 m³/s, or explained", "Every failure run"],
        ["Water reaches the sea", "No volume lost at open edges; sea outflow plus storage equals inflow plus breach volume", "Every run"],
        ["Counts", "People and plot counts reproduced by an independent QGIS overlay", "Base runs"],
    ], "Checks.", "chk", col_w=[1.2, 3.6, 1.2], font_sz=FS)
