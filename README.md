# Wadi Majlas Dam Break Analysis

Dam break analysis of the Wadi Majlas Flood Protection Dam (Wilayat Qurayat, Muscat Governorate, Oman), carried out by Renardet S.A. & Partners within the design review of the dam. The analysis answers three questions for the emergency action plan and the design review: how fast and how far the water goes if the dam fails, who and what is in its way, and how much worse a failure is than the flood the dam is already passing.

This file is the entry point to the repository and is kept up to date whenever something meaningful changes (a result, a decision, a deliverable). Two more live documents carry the detail: [`W2/README.md`](W2/README.md) (what the working folder holds and how to run it) and [`W2/PROJECT_STATE.md`](W2/PROJECT_STATE.md) (every decision, number and open item, dated).

*Last updated: 2026-09-23 07:30. Campaign status: base scenarios complete, six sensitivity runs still computing, interim report 62 pages.*

## The dam in brief

Roller-compacted concrete gravity dam on a straight axis, 2 km upstream of Qurayat: 72.5 m above the wadi bed (110.5 m above the foundation at −15.0 m a.s.l.), crest at 95.5 m a.s.l. with a parapet to 96.7 m, 6 m wide and 312 m long, in 17 monoliths (31.21 m, fifteen of 17.00 m, 25.79 m). Free ogee spillway on the dam body, crest at 84.5 m (the full supply level), five bays of 40 m, 200 m net, designed for 17,000 m³/s, with a stepped chute and a USBR type II stilling basin. Reservoir 102.2 Mm³ at the full supply level. Below the gorge the wadi crosses the coastal plain of Qurayat, where two training dikes designed for the 200-year flood guide it to the sea.

## Logic of the analysis

1. **Failure mode follows the dam type.** A concrete gravity dam does not erode; it fails, if at all, by the sudden sliding of one or more monoliths. The breach is therefore rectangular with vertical sides, its width a whole number of monoliths, and it forms in minutes. The regression equations written for earth dams are not used. Base case: five monoliths, 85 m, in 6 min, weir coefficient 1.66.
2. **Three scenarios, two of them failures.**

   | Scenario | Reservoir at start | Inflow | Failure |
   |---|---|---|---|
   | S1, sunny-day failure | Full supply level, 84.5 m | None | Five monoliths at a set time, two hours into the run |
   | S2, flood-day failure | Full supply level | PMF, with rain on the plain | Five monoliths at the moment the reservoir reaches its maximum level (read from S3) |
   | S3, PMF without failure | Full supply level | PMF, with rain on the plain | None |

   Each was planned with the training dikes in place (D) and without them (N).
3. **Incremental reading.** A flood-day failure is read against its no-failure twin: only what the failure adds to the flood counts against the dam. The sunny-day failure stands alone.
4. **Dikes decision gate.** S1N and S1D were run first; they differ by 0.4 % in flooded area and people at risk, so the flood-day pair without dikes (S3N, S2N) was not run and the with-dikes runs stand for both conditions (`W2/04_data/dikes_decision.json`).
5. **Sensitivity, one parameter at a time.** Breach width 51, 119 and 153 m (three, seven and nine monoliths), formation time 3 and 18 min, weir coefficient 1.44, and the 10,000-year flood instead of the PMF.
6. **Consequences.** Depth, velocity and their product on a 2 m grid, AIDR hazard classes H1–H6, people (GHS-POP 2025) and plots (flood-risk land-use layer) in the flooded area, and, because the hazard maps alone make the PMF look as bad as a failure, **warning time**: who is reached, and when, timed from each scenario's own trigger.

## Models and tools

