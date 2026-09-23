# -*- coding: utf-8 -*-
"""Every figure used in the W1 methodology report, with its source. Read by charts.py and build_report.py.

Sources
  DECK  = Renardet, "Wadi Majlas Dam Design Review & Tender Documents", client presentation, 21 September 2026
          (W:/2525 .../07-DRAWINGS/07-Presentations/20260921-Majlas Dam DR and TD/20260921-Majlas Dam Design.pptx)
  HYD   = Renardet, Wadi Majlas Hydrology Report, Rev 00, July 2026 (D:/.../Majlas/Hydrology/Report)
  DRR   = Renardet, Majlas Dam Design Review Report (W:/2525 .../06-Design Reports/02-Majlas Design Review Report)
  RISK  = Renardet, Techno-Economical Assessment (D:/.../Hydraulic/Flood Protection/Risk)
  RAS   = existing HEC-RAS models (D:/.../Hydraulic/Hydraulic Model/HEC-RAS and .../Flood Protection/Hydraulic)
  HECREF= HEC-RAS 1D Technical Reference, "Estimating breach parameters" (USACE, v6.2 online reference)
"""
BASE = "D:/Mojtaba/Renardet/2224 WS11/Majlas/"
HYPSO_XLSX = BASE + "Hydrology/Report/data/Majlas_Dam_Hypsometric_curves.xlsx"   # HYD, original arch axis; indicative for the straight axis

# ---- reservoir (DECK slide 78) ----
CATCHMENT_KM2 = 571.3
FSL = 84.5              # m a.s.l., full supply level = spillway crest
MWL_TABLE = 96.0        # m a.s.l., "Maximum Water Level" in the DECK characteristics table
PMF_LEVEL = 96.7        # m a.s.l., "PMF 96.70" on the DECK dam section drawing; = parapet top. Used until the team confirms.
VOL_FSL_MM3 = 102.2
VOL_MWL_MM3 = 150.7

# ---- dam (DECK slides 22-27, 78) ----
DAM_TYPE = "Roller-compacted concrete (RCC) gravity dam with grout-enriched RCC facing"
CREST = 95.5            # m a.s.l.
PARAPET = 96.7          # m a.s.l.
CREST_WIDTH = 6.0       # m
CREST_LENGTH = 312.0    # m
HEIGHT_THALWEG = 72.5   # m
HEIGHT_FOUNDATION = 110.5
FOUNDATION_LEVEL = -15.0
BED_AT_DAM = 23.0       # m a.s.l., wadi bed at the axis = crest 95.5 - 72.5 (DECK); stilling basin floor 15.5, end sill about 21
US_SLOPE = "0.05H:1V"
DS_SLOPE = "0.75H:1V"
AXIS_SHIFT_M = 110      # straight axis moved downstream of the original arch axis (DECK slide 22)
N_BLOCKS = 17           # blocks B1 to B17 on the DECK general plan (slide 33); block widths to be supplied

# ---- spillway (DECK slides 32-36, 78) ----
SPILL_TYPE = "Free overflow ogee with stepped chute, ungated"
SPILL_CREST = 84.5
SPILL_NET_LENGTH = 200.0
SPILL_BAYS = 5
SPILL_BAY_WIDTH = 40.0
SPILL_PIERS = 4
SPILL_PIER_THK = 3.0
SPILL_GROSS_LENGTH = 212.0
SPILL_BAY_PITCH = SPILL_BAY_WIDTH + SPILL_PIER_THK   # 43 m, pier centre to pier centre
SPILL_QMAX = 17000.0     # m3/s (DECK table, "Qs-max")
UNIT_Q_DESIGN = 60.7     # m2/s (DECK slide 32)
UNIT_Q_PMF = 85.0
BASIN_TYPE = "USBR Type II"
BASIN_LENGTH = 55.0
BASIN_FLOOR = 15.5
OGEE_C_LOW, OGEE_C_HIGH = 2.0, 2.2   # m^0.5/s, free ogee near design head; 2.0 x 200 x 12.2^1.5 = 17,050 m3/s reproduces the DECK capacity

# ---- bottom outlet (DECK slides 38-41, 78) ----
BO_DIAMETER = 2.8
BO_QMAX = 120.0
BO_INTAKES = (36.0, 44.0)
BO_OUTLET_INVERT = 23.0
BO_GATES = "1.8 x 2.5 m service radial gate, 2.0 x 2.6 m emergency slide gate, 2.8 x 2.8 m bulkhead gate"

