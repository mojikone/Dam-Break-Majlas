# Wadi Majlas Dam Break Analysis — W2: model inputs and HEC-RAS runs

**Status: W2 is the live iteration** (started 2026-09-22). W1 (methodology report Rev 00 and the HEC-RAS run sheet) is frozen and superseded only where this folder says so.

Campaign status (2026-09-23 04:40): base runs S1D, S1N, S3D, S2D done; S3N and S2N dropped (dikes immaterial, `04_data/dikes_decision.json`); sensitivity runs S1D-W51, S1D-W153, S1D-C1.44, S2D-W119 done, S3D-F10000, S2D-T18m, S2D-T3m running, S2D-F10000, S2D-W51, S2D-W153 queued. Interim report: `05_report/R0/Wadi Majlas Dam Break Analysis Report Rev00.pdf` (62 pages, 07:15); the final build follows the last run. Details and numbers: `PROJECT_STATE.md`.

## What this folder holds

| Folder | Content |
|---|---|
| `01_scripts/` | Copied from W1 (report builders, charts, QGIS maps, data facts) plus the W2 scripts. Hydrology: `01_hms_hydrographs.py` extracts the HEC-RAS boundary hydrographs from the HEC-HMS "DA … Res2" runs (`_sample_01_hydrographs_from_W2Majlas.py` is the earlier hydrology script it was built from). HEC-RAS: `ras_setup.py` builds the unsteady-flow files and plans (never the geometries), `ras_run.py` drives one plan through the HECRASController, `ras_sequence.py` runs a list of plans unattended and post-processes each, `ras_results.py` turns a plan HDF into CSV series, 2 m rasters and `summary.json`, `ras_analysis.py` counts people and plots at risk, `ras_warning.py` times who is reached when (arrival bands, places, band × hazard matrix, failure wave over the PMF), `results_charts.py` draws the result charts, `qgis_result_maps.py` exports the result maps inside QGIS, `ras_make_copies.py` creates the parallel project copies, `ras_maps_def.py` and `ras_rename_plans.py` prepared the RAS Mapper file and the plan names. |
| `04_data/` | Hydrographs (`hms_res2_hydrographs.xlsx`, `hms_res2_<location>.csv`), `gis/`, the run log `run_sequence.log`, the run register `run_register.csv`, and `results/<plan>/` with `summary.json`, `connection.csv`, `boundary_*.csv`, `trigger.json` (S2 runs) and the rasters `max_depth`, `max_velocity`, `max_dv`, `arrival_h`, `duration_h`, `hazard_aidr` (2 m, EPSG:32640). |
| `02_figures/` | `charts/results_*.png` and `maps/results/<plan> <map> <extent>.png` (depth, hazard, arrival; reach and town). |
| `02_figures/deck/` | Drawings taken from the design review deck (`Data/20260921-Majlas Dam Design.pptx`): upstream elevation with the monoliths, non-overflow and spillway sections, cropped for the report. |
| `03_maps/` | `Majlas_DamBreak_W2.qgz`, the QGIS project whose layouts produce the maps. |
| `05_report/`, `06_refs/` | Report and references, filled when the runs are complete. |

Related folders beside W1/W2 (not iterations, kept as given):

- `HEC_HMS_Majlas/` — copy of the HEC-HMS project with the south catchment ("Basin 1 Res2", runs "DA <rp> Res2").
- `HEC-RAS Majlas/` — the HEC-RAS project: the user's geometries g02 (dikes) and g03 (no dikes), the flow files u26–u31 and plans p27–p43, p48 written by `ras_setup.py`.
- `HEC-RAS Majlas_run2/`, `_run3/` — lightweight copies for parallel runs (text files copied, terrain linked); results are still written to `W2/04_data/results/`. `_test/`, `_test2/` are scratch copies used for the 2026-09-22 stall diagnosis and can be deleted.

## Plan names

S1 sunny day failure, S2 flood day PMF failure at the maximum pool, S3 PMF no failure; D with dikes, N without; a suffix names the one thing changed: W<breach width m>, T<formation time>, C<weir coefficient>, F<flood return period>. Fill plans (Fill, FillN) only write the restart file each geometry starts from. See `PROJECT_STATE.md` for the plan codes and the run status.

## How to run

```
python W2/01_scripts/01_hms_hydrographs.py          # hydrographs from HEC-HMS
python W2/01_scripts/ras_setup.py --rebuild          # flow files and plans (project file untouched)
python W2/01_scripts/ras_sequence.py p27 p32 p30     # run a list of plans and post-process each (HEC-RAS closed; RAS_DIR selects a copy)
python W2/01_scripts/results_charts.py               # charts from whatever results exist
```
Maps: in QGIS with the W2 project open, run `qgis_result_maps.py` through the console or the MCP and call `maps_for_plan("p28")`.
