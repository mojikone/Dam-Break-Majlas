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
DIKE_LENGTH_M = 2600
DIKE_DESIGN_RP = 200
DAM_TO_QURAYAT_KM = 2

# ---- design floods at the dam: (label, years, rain mm, peak m3/s, volume Mm3)  (DECK slide 7) ----
DESIGN_FLOODS = [("5-yr", 5, 55.3, 420.6, 11.1), ("10-yr", 10, 105.5, 1123.9, 25.0), ("25-yr", 25, 137.5, 1804.6, 42.8),
                 ("50-yr", 50, 168.1, 2477.3, 55.5), ("100-yr", 100, 205.4, 3321.1, 71.1), ("200-yr", 200, 251.0, 4370.2, 90.5),
                 ("500-yr", 500, 327.2, 6143.0, 123.1), ("1,000-yr", 1000, 399.9, 7856.5, 154.5), ("2,000-yr", 2000, 488.7, 9114.6, 192.9),
                 ("5,000-yr", 5000, 639.1, 12377.7, 258.2), ("10,000-yr", 10000, 685.1, 13375.2, 278.1), ("PMF", None, 1306.6, 18179.1, 549.1)]
HISTORIC = [("Cyclone Gonu, June 2007", 501.0, 6537.6, 265.7), ("Cyclone Phet, June 2010", 264.0, 2035.8, 127.3)]
PMF_TIME_TO_PEAK_H = 14.6   # hours from start of the 48-h storm (HYD hydrograph file, W1/04_data/majlas_inflow_hydrographs.csv)

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
