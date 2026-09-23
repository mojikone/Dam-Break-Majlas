# -*- coding: utf-8 -*-
"""Result maps for the dam-break runs, inside QGIS (run through the QGIS MCP execute_code or the console).
For every plan folder in W2/04_data/results/<plan>/ with rasters, clones the client layout template and exports
max depth, AIDR hazard and arrival-time maps (general view of the reach and a Qurayat close-up) to W2/02_figures/maps/results/.
Layouts stay in the W2 QGIS project. Reuses helpers of W1/qgis_maps.py (same template, same furniture).
"""
import os, json, glob
from qgis.core import (QgsProject, QgsRasterLayer, QgsVectorLayer, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemLabel, QgsLayoutFrame, QgsLayoutItemManualTable, QgsTableCell, QgsLayoutExporter, QgsRectangle,
                       QgsSingleBandPseudoColorRenderer, QgsColorRampShader, QgsRasterShader, QgsPalettedRasterRenderer, QgsLayoutItemScaleBar,
                       QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes, QgsLineSymbol, QgsSingleSymbolRenderer, QgsLegendRenderer, QgsLegendStyle)
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtGui import QColor

BASE = "D:/Mojtaba/Renardet/2224 WS11/Majlas/"
W2 = BASE + "Hydraulic/Dam Breack/W2/"
RESULTS = W2 + "04_data/results/"
OUT = W2 + "02_figures/maps/results/"
TPL = BASE + "Hydraulic/Dam Breack/Data/QGIS/QGIS layout template.qpt"
GIS = W2 + "04_data/gis/"
os.makedirs(OUT, exist_ok=True)
prj = QgsProject.instance()
SUBTITLE = "Wadi Majlas Flood Protection Dam - Dam Break Analysis | Renardet S.A. & Partners, 2026"
EXTENTS = {"reach": (681700, 2565850, 698500, 2577300, 60000),      # the whole 2D area (682406-697834 E, 2566166-2576981 N) with a margin
           "town": (689900, 2570200, 698900, 2576300, 32000),       # Qurayat and the plain down to the southern flooded fields (user, 2026-09-23)
           "hms": (663000, 2563500, 699500, 2583500, 130000)}       # the whole HEC-HMS basin model

def sat():
    for l in prj.mapLayers().values():
        if "Google Satellite" in l.name(): return l

def vector(name, path, symbol):
    for l in prj.mapLayers().values():
        if l.name() == name:
            l.setRenderer(QgsSingleSymbolRenderer(symbol)); l.triggerRepaint(); return l      # existing layer takes the current style
    l = QgsVectorLayer(path, name, "ogr"); l.setRenderer(QgsSingleSymbolRenderer(symbol))
    if l.crs().authid() != "EPSG:32640":
        from qgis.core import QgsCoordinateReferenceSystem; l.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))    # project files are UTM 40N
    prj.addMapLayer(l); return l

def raster(name, path):
    for l in prj.mapLayers().values():
        if l.name() == name: prj.removeMapLayer(l.id())
    l = QgsRasterLayer(path, name); prj.addMapLayer(l); return l

def style_depth(l):
    sh = QgsRasterShader(); r = QgsColorRampShader(); r.setColorRampType(QgsColorRampShader.Discrete)
    steps = [(0.3, "#cde2fb", "0.05 - 0.3 m"), (0.5, "#9ec5f4", "0.3 - 0.5 m"), (1.0, "#6da7ec", "0.5 - 1 m"), (2.0, "#3987e5", "1 - 2 m"),
             (4.0, "#1c5cab", "2 - 4 m"), (8.0, "#104281", "4 - 8 m"), (1000, "#0d366b", "over 8 m")]
    r.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), lab) for v, c, lab in steps]); sh.setRasterShaderFunction(r)
    rr = QgsSingleBandPseudoColorRenderer(l.dataProvider(), 1, sh); rr.setOpacity(0.85); l.setRenderer(rr)

def style_hazard(l):
    # same colours and wording as the flood-protection risk maps (Flood Protection/Risk/Data/QGIS RISK.qgz), so the two studies read alike
    cls = [(1, "#0000ff", "H1 generally safe"), (2, "#00ecff", "H2 unsafe: small vehicles"), (3, "#00a504", "H3 unsafe: vehicles, children"),
           (4, "#00ff30", "H4 unsafe for people"), (5, "#fff900", "H5 unsafe; buildings damaged"), (6, "#f41f1f", "H6 unsafe; buildings fail")]
    r = QgsPalettedRasterRenderer(l.dataProvider(), 1, [QgsPalettedRasterRenderer.Class(v, QColor(c), lab) for v, c, lab in cls]); r.setOpacity(0.85); l.setRenderer(r)