# ---- downstream works (DECK slides 74-78) ----
SEA_LEVEL = 0.71        # m a.s.l. = mean higher high water (MHHW) at Qurayyat, ONHO Maritime Book 2024 (Data/Maritime details.xlsx, row 8);
                        # shoreline terrain is higher, so the coast stays a normal-depth outflow
TIDE = dict(station="Qurayyat (Oman LNG reference port)", z0_m=1.89, mean_range_m=1.7,            # chart datum Z0 below mean sea level
            mhhw_cd=2.60, mlhw_cd=2.50, mhlw_cd=1.60, mllw_cd=0.90,                                # m above chart datum
            mhhw_msl=0.71, mlhw_msl=0.61, mhlw_msl=-0.29, mllw_msl=-0.99,                          # m above mean sea level
            source="Oman National Hydrographic Office, Maritime Book 2024")

# ---- the HEC-RAS model as built by the user (read from Majlas.g02.hdf / g03.hdf, u28, u29, p32 on 2026-09-22 19:45)
MODEL = dict(
    area_name="DS Protection", area_km2=59.4, cells_dikes=35652, cells_nodikes=35878,
    cell_size_m=dict(p10=21, median=45, p90=50, max=79), connection_cells_m=(10, 25), breaklines=30, breakline_spacing_m=(20, 25),
    terrain_dikes="Terrain (2).Protection2", terrain_nodikes="Terrain (2)", terrain_base="drone DTM 5 m with the design surfaces",
    manning={"0.06 (plain, land cover default)": 95.8, "0.035 (wadi bed polygon)": 4.2},           # % of the area
    connection=dict(weir_shape="broad crested", coef=2.2, width_m=6.0, max_submergence=0.98, profile="non-overflow crest 96.7 m; ogee 84.5 m from station 60 to 260 (200 m)"),
    breach=dict(center_station=190, width_m=85, bottom_m=23, side_slopes=0, formation_h=0.1, weir_coef=1.66, progression="sine wave"),
    solver=dict(equation="SWE-ELM", theta=1.0, eddy_viscosity=0.3, base_step_s=10, courant=(0.4, 0.9), min_step_s=0.335, max_step_s=42.9,
                output_min=1, mapping_min=5, cores="all 32 logical (wmic missing)"),
    bc=dict(dam_pmf=(18714, 14.5, 549.4), j11_pmf=(2101, 12.4, 28.4), jsouth_pmf=(7231, 13.2, 156.9),        # peak m3/s, time h, volume Mm3
            dam_10k=(14157, 14.7, 278.0), j11_10k=(1711, 11.6, 12.8), jsouth_10k=(6034, 12.4, 81.4),
            rain_pmp_mm=998, rain_pmp_peak_mm_10min=73.9, rain_10k_mm=524, rain_areal_factor=0.76,
            outflow="normal depth, friction slope 0.003, lines 'Outflow Sea' and 'Outflow 2'"),
    fill=dict(q_m3s=2500, hours=10.3, ramp_h=1.0, volume_Mm3=101.7, pool_m=84.51, window_h=48),
)
DIKE_LENGTH_M = 2600
DIKE_DESIGN_RP = 200
DAM_TO_QURAYAT_KM = 2

# ---- design floods at the dam: (label, years, rain mm, peak m3/s, volume Mm3) ----
# rain: DECK slide 7 (Flood-Mapping 24-h depths); peak and volume: HEC-HMS runs 'DA <rp> Res2' of 2026-09-22 (south catchment added),
# read from the DSS files by W2/01_scripts/01_hms_hydrographs.py -> W2/04_data/hms_res2_hydrographs.xlsx
DESIGN_FLOODS = [("5-yr", 5, 55.3, 459.0, 11.1),
                 ("10-yr", 10, 105.5, 1160.3, 24.9),
                 ("25-yr", 25, 137.5, 1858.3, 42.8),
                 ("50-yr", 50, 168.1, 2559.3, 55.4),
                 ("100-yr", 100, 205.4, 3449.9, 71.1),
                 ("200-yr", 200, 251.0, 4562.7, 90.5),
                 ("500-yr", 500, 327.2, 6454.4, 123.1),
                 ("1,000-yr", 1000, 399.9, 8282.6, 154.4),
                 ("2,000-yr", 2000, 488.7, 9599.8, 192.9),
                 ("5,000-yr", 5000, 639.1, 13085.9, 258.0),
                 ("10,000-yr", 10000, 685.1, 14156.5, 278.0),
                 ("PMF", None, 1306.6, 18714.2, 549.4)]