- **HEC-HMS** basin model "Basin 1 Res2" (21 sub-basins on the 5 m terrain, southern catchment added) gives the PMF and 10,000-year hydrographs at the three boundary lines (reservoir inflow 18,714 m³/s and 549 Mm³ for the PMF; side wadi J11; southern catchment) and the storm that falls on the 2D area (PMP 998 mm, areal reduction factor 0.76).
- **HEC-RAS 6.6, two-dimensional**: one 2D area of 59.4 km² from the reservoir to the sea (35,652 cells with dikes, 35,878 without; 10 m cells along the dam, 25 m beyond, median 45 m), the dam as an SA/2D connection whose profile carries the ogee at 84.5 m and the non-overflow crest at 96.7 m (the parapet is credited), the breach cut into it, shallow-water equations with the Eulerian-Lagrangian scheme, adaptive time step on a Courant number of 0.4–0.9, output every minute. Every run starts from a restart file written by a fill run. Sea level 0.71 m a.s.l. (mean higher high water at Qurayat, ONHO Maritime Book 2024) is an input; the shoreline terrain is higher and the coast is a normal-depth outflow.
- **Automation**: the HEC-RAS controller (COM) drives the plans unattended, three project copies run in parallel, and a dispatcher (`W2/01_scripts/orchestrate.py`) applies the dependency rules and the dikes gate.
- **Post-processing**: Python (h5py, numpy, scipy, rasterio, geopandas, matplotlib) turns each plan's HDF into 2 m rasters, hazard classes, arrival times, people and plots at risk and warning-time products; QGIS 3 print layouts make the maps; FigJam the flowcharts; the report is built as Word OOXML from the hydrology report template and rendered through Word.

## Inputs kept in this repository

| What | Where |
|---|---|
| Hydrology data and rainfall patterns as entered in HEC-RAS | `Data/XLS/` |
| Dam axis, training dikes, land-use plots, project outline | `Data/SHP/` |
| Sea level from the Oman maritime book | `Data/Maritime details.xlsx` |
| HEC-RAS model, text files: project, geometries g02 (dikes) and g03 (no dikes), flow files u26–u31, plans p27–p48, RAS Mapper file | `HEC-RAS Majlas/` |
| HEC-HMS model: basin, meteorology, control and run files | `HEC_HMS_Majlas/` |
| Boundary hydrographs extracted from HEC-HMS | `W2/04_data/hms_res2_hydrographs.xlsx`, `hms_res2_*.csv` |
| 2D area, boundary lines, dam connection, HMS elements as GeoJSON (EPSG:32640) | `W2/04_data/gis/` |
| Dam drawings from the design review (elevation with monoliths, sections) | `W2/02_figures/deck/` |

Not in the repository (size or third-party): the 5 m terrain and the HEC-RAS terrain layers, the HEC-RAS result files (`*.hdf`, 340 MB each), restart files, DSS files, the 2 m result rasters (rebuilt by `ras_results.py`), the design review presentation, the maritime book and the sample dam-break report. They live in the project directory and on the workstation that ran the campaign.

## Outcomes so far

Peak flow at the dam, flooded area (depth over 0.3 m, reservoir excluded), people in the flooded area, area in the worst hazard class and people reached by a 0.3 m rise within 15 minutes of the trigger (failures from the breach; S3D from the start of the storm, hence none).

| Scenario | Peak (m³/s) | Flooded (km²) | People | H6 (km²) | Reached in 15 min |
|---|---|---|---|---|---|
| S1D, sunny-day failure, dikes | 45,312 | 17.0 | 23,212 | 8.7 | 15,600 |
| S1N, sunny-day failure, no dikes | 45,346 | 17.1 | 23,299 | 8.9 | 15,800 |
| S3D, PMF without failure | 17,323 (pool 96.06 m, not overtopped) | 25.9 | 44,088 | 13.0 | 0 (12,000 within 3 h) |
| S2D, flood-day failure at the PMF peak | 63,858 | 27.1 | 46,299 | 18.4 | 25,400 (failure wave over the PMF) |
| S2D-W119, breach 119 m | 79,030 | 27.5 | 46,960 | 19.0 | 25,800 |
| S1D-W51, breach 51 m | 31,663 | 16.4 | 21,999 | 7.4 | 7,600 |
| S1D-W153, breach 153 m | 66,955 | 17.4 | 24,148 | 10.5 | 21,900 |
| S1D-C1.44, weir coefficient 1.44 | 42,384 | 16.9 | 22,876 | 8.5 | 13,900 |