def style_arrival(l):
    # user's sequence (2026-09-23): red = least warning, then orange, yellow, green, light blue = most warning time
    sh = QgsRasterShader(); r = QgsColorRampShader(); r.setColorRampType(QgsColorRampShader.Discrete)
    steps = [(0.25, "#b30000", "0 - 15 min"), (0.5, "#e8432f", "15 - 30 min"), (1.0, "#f28e2b", "30 - 60 min"), (2.0, "#f2d13d", "1 - 2 h"),
             (4.0, "#5fbf6a", "2 - 4 h"), (1000, "#9ecae1", "over 4 h")]
    r.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), lab) for v, c, lab in steps]); sh.setRasterShaderFunction(r)
    rr = QgsSingleBandPseudoColorRenderer(l.dataProvider(), 1, sh); rr.setOpacity(0.85); l.setRenderer(rr)

def load_template(name):
    mgr = prj.layoutManager()
    for l in list(mgr.printLayouts()):
        if l.name() == name: mgr.removeLayout(l)
    doc = QDomDocument(); doc.setContent(open(TPL, encoding="utf-8").read())
    lay = QgsPrintLayout(prj); lay.initializeDefaults(); lay.loadFromTemplate(doc, QgsReadWriteContext()); lay.setName(name); mgr.addLayout(lay); return lay

def items_of(lay):
    out = {"labels": []}
    for it in lay.items():
        if isinstance(it, QgsLayoutItemMap): out["map"] = it
        elif isinstance(it, QgsLayoutItemLegend): out["legend"] = it
        elif isinstance(it, QgsLayoutItemLabel): out["labels"].append(it)
        elif isinstance(it, QgsLayoutItemScaleBar): out["scalebar"] = it
        elif isinstance(it, QgsLayoutFrame) and isinstance(it.multiFrame(), QgsLayoutItemManualTable): out["table"] = it.multiFrame(); out["frame"] = it
    out["title"] = [l for l in out["labels"] if l.textFormat().size() >= 14][0]; out["subtitle"] = [l for l in out["labels"] if 8 <= l.textFormat().size() < 10][0]
    return out

def fit(m, xmin, ymin, xmax, ymax):
    ar = m.sizeWithUnits().width() / m.sizeWithUnits().height(); cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2; w, h = xmax - xmin, ymax - ymin
    if w / h < ar: w = h * ar
    else: h = w / ar
    m.setExtent(QgsRectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))

def export(name, title, layers, legend_layers, extent_key, rows, hide_title=(), subtitle=None):
    lay = load_template(name); it = items_of(lay)
    it["title"].setText(title); it["subtitle"].setText(subtitle or SUBTITLE)
    try: it["title"].attemptResize(QgsLayoutSize(180.0, it["title"].sizeWithUnits().height(), QgsUnitTypes.LayoutMillimeters))   # never under the scale bar
    except Exception: pass
    m = it["map"]; ls = list(layers); s = sat()
    if s: ls.append(s)
    m.setLayers(ls); m.setKeepLayerSet(True); x0, y0, x1, y1, sc = EXTENTS[extent_key]; fit(m, x0, y0, x1, y1); m.setScale(sc)
    lg = it["legend"]; lg.setAutoUpdateModel(False); root = lg.model().rootGroup(); root.removeAllChildren()
    for l in legend_layers:
        node = root.addLayer(l)
        if l.name() in hide_title: QgsLegendRenderer.setNodeLegendStyle(node, QgsLegendStyle.Hidden)
        if isinstance(l, QgsRasterLayer):      # drop the "Band 1 (Gray)" line that QGIS puts above a raster's classes
            try:
                from qgis.core import QgsMapLayerLegendUtils
                n = len(lg.model().layerLegendNodes(node, True))
                if n > 1: QgsMapLayerLegendUtils.setLegendNodeOrder(node, list(range(1, n))); lg.model().refreshLayerLegend(node)
            except Exception as e: print("legend band label:", e)
    lg.setLinkedMap(m); lg.updateLegend(); lg.adjustBoxSize()
    tbl = it["table"]; tbl.setTableContents([[QgsTableCell(a), QgsTableCell(b)] for a, b in rows]); tbl.setColumnWidths([34.0, 62.0])
    try:
        from qgis.PyQt.QtGui import QColor as _QC
        tbl.setBackgroundColor(_QC(255, 255, 255, 190)); it["frame"].setBackgroundEnabled(False)      # lightly transparent, it sits on the map
    except Exception as e: print("table background:", e)
    # information table: bottom-right corner INSIDE the map frame, 6 mm clear of its edge. The frame takes the table's own rendered size
    # (column widths plus cell margins and borders), which is wider than the sum of the column widths.
    from qgis.core import QgsLayoutTable
    tbl.setHeaderMode(QgsLayoutTable.NoHeaders)      # the template's (empty) header row inflated totalHeight() by 13 mm and left a gap below the table
    tbl.refreshAttributes(); tbl.recalculateFrameSizes()
    # totalHeight() reports 45.7 mm for five rows that render 25.5 mm tall (row heights are not cached before an export), so the
    # height is computed from the font: text height + two cell margins + grid line per row
    try:
        font_mm = tbl.contentTextFormat().size() * 0.3528 if tbl.contentTextFormat().sizeUnit() == QgsUnitTypes.RenderPoints else 2.8
    except Exception: font_mm = 2.8
    row_h = 1.15 * font_mm + 2 * tbl.cellMargin() + tbl.gridStrokeWidth()
    fw, fh = tbl.totalWidth(), row_h * len(rows) + tbl.gridStrokeWidth()
    mp = m.positionWithUnits(); ms = m.sizeWithUnits(); margin = 4.0
    fx = mp.x() + margin; fy = mp.y() + ms.height() - fh - margin      # anchored to the map's lower-LEFT corner: the lower right holds the town (user, 2026-09-23)
    it["frame"].attemptMove(QgsLayoutPoint(fx, fy, QgsUnitTypes.LayoutMillimeters)); it["frame"].attemptResize(QgsLayoutSize(fw, fh, QgsUnitTypes.LayoutMillimeters))
    sb = it.get("scalebar")
    if sb: sb.setLinkedMap(m); sb.setNumberOfSegments(2); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment({60000: 1.0, 30000: 0.5, 32000: 0.5, 130000: 5.0}.get(sc, 1.0)); sb.update()
    lay.refresh(); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 250
    QgsLayoutExporter(lay).exportToImage(OUT + name + ".png", st); print("exported", name)

