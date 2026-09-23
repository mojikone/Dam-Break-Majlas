# Project state — Wadi Majlas dam break analysis

Last substantive update: 2026-09-20 (W1 methodology report Rev 00 built and rendered).
Live iteration: **W1**. Superseded iterations: none.

## Decided

- The methodology report is a standalone deliverable, approved before any modelling; everything later is based on it (user instruction, 2026-09-20).
- Standard hierarchy: Client requirements → FEMA P-946 (2013) → USACE TD-39 / HEC-RAS manuals → FERC/USACE breach guidance for concrete dams → USBR RCEM 2015 and Best Practices → ANCOLD 2012 → AIDR 7-3 / Smith et al. 2014 → ICOLD B111. No published Omani dam-break standard is known.
- Failure model: concrete gravity → sliding of whole monoliths; breach bottom at the wadi bed (23.0 m); vertical sides; formation time 0.1 h (range 0.05–0.3 h); linear progression; breach weir coefficient 1.44–1.66 m^0.5/s (HEC-RAS gravity range).
- Scenarios S1 sunny day (FSL 84.5 m, no inflow), S2 flood day (PMF, failure when the pool reaches 96.7 m), S3 PMF no failure; each with/without the 200-yr dikes. Hayfaz cascade excluded; bottom outlet closed.
- PMF level used: **96.7 m** (dam section drawing) until the team confirms; the design table says 96.0 m. The parapet (95.5→96.7 m) is **not credited** in the no-failure run; a sensitivity run credits it.
- Consequences: PAR from GHS-POP 2025; loss of life by RCEM with warning cases W0 (none) / W1 (15 min, EWS) / W2 (1 h) / W3 (3 h); damage with the flood-risk study curves; incremental over S3; ANCOLD 2012 + FEMA classes.
- Maps: QGIS, client layout template (`Data/QGIS/QGIS layout template.qpt`), 2 m rasters, same AIDR hazard classes as the flood-risk study.
- Flowcharts: FigJam (Figma MCP); the two long process charts needed subgraph-to-subgraph links to keep column layouts.

## Done (W1)

- Read the deck of 21 Sep 2026 (97 slides) and extracted the finalised characteristics into `01_scripts/data_facts.py`.
- Four QGIS maps, eight charts, four FigJam flowcharts, seven deck drawings.
- Report Rev 00: 82 pages; Word fields updated; PDF exported; 30 pages visually checked (cover, TOC, lists, executive summary, tables, footnotes, landscape maps, equations, conclusions). Remaining known cosmetic items: large white space before landscape pages (inherent to section breaks); bullets use the template's small Bullet style.
- HEC-RAS Run Sheet Rev 00 (5 pages, 11 tables): run register, results to record, geometry and terrain steps, Manning table, dam connection entries, breach entries (base/lower/upper), six base runs, water levels, 15 sensitivity runs, computation and output settings, checks. Companion to the report; no explanations by design (user request, 2026-09-20).

## Open / needed from the team (also Appendix D of the report)

1. Monolith joint layout with block widths (B1–B17) → final breach widths.
2. Routed PMF maximum water level (96.0 or 96.7 m) and the routing calculation.
3. Elevation–area–volume table for the straight axis (current curve is for the arch axis).
4. Design surfaces (dam, spillway, basin, chute, dikes, crossings, roads) and the 5 cm / 2 m survey files.
5. Spillway rating curve and ogee design head; tide levels at Qurayat; infrastructure and daytime-population layers.

## Next

- Internal review of Rev 00 by a senior engineer; then issue to the Client for approval.
- On approval: W2 = model build (terrain merge, reservoir 2D area, dam connection), following Appendix B of the report.

## Numbers that anyone quoting this project must use (from the 21 Sep 2026 deck)

FSL 84.5 m / 102.2 Mm³; MWL 96.0 (table) or 96.7 m (section) / 150.7 Mm³; crest 95.5 m, parapet 96.7 m, crest length 312 m, height 72.5 m above bed, 110.5 m above foundation (−15 m); spillway ogee 84.5 m, 5 × 40 m bays, 4 × 3 m piers, 200 m net, 17,000 m³/s; bottom outlet 2.8 m pipe, 120 m³/s; PMF 18,179 m³/s / 549 Mm³; 10,000-yr 13,375 m³/s; 200-yr 4,370 m³/s / 90.5 Mm³; dikes 2,600 m for 200-yr; Qurayat 2 km downstream.