What they mean: the breach width sets the peak almost in proportion, the flooded plain barely moves; the failure at the PMF peak adds depth and force rather than extent; and time, not extent, separates the scenarios: the sunny-day wave reaches the residential centre of Qurayat in 15 minutes and the shoreline in 22, the PMF without failure takes about an hour to reach the town and twelve to reach everyone it will reach. Still computing: S3D-F10000, S2D-F10000, S2D-W51, S2D-W153, S2D-T18m, S2D-T3m.

Deliverables: `W2/05_report/R0/Wadi Majlas Dam Break Analysis Report Rev00.pdf` (interim build, rebuilt from the results at the end of the campaign), maps in `W2/02_figures/maps/results/`, charts in `W2/02_figures/charts/`, per-plan results in `W2/04_data/results/<plan>/` (`summary.json`, `consequences.json`, `warning.json`, `connection.csv`, boundary series, flood outline). The methodology report Rev 00 and the HEC-RAS run sheet are in `W1/05_report/R0/`.

## Repository layout

```
Data/                 inputs as given (XLS, SHP, sea level, QGIS layout template)
HEC-RAS Majlas/       the 2D model, text files only (results and terrain excluded)
HEC_HMS_Majlas/       the basin model, text files only
W1/                   iteration 1: methodology report Rev 00 and run sheet, frozen
W2/                   iteration 2: the runs, the results and the analysis report, live
  01_scripts/         setup, run, dispatch, post-process, charts, maps, report builder
  02_figures/         charts, flowcharts, maps, dam drawings
  03_maps/            QGIS project with the print layouts
  04_data/            hydrographs, GIS, run log, dikes decision, results per plan
  05_report/          the Dam Break Analysis Report
  PROJECT_STATE.md    decisions, numbers, open items, dated
  README.md           the working folder and how to run it
```

## Reproducing

```bash
python W2/01_scripts/01_hms_hydrographs.py       # boundary hydrographs from the HEC-HMS runs
python W2/01_scripts/ras_setup.py --rebuild      # flow files and plans (the geometries are never written by scripts)
python W2/01_scripts/ras_sequence.py p27 p32 p30 # run plans unattended and post-process each (HEC-RAS closed)
python W2/01_scripts/ras_warning.py p28 p32 p30  # warning-time products (a flood-day plan needs its twin's HDF)
python W2/01_scripts/results_charts.py           # charts from whatever results exist
python W2/01_scripts/build_report.py --results   # the report docx; render_pdf.py --results makes the PDF through Word
```

Maps are exported inside QGIS with `W2/01_scripts/qgis_result_maps.py` (`maps_for_plan("p28")`, `map_population("p28")`, `map_warning_arrival("p30")`). Plan names: S1 sunny day, S2 flood day, S3 PMF without failure; D with dikes, N without; a suffix names the one change (W = breach width in m, T = formation time, C = weir coefficient, F = flood). The plan-to-scenario table is in `W2/README.md`.

## Conventions

- Iterations live in `W#` folders and are never overwritten; a rework is the next `W#`. W1 is the record of the methodology as issued; W2 is live.
- The report is rebuilt from the result files, so nothing in it is typed by hand; a scenario without products prints as "pending".
- Open items are listed in `W2/PROJECT_STATE.md`, among them an erratum for the methodology report (its "section" figure is a gallery detail) and the routed PMF level to be confirmed by the design team.

## References

Renardet S.A. & Partners (2026), Dam Break Analysis Methodology Report Rev 00 and Wadi Majlas Hydrology Report; USACE (2024), HEC-RAS 6.6 User's and 2D Modeling manuals; USACE (2014), Using HEC-RAS for Dam Break Studies, TD-39; FERC (2014), Engineering Guidelines, Chapter 2; AIDR (2017), Guideline 7-3 Flood Hazard; ICOLD (2020), Bulletin 111.