def maps_for_plan(code):
    d = RESULTS + code + "/"
    if not os.path.exists(d + "max_depth.tif"): print("no rasters for", code); return
    s = json.load(open(d + "summary.json"))
    axis = vector("Straight dam axis (indicative)", GIS + "dam_axis_straight_indicative.shp", QgsLineSymbol.createSimple({"color": "#000000", "width": "1.4"}))   # black: red vanished on the H6 / arrival classes
    # the two training dikes as drawn in the flood-protection risk maps (CAD export, 2 lines), not the older 5-line sketch (user, 2026-09-22)
    dikes = vector("Training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Dykes.shp", QgsLineSymbol.createSimple({"color": "#eb6834", "width": "0.9"}))
    label = s.get("plan_title", code); sid = label.split()[0]      # scenario id (S1D, S2D-W51, ...) for legend titles
    dep = raster(f"{sid} max depth (m)", d + "max_depth.tif"); style_depth(dep)
    haz = raster(f"{sid} hazard AIDR", d + "hazard_aidr.tif"); style_hazard(haz)
    arr = raster(f"{sid} arrival time (h)", d + "arrival_h.tif"); style_arrival(arr)
    desc = label[len(sid):].strip(" ,").replace(", no dikes", ", without dikes").replace(", dikes", ", with dikes")
    rows = [["Scenario", f"{sid} ({desc})"], ["Peak flow at dam", f"{s.get('peak_total_flow_m3s', 0):,.0f} m3/s"], ["Time of peak", f"{s.get('peak_time_h', 0):.1f} h"],
            ["Flooded area > 0.3 m", f"{s.get('inundated_area_km2_gt0.3m', 0):.1f} km2"],
            ["Max depth, gorge / plain", f"{s.get('max_depth_m', 0):.0f} m / {s.get('max_depth_plain_m', 0) or 0:.1f} m"]]      # no volume error on maps (user, 2026-09-22)
    over = [axis] if sid.split("-")[0].endswith("N") else [axis, dikes]      # no dikes drawn on a no-dikes scenario
    sub = f"{label} | Wadi Majlas Flood Protection Dam, Dam Break Analysis | Renardet S.A. & Partners, 2026"   # description in the subtitle keeps the title short
    ref = "after the start of the storm" if sid.startswith("S3") else "after the breach"
    for ext in ("reach", "town"):
        export(f"{sid} depth {ext}", f"{sid}: maximum depth", over + [dep], over + [dep], ext, rows, hide_title=(), subtitle=sub)
        export(f"{sid} hazard {ext}", f"{sid}: flood hazard class (AIDR H1 to H6)", over + [haz], over + [haz], ext, rows, subtitle=sub)
        export(f"{sid} arrival {ext}", f"{sid}: arrival time of a 0.3 m depth {ref}", over + [arr], over + [arr], ext, rows, subtitle=sub)
    prj.write()

def map_warning_arrival(code):
    """arrival of the failure wave on top of the PMF (flood-day failures): the time after the breach at which the depth is 0.3 m more
    than in the no-failure twin at the same instant (ras_warning.py, warning_arrival_h.tif); user request 2026-09-23"""
    d = RESULTS + code + "/"
    if not os.path.exists(d + "warning_arrival_h.tif"): print("no warning arrival for", code); return
    s = json.load(open(d + "summary.json")); w = json.load(open(d + "warning.json"))
    axis = vector("Straight dam axis (indicative)", GIS + "dam_axis_straight_indicative.shp", QgsLineSymbol.createSimple({"color": "#000000", "width": "1.4"}))
    dikes = vector("Training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Dykes.shp", QgsLineSymbol.createSimple({"color": "#eb6834", "width": "0.9"}))
    label = s.get("plan_title", code); sid = label.split()[0]
    arr = raster(f"{sid} failure wave arrival (h)", d + "warning_arrival_h.tif"); style_arrival(arr)
    desc = label[len(sid):].strip(" ,").replace(", no dikes", ", without dikes").replace(", dikes", ", with dikes")
    pc = w["people_cum"]; bands = w["bands_h"]
    rows = [["Scenario", f"{sid} ({desc})"], ["Breach", f"{s.get('breach_start_h', 0):.1f} h into the storm"],
            ["People +0.3 m within 15 min", f"{pc[bands.index(0.25)]:,.0f}"], ["People +0.3 m within 1 h", f"{pc[bands.index(1.0)]:,.0f}"],
            ["People in flooded area", f"{w['people_total']:,.0f}"]]
    over = [axis] if sid.split("-")[0].endswith("N") else [axis, dikes]
    sub = f"{label} | Wadi Majlas Flood Protection Dam, Dam Break Analysis | Renardet S.A. & Partners, 2026"
    export(f"{sid} wave town", f"{sid}: arrival of the failure wave over the PMF (0.3 m extra depth)", over + [arr], over + [arr], "town", rows, subtitle=sub)
    prj.write()

