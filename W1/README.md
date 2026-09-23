# Wadi Majlas Dam Break Analysis — W1: Methodology Report

**Status: W1 is the live iteration.** No earlier iteration exists. The methodology report Rev 00 was built on 2026-09-20 and is ready for internal review before issue to the Client.

## What this folder holds

| Folder | Content |
|---|---|
| `01_scripts/` | Everything that builds the deliverable. `data_facts.py` holds every number with its source; `charts.py` draws the charts; `qgis_maps.py` builds the four map layouts inside QGIS; `build_report.py` + `rpt_content.py` + `rpt_content2.py` write the Word report from the Hydrology Report template; `render_pdf.py` updates fields in Word, exports the PDF and renders review pages. |
| `02_figures/` | `charts/` (8 charts), `maps/` (4 QGIS exports at 250 dpi), `flowcharts/` (4 FigJam diagrams as SVG + PNG), `deck/` (7 drawings taken from the 21 Sep 2026 design review presentation). |
| `03_maps/` | `Majlas_DamBreak_W1.qgz` — QGIS project with all layers styled and the four print layouts (Map 01 to Map 04) cloned from the client-approved template; `figma_boards.md` — links to the editable FigJam boards. |
| `04_data/` | `majlas_inflow_hydrographs.csv` (200/500/1,000/10,000-yr and PMF inflow, 5-min step); `gis/` — indicative straight dam axis, model extents (existing 2D area + proposed), data-extent boxes, Qurayat point. |
| `05_report/R0/` | **Wadi Majlas Dam Break Analysis Methodology Report Rev00.docx** and `.pdf` (82 pages, 23 figures, 32 tables, 13 equations, 19 footnotes). **Wadi Majlas Dam Break Analysis - HEC-RAS Run Sheet Rev00.docx** and `.pdf` (5 pages, 11 tables): the short companion with values and actions only, built by `build_report.py --runsheet` from `rpt_runsheet.py`. `_build/`, `_review/` and `_review_runsheet/` are scratch. |
| `06_refs/` | Reference notes (none yet; the reference list is in the report). |

## How to rebuild

```
python 01_scripts/charts.py            # charts from data_facts.py and 04_data
# in QGIS (MCP or console): exec(open("01_scripts/qgis_maps.py").read())   # maps; saves the project
python 01_scripts/build_report.py      # Word report from the template
python 01_scripts/render_pdf.py 1 3 10 # Word field update + PDF + review PNGs of the listed pages
python 01_scripts/build_report.py --runsheet && python 01_scripts/render_pdf.py --runsheet 1-5   # the companion run sheet
```

Change a number only in `data_facts.py`; charts, tables and text all read from it.

## Key decisions recorded in the report (see PROJECT_STATE.md for the reasoning and open items)

- RCC gravity dam → monolith-based breach (vertical sides, whole blocks, 0.1 h), not the embankment regression equations used for Al Dreez.
- Three scenarios: sunny day at FSL 84.5 m; flood day at the PMF pool 96.7 m; PMF without failure (baseline). Each with and without the dikes → six base runs, plus a named sensitivity list.
- Breach width: base two spillway bays (86 m), lower one bay (43 m), upper half the crest (156 m); to be rounded to the real block layout when supplied.
- HEC-RAS 6.6, 2D, full shallow-water equations, reservoir as a 2D area, dam as an SA/2D connection, sea boundary.
- Products: depth, velocity, D×V, arrival time, duration, AIDR H1–H6, incremental depth; PAR, RCEM loss of life, damage; ANCOLD 2012 category and FEMA class.