# ---- HEC-RAS boundary hydrograph peaks from the 'DA <rp> Res2' runs (m3/s): (reservoir inflow, J11, Jsouth, reservoir outflow = routing check) ----
RES2_PEAKS = {
    "2-yr": (91.8, 36.2, 102.4, 0.0),
    "5-yr": (459.0, 141.1, 433.8, 0.0),
    "10-yr": (1160.3, 302.3, 953.9, 0.0),
    "25-yr": (1858.3, 338.2, 1150.2, 0.0),
    "50-yr": (2559.3, 429.8, 1467.8, 0.0),
    "100-yr": (3449.9, 540.8, 1853.8, 0.0),
    "200-yr": (4562.7, 675.6, 2323.1, 0.0),
    "500-yr": (6454.4, 898.9, 3101.7, 877.4),
    "1,000-yr": (8282.6, 1110.5, 3839.5, 2227.2),
    "2,000-yr": (9599.8, 1210.9, 4262.7, 4027.4),
    "5,000-yr": (13085.9, 1594.3, 5620.0, 7601.8),
    "10,000-yr": (14156.5, 1711.3, 6034.0, 8741.8),
    "PMF": (18714.2, 2101.3, 7230.9, 17213.8),
}
RES2_TIME_TO_PEAK_H = {"200-yr": 15.42, "10,000-yr": 14.67, "PMF": 14.50}   # reservoir inflow, h from start
SOUTH_CATCHMENT_KM2 = 159   # south catchment joining below the dam (catchment map in the design review deck); confirm from HEC-HMS

HISTORIC = [("Cyclone Gonu, June 2007", 501.0, 6537.6, 265.7), ("Cyclone Phet, June 2010", 264.0, 2035.8, 127.3)]
PMF_TIME_TO_PEAK_H = 14.5   # hours from start of the 48-h storm, DA PMP Res2 run

# ---- existing models and data (RAS, RISK) ----
RAS_VERSIONS = "6.6 (geometry and most plans) and 7.0 (latest plan)"
DS_2D_CELLS = 12680
DS_2D_AREA_KM2 = 15.7
PROPOSED_MODEL_KM2 = 27
FULL_2D_CELLS = 145491       # Quriyat 2D area of the catchment-wide model (g02)
POP_GRID = "GHS-POP 2025, 100 m cells"
LU_PLOTS = {"Residential": 2598, "Commercial": 265, "Industrial": 5, "Agricultural": 1043}
DEPTH_RASTER_RES_M = 2

# ---- breach parameters proposed for the analysis ----
# Guidance for concrete gravity dams (HECREF table of FERC / USACE / NWS values):
#   width usually <= 0.5 x crest length, several monoliths; side slopes vertical; time 0.1-0.5 h (USACE), 0.1-0.3 h (FERC), 0.1-0.2 h (NWS)
BREACH_WIDTH_CASES = [("lower: one spillway bay", SPILL_BAY_PITCH), ("base: two bays", 2 * SPILL_BAY_PITCH),
                      ("three bays", 3 * SPILL_BAY_PITCH), ("upper: half the crest", 0.5 * CREST_LENGTH)]
BREACH_TIME_BASE = 0.1        # h
BREACH_TIME_RANGE = (0.05, 0.3)  # h
BREACH_BOTTOM = BED_AT_DAM    # m a.s.l.
BREACH_SIDE_SLOPE = 0.0       # H:V, vertical
BREACH_WEIR_C = 1.7           # SI; HEC-RAS gravity-dam range 2.6-3.0 (US) = 1.44-1.66 SI; 1.7 used for the hand check (upper bound)
BREACH_WEIR_C_RANGE_SI = (1.44, 1.66)
PIPING_C_RANGE = (0.5, 0.6)   # not used: piping through an RCC body is screened out

# ---- hazard classes (AIDR Guideline 7-3 / Smith, Davey and Cox 2014): (D x V limit m2/s, depth limit m, velocity limit m/s) ----
HAZ = {"H1": (0.3, 0.3, 2.0), "H2": (0.6, 0.5, 2.0), "H3": (0.6, 1.2, 2.0), "H4": (1.0, 2.0, 2.0), "H5": (4.0, 4.0, 4.0)}

# ---- indicative programme (task, start week index, duration weeks) ----
PROGRAMME = [("Data requests answered, axis and joints", 0, 2), ("Terrain merge and land cover", 1, 2),
             ("Reservoir 2D area and dam connection", 2, 2), ("PMF no-failure run and routing check", 3, 1),
             ("Sunny-day and flood-day base runs", 4, 2), ("Sensitivity runs", 5, 2), ("Maps and hazard classes", 6, 2),
             ("Consequences and classification", 7, 2), ("Draft report and internal review", 8, 2), ("Client review and final", 10, 2)]