def map_hazard_arrival(code, iso="isochrones_v1.geojson", wave=False):
    """hazard class (AIDR palette) with arrival isochrones on top (15 min, 30 min, 1 h, 2 h after the breach; for a flood-day failure the
    arrival of the failure wave over the PMF). Lines from ras_warning products (isochrones_*.geojson); user request 2026-09-23 11:10"""
    d = RESULTS + code + "/"
    if not os.path.exists(d + iso): print("no isochrones for", code); return
    s = json.load(open(d + "summary.json")); w = json.load(open(d + "warning.json")) if os.path.exists(d + "warning.json") else {}
    axis = vector("Straight dam axis (indicative)", GIS + "dam_axis_straight_indicative.shp", QgsLineSymbol.createSimple({"color": "#000000", "width": "1.4"}))
    dikes = vector("Training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Dykes.shp", QgsLineSymbol.createSimple({"color": "#eb6834", "width": "0.9"}))
    label_ = s.get("plan_title", code); sid = label_.split()[0]
    haz = raster(f"{sid} hazard AIDR", d + "hazard_aidr.tif"); style_hazard(haz)
    sym = QgsLineSymbol.createSimple({"color": "#111111", "width": "0.8", "line_style": "solid"})
    from qgis.core import QgsSimpleLineSymbolLayer
    sym.insertSymbolLayer(0, QgsSimpleLineSymbolLayer(QColor(255, 255, 255), 1.9))        # white casing so the line reads on red and yellow
    iso_l = vector(f"{sid} arrival isochrones", d + iso, sym)
    label(iso_l, field="label", size=9, placement="line", bold=True, color="#111111", all_labels=False)
    desc = label_[len(sid):].strip(" ,").replace(", no dikes", ", without dikes").replace(", dikes", ", with dikes")
    pc = w.get("people_cum", []); bands = w.get("bands_h", [])
    rows = [["Scenario", f"{sid} ({desc})"], ["Peak flow at dam", f"{s.get('peak_total_flow_m3s', 0):,.0f} m3/s"],
            ["Isochrones", "arrival of the failure wave over the PMF" if wave else "arrival of a 0.3 m rise after the breach"]]
    if pc: rows += [["People reached within 15 min", f"{pc[bands.index(0.25)]:,.0f}"], ["People reached within 1 h", f"{pc[bands.index(1.0)]:,.0f}"]]
    over = [axis] if sid.split("-")[0].endswith("N") else [axis, dikes]
    sub = f"{label_} | Wadi Majlas Flood Protection Dam, Dam Break Analysis | Renardet S.A. & Partners, 2026"
    what = "hazard class (AIDR) with arrival isochrones of the failure wave" if wave else "hazard class (AIDR) with arrival isochrones"
    export(f"{sid} hazard-arrival town", f"{sid}: {what}", over + [iso_l, haz], over + [haz, iso_l], "town", rows, subtitle=sub)
    prj.write()

def style_arrival_steps(l, steps):
    """arrival fill: red = least warning, fading with time to light blue (user, 2026-09-23 11:45)"""
    sh = QgsRasterShader(); r = QgsColorRampShader(); r.setColorRampType(QgsColorRampShader.Discrete)
    r.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), lab) for v, c, lab in steps]); sh.setRasterShaderFunction(r)
    rr = QgsSingleBandPseudoColorRenderer(l.dataProvider(), 1, sh); rr.setOpacity(0.85); l.setRenderer(rr)

ARRIVAL_FAIL = [(5 / 60, "#7f0000", "0 - 5 min"), (10 / 60, "#b30000", "5 - 10 min"), (0.25, "#e8432f", "10 - 15 min"), (0.5, "#f28e2b", "15 - 30 min"),
                (1.0, "#f2d13d", "30 - 60 min"), (1000, "#9ecae1", "over 1 h")]
ARRIVAL_PMF = [(1.0, "#7f0000", "0 - 1 h"), (2.0, "#b30000", "1 - 2 h"), (3.0, "#e8432f", "2 - 3 h"), (6.0, "#f28e2b", "3 - 6 h"), (12.0, "#f2d13d", "6 - 12 h"),
               (1000, "#9ecae1", "over 12 h")]

def hazard_lines(sid, path):
    """H6 and H4 boundaries as two line layers (solid and dashed, white casing), from hazard_lines_*.geojson"""
    from qgis.core import QgsSimpleLineSymbolLayer
    out = []
    for lab, name, style in (("H6", f"{sid} H6 boundary: buildings fail", "solid"), ("H4", f"{sid} H4 boundary: unsafe on foot", "dash")):
        sym = QgsLineSymbol.createSimple({"color": "#ffffff", "width": "0.9" if lab == "H6" else "0.8", "line_style": style})
        sym.insertSymbolLayer(0, QgsSimpleLineSymbolLayer(QColor(0, 0, 0), 2.0 if lab == "H6" else 1.8))          # white on a black casing
        l = vector(name, path, sym); l.setSubsetString(f"\"label\" = '{lab}'"); out.append(l)
        label(l, field="label", size=8, placement="line", bold=True, color="#000000", all_labels=False)
    return out

def map_arrival_hazard(code, version="v3"):
    """one map per scenario: for a failure, the arrival fill (0.3 m rise; the failure wave over the PMF on a flood day) with the H4 and H6
    boundaries on top; for the flood without failure, the hazard fill with arrival isochrones (hours). User, 2026-09-23 11:45."""
    d = RESULTS + code + "/"
    if not os.path.exists(d + f"hazard_lines_{version}.geojson"): print("no lines for", code); return
    s = json.load(open(d + "summary.json")); w = json.load(open(d + "warning.json")) if os.path.exists(d + "warning.json") else {}
    axis = vector("Straight dam axis (indicative)", GIS + "dam_axis_straight_indicative.shp", QgsLineSymbol.createSimple({"color": "#000000", "width": "1.4"}))
    dikes = vector("Training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Dykes.shp", QgsLineSymbol.createSimple({"color": "#eb6834", "width": "0.9"}))
    label_ = s.get("plan_title", code); sid = label_.split()[0]; fail = s.get("breach_start_h") is not None; wave = fail and s["breach_start_h"] > 5
    desc = label_[len(sid):].strip(" ,").replace(", no dikes", ", without dikes").replace(", dikes", ", with dikes")
    over = [axis] if sid.split("-")[0].endswith("N") else [axis, dikes]
    sub = f"{label_} | Wadi Majlas Flood Protection Dam, Dam Break Analysis | Renardet S.A. & Partners, 2026"
    pc = w.get("people_cum", []); bands = w.get("bands_h", [])
    rows = [["Scenario", f"{sid} ({desc})"], ["Peak flow at dam", f"{s.get('peak_total_flow_m3s', 0):,.0f} m3/s"]]
    if fail:
        arr = raster(f"{sid} arrival of the wave (0.3 m rise)" + (" over the PMF" if wave else ""), d + "warning_arrival_h.tif"); style_arrival_steps(arr, ARRIVAL_FAIL)
        lines = hazard_lines(sid, d + f"hazard_lines_{version}.geojson")
        if pc: rows += [["People reached within 15 min", f"{pc[bands.index(0.25)]:,.0f}"], ["People reached within 1 h", f"{pc[bands.index(1.0)]:,.0f}"], ["People in flooded area", f"{w['people_total']:,.0f}"]]
        title = f"{sid}: failure wave over the PMF, with the H4 and H6 lines" if wave else f"{sid}: wave arrival with the H4 and H6 lines"
        export(f"{sid} arrival-hazard town", title, over + lines + [arr], over + [arr] + lines, "town", rows, subtitle=sub)
    else:
        haz = raster(f"{sid} hazard AIDR", d + "hazard_aidr.tif"); style_hazard(haz)
        from qgis.core import QgsSimpleLineSymbolLayer
        sym = QgsLineSymbol.createSimple({"color": "#111111", "width": "0.8"}); sym.insertSymbolLayer(0, QgsSimpleLineSymbolLayer(QColor(255, 255, 255), 1.9))
        iso_l = vector(f"{sid} arrival isochrones (h after the storm starts)", d + f"isochrones_{version}.geojson", sym)
        label(iso_l, field="label", size=9, placement="line", bold=True, color="#111111", all_labels=False)
        if pc: rows += [["People reached within 3 h", f"{pc[bands.index(3.0)]:,.0f}"], ["People reached within 12 h", f"{pc[bands.index(12.0)]:,.0f}"], ["People in flooded area", f"{w['people_total']:,.0f}"]]
        export(f"{sid} arrival-hazard town", f"{sid}: hazard class with arrival isochrones (hours)", over + [iso_l, haz], over + [haz, iso_l], "town", rows, subtitle=sub)
    prj.write()

# ---- variants for the user's choice (2026-09-23 12:00): which variable is the fill, which the lines, and how the lines are coloured
HAZ_COL = {"H2": "#00ffff", "H3": "#008000", "H4": "#00ff00", "H5": "#ffff00", "H6": "#f41f1f"}          # risk-map palette
HAZ_GREY = {"H2": "#c8c8c8", "H3": "#9a9a9a", "H4": "#6a6a6a", "H5": "#3a3a3a", "H6": "#000000"}         # strong to less strong
ISO_COL = {"5 min": "#7f0000", "10 min": "#b30000", "15 min": "#e8432f", "30 min": "#f28e2b", "1 h": "#f2d13d"}

def line_layers(prefix, path, labels, colours, widths=None, casing=True, dashed=()):
    """one line layer per label (subset of the geojson), coloured per label, optional white casing"""
    from qgis.core import QgsSimpleLineSymbolLayer
    out = []
    for lab in labels:
        w = (widths or {}).get(lab, 0.8)
        sym = QgsLineSymbol.createSimple({"color": colours[lab], "width": str(w), "line_style": "dash" if lab in dashed else "solid"})
        if casing: sym.insertSymbolLayer(0, QgsSimpleLineSymbolLayer(QColor(255, 255, 255), w + 1.2))
        l = vector(f"{prefix} {lab}", path, sym); l.setSubsetString(f"\"label\" = '{lab}'"); out.append(l)
    return out

def map_variants(code, version="v3"):
    d = RESULTS + code + "/"; s = json.load(open(d + "summary.json")); w = json.load(open(d + "warning.json"))
    axis = vector("Straight dam axis (indicative)", GIS + "dam_axis_straight_indicative.shp", QgsLineSymbol.createSimple({"color": "#000000", "width": "1.4"}))
    dikes = vector("Training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Dykes.shp", QgsLineSymbol.createSimple({"color": "#eb6834", "width": "0.9"}))
    label_ = s.get("plan_title", code); sid = label_.split()[0]
    desc = label_[len(sid):].strip(" ,").replace(", no dikes", ", without dikes").replace(", dikes", ", with dikes")
    over = [axis, dikes]; sub = f"{label_} | Wadi Majlas Flood Protection Dam, Dam Break Analysis | Renardet S.A. & Partners, 2026"
    pc = w["people_cum"]; bands = w["bands_h"]
    rows = [["Scenario", f"{sid} ({desc})"], ["Peak flow at dam", f"{s.get('peak_total_flow_m3s', 0):,.0f} m3/s"],
            ["People reached within 15 min", f"{pc[bands.index(0.25)]:,.0f}"], ["People reached within 1 h", f"{pc[bands.index(1.0)]:,.0f}"], ["People in flooded area", f"{w['people_total']:,.0f}"]]
    arr = raster(f"{sid} arrival of the wave (0.3 m rise)", d + "warning_arrival_h.tif"); style_arrival_steps(arr, ARRIVAL_FAIL)
    allp = d + f"hazard_lines_all_{version}.geojson"; labs = ["H2", "H3", "H4", "H5", "H6"]
    # 2: arrival fill + every hazard boundary in greys, strong to less strong
    L2 = line_layers(f"{sid} hazard boundary", allp, labs, HAZ_GREY, widths={"H2": 0.45, "H3": 0.55, "H4": 0.65, "H5": 0.8, "H6": 1.0})
    export(f"{sid} variant2 town", f"{sid}: wave arrival, hazard boundaries in greys", over + L2 + [arr], over + [arr] + L2, "town", rows, subtitle=sub)
    for l in L2: prj.removeMapLayer(l.id())
    # 3: arrival fill + every hazard boundary in the hazard colours
    L3 = line_layers(f"{sid} hazard boundary", allp, labs, HAZ_COL, widths={"H2": 0.6, "H3": 0.6, "H4": 0.7, "H5": 0.8, "H6": 0.9})
    export(f"{sid} variant3 town", f"{sid}: wave arrival, hazard boundaries in hazard colours", over + L3 + [arr], over + [arr] + L3, "town", rows, subtitle=sub)
    for l in L3: prj.removeMapLayer(l.id())
    # 4: hazard fill + isochrones coloured by the arrival ramp
    haz = raster(f"{sid} hazard AIDR", d + "hazard_aidr.tif"); style_hazard(haz)
    isop = d + f"isochrones_{version}.geojson"; ilabs = ["5 min", "10 min", "15 min", "30 min", "1 h"]
    L4 = line_layers(f"{sid} arrival", isop, ilabs, ISO_COL, widths={k: 0.9 for k in ilabs})
    for l in L4: label(l, field="label", size=8, placement="line", bold=True, color="#111111", all_labels=False)
    export(f"{sid} variant4 town", f"{sid}: hazard class with arrival isochrones coloured by time", over + L4 + [haz], over + [haz] + L4, "town", rows, subtitle=sub)
    for l in L4: prj.removeMapLayer(l.id())
    prj.write()

POP = BASE + "Hydraulic/Flood Protection/Risk/Data/Population/GHS POP 2025 Majlas.tif"
MAGMA_R = [(0, "#fcfdbf"), (2, "#fec98d"), (5, "#fd9668"), (10, "#f1605d"), (25, "#cd4071"), (50, "#9e2f7f"), (100, "#721f81"), (200, "#440f76"), (400, "#180f3e")]

def style_population(l):
    """people per 100 m cell, magma reversed (light = few, dark = many); cells with nobody are transparent (user, 2026-09-23)"""
    sh = QgsRasterShader(); r = QgsColorRampShader(); r.setColorRampType(QgsColorRampShader.Discrete)
    steps = [(0.5, QColor(252, 253, 191, 0), "none"), (5, "#fec98d", "1 - 5"), (10, "#fd9668", "5 - 10"), (25, "#f1605d", "10 - 25"),
             (50, "#cd4071", "25 - 50"), (100, "#9e2f7f", "50 - 100"), (200, "#721f81", "100 - 200"), (100000, "#440f76", "over 200")]
    r.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, c if isinstance(c, QColor) else QColor(c), lab) for v, c, lab in steps]); sh.setRasterShaderFunction(r)
    rr = QgsSingleBandPseudoColorRenderer(l.dataProvider(), 1, sh); rr.setOpacity(0.9); l.setRenderer(rr)

def flood_outline(code):
    """polygon of the flooded area (max depth > 0.3 m) at 10 m, for drawing an outline over other layers"""
    import rasterio, numpy as np
    from rasterio import features
    from rasterio.enums import Resampling
    src = RESULTS + code + "/max_depth.tif"; out = RESULTS + code + f"/flood_extent_{int(os.path.getmtime(src))}.geojson"   # versioned: QGIS keeps the loaded file locked
    if not os.path.exists(out):
        with rasterio.open(src) as r:
            full = r.read(1); full[full == r.nodata] = 0
            h5, w5 = r.height // 5, r.width // 5
            a = full[:h5 * 5, :w5 * 5].reshape(h5, 5, w5, 5).max(axis=(1, 3))          # block maximum to 10 m (read() cannot resample with max)
            tr = r.transform * r.transform.scale(5, 5)
        mask = (a > 0.3).astype("uint8")
        from shapely.geometry import shape, mapping, Polygon
        feats = []
        for g, v in features.shapes(mask, mask=mask == 1, transform=tr):
            p = shape(g)
            if p.area < 1e4: continue                                                     # islands under 1 ha
            p = Polygon(p.exterior, [i for i in p.interiors if Polygon(i).area >= 1e4])     # holes under 1 ha closed
            feats.append({"type": "Feature", "properties": {"v": int(v)}, "geometry": mapping(p)})
        json.dump({"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32640"}}, "features": feats}, open(out, "w"))
    return out

def map_population(code):
    """people at risk: the population grid in magma reversed with the flooded extent outlined"""
    from qgis.core import QgsFillSymbol
    d = RESULTS + code + "/"; s = json.load(open(d + "summary.json")); c = json.load(open(d + "consequences.json")) if os.path.exists(d + "consequences.json") else {}
    label = s.get("plan_title", code); sid = label.split()[0]
    pop = raster("People per 100 m cell (GHS-POP 2025)", POP); style_population(pop)
    ext = vector(f"{sid} flooded area (depth over 0.3 m)", flood_outline(code), QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#1f4e9c", "outline_width": "0.7"}))
    axis = vector("Straight dam axis (indicative)", GIS + "dam_axis_straight_indicative.shp", QgsLineSymbol.createSimple({"color": "#000000", "width": "1.4"}))
    dikes = vector("Training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Dykes.shp", QgsLineSymbol.createSimple({"color": "#eb6834", "width": "0.9"}))
    over = [axis] if sid.split("-")[0].endswith("N") else [axis, dikes]
    rows = [["Scenario", sid], ["", label[len(sid):].strip(" ,")], ["People in flooded area", f"{c.get('par_total', 0):,.0f}"],
            ["of whom in H4 or worse", f"{c.get('par_H4plus', 0):,.0f}"], ["Plots touched", f"{c.get('plots_total', 0):,}"]]
    sub = f"{label} | Wadi Majlas Flood Protection Dam, Dam Break Analysis | Renardet S.A. & Partners, 2026"
    export(f"{sid} population town", f"{sid}: people in the flooded area", over + [ext, pop], over + [ext, pop], "town", rows, subtitle=sub)
    prj.write()

def label(layer, field="name", size=8, placement="line", bold=False, color="#000000", all_labels=True):
    """labels with a white halo, every feature labelled (user, 2026-09-23); all_labels=False lets QGIS drop colliding ones"""
    try:
        from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings
        from qgis.PyQt.QtGui import QFont
        s = QgsPalLayerSettings(); s.fieldName = field
        s.placement = QgsPalLayerSettings.Line if placement == "line" else QgsPalLayerSettings.AroundPoint if placement == "point" else QgsPalLayerSettings.Horizontal
        tf = QgsTextFormat(); tf.setSize(size); tf.setColor(QColor(color)); f = QFont("Arial"); f.setBold(bold); tf.setFont(f)
        b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(1.0); b.setColor(QColor(255, 255, 255)); tf.setBuffer(b); s.setFormat(tf)
        if all_labels:
            try: s.displayAll = True
            except Exception: pass
            try:
                from qgis.core import QgsLabeling
                s.placementSettings().setOverlapHandling(QgsLabeling.OverlapHandling.AllowOverlapIfRequired)
            except Exception: pass
        layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(s)); layer.triggerRepaint()
    except Exception as e: print("label:", e)

def map_hms():
    """The HEC-HMS basin model 'Basin 1 Res2': subbasins, reaches and elements, with the three elements whose hydrographs feed HEC-RAS
    highlighted (reservoir inflow at the 'Majlas Dam' junction, J11, Jsouth)."""
    from qgis.core import QgsFillSymbol, QgsMarkerSymbol, QgsRuleBasedRenderer, QgsSymbol
    subs = vector("HEC-HMS subbasins (Basin 1 Res2)", GIS + "hms_subbasins.geojson", QgsFillSymbol.createSimple({"color": "255,255,255,30", "outline_color": "#4a3aa7", "outline_width": "0.6"}))
    reaches = vector("HEC-HMS reaches", GIS + "hms_reaches.geojson", QgsLineSymbol.createSimple({"color": "#2a78d6", "width": "0.9"}))
    el = vector("HEC-HMS junctions and reservoir", GIS + "hms_elements_v2.geojson", QgsMarkerSymbol.createSimple({"name": "circle", "color": "#ffffff", "outline_color": "#0b0b0b", "size": "2.2"}))
    used = vector("Hydrographs used in HEC-RAS (Majlas Dam inflow, J11, Jsouth)", GIS + "hms_elements_v2.geojson", QgsMarkerSymbol.createSimple({"name": "circle", "color": "#e34948", "outline_color": "#7f0000", "size": "4.5"}))
    print("subset used:", used.setSubsetString('"used" = 1'), "| subset others:", el.setSubsetString('"used" = 0'))
    area = vector("2D flow area 'DS Protection' (59.4 km2)", GIS + "model_2d_area.geojson", QgsFillSymbol.createSimple({"color": "60,120,220,40", "outline_color": "#1f4e9c", "outline_width": "0.9"}))
    label(subs, "name", 7, "horizontal", color="#4a3aa7"); label(el, "name", 8, "point", all_labels=False); label(used, "name", 9, "point", bold=True, color="#7f0000")
    rows = [["Basin model", "Basin 1 Res2, HEC-HMS 4.12"], ["Subbasins", f"{subs.featureCount()}"], ["Used in HEC-RAS", "Majlas Dam (reservoir inflow), J11, Jsouth"], ["Runs", "DA PMP Res2, DA 10000yr Res2"]]
    export("HEC-HMS model", "HEC-HMS basin model 'Basin 1 Res2'", [used, el, reaches, area, subs], [used, el, reaches, subs, area], "hms", rows,
           subtitle="Red elements: hydrographs fed into HEC-RAS | Wadi Majlas Dam Break Analysis | Renardet S.A. & Partners, 2026")
    prj.write()

def map_model_extent():
    """Figure for the report: the as-built 2D area, its boundary lines and the dam connection, over the satellite image (replaces the W1
    reach map whose model extent is outdated; user, 2026-09-23)."""
    from qgis.core import QgsFillSymbol, QgsMarkerSymbol
    area = vector("2D flow area 'DS Protection' (59.4 km2)", GIS + "model_2d_area.geojson",
                  QgsFillSymbol.createSimple({"color": "60,120,220,40", "outline_color": "#1f4e9c", "outline_width": "0.9"}))
    bcl = vector("Boundary condition lines", GIS + "model_bc_lines.geojson", QgsLineSymbol.createSimple({"color": "#e34948", "width": "1.6"}))
    con = vector("Dam connection (SA/2D)", GIS + "model_dam_connection.geojson", QgsLineSymbol.createSimple({"color": "#000000", "width": "1.6"}))
    dikes = vector("Training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Dykes.shp", QgsLineSymbol.createSimple({"color": "#eb6834", "width": "0.9"}))
    label(bcl, "name", 8, "line", bold=True, color="#7f0000"); label(con, "name", 8, "line"); label(dikes, "Layer", 7, "line", color="#9c3d10"); label(area, "name", 8, "horizontal", color="#1f4e9c")
    rows = [["2D area", "59.4 km2, 35,652 cells"], ["Cell size", "10 m at the dam, median 45 m"], ["Terrain", "drone DTM 5 m + design surfaces"],
            ["Inflow lines", "Majlas Dam, J11, Jsouth"], ["Outflow lines", "Outflow Sea, Outflow 2"]]
    export("Model extent", "The HEC-RAS model: 2D area, boundary lines and dam connection", [con, bcl, dikes, area], [area, bcl, con, dikes], "reach", rows,
           subtitle="Wadi Majlas Flood Protection Dam, Dam Break Analysis | Renardet S.A. & Partners, 2026")
    prj.write()

def all_plans():
    for d in sorted(glob.glob(RESULTS + "p*/")):
        maps_for_plan(os.path.basename(d.rstrip("/")))

if __name__ == "__main__" or True:
    import sys
    codes = [a for a in getattr(sys, "argv", [])[1:] if a.startswith("p")]
    if codes:
        for c in codes: maps_for_plan(c)
