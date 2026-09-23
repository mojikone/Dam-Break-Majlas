# -*- coding: utf-8 -*-
"""Build the W1 map figures inside QGIS (run through the QGIS MCP execute_code or the Python console).

Loads the study layers once, styles them, clones the client-approved layout template
(Data/QGIS/QGIS layout template.qpt) once per figure, fills title / legend / information
table, and exports PNGs to W1/02_figures/maps/. Layouts stay in the project so they can be
re-exported by hand later (Majlas_DamBreak_W1.qgz).
"""
import os
from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer, QgsPrintLayout, QgsReadWriteContext,
                       QgsLayoutItemMap, QgsLayoutItemLegend, QgsLayoutItemLabel, QgsLayoutFrame,
                       QgsLayoutItemManualTable, QgsTableCell, QgsLayoutExporter, QgsRectangle,
                       QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsSingleSymbolRenderer,
                       QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsHillshadeRenderer,
                       QgsSingleBandPseudoColorRenderer, QgsColorRampShader, QgsRasterShader,
                       QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling, QgsLegendStyle,
                       QgsLayerTreeLayer, QgsLegendRenderer, QgsTextBufferSettings, QgsUnitTypes,
                       QgsLayoutItemScaleBar, QgsLayoutPoint, QgsLayoutSize)
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtGui import QColor, QFont

BASE = "D:/Mojtaba/Renardet/2224 WS11/Majlas/"
W1 = BASE + "Hydraulic/Dam Breack/W1/"
GIS = W1 + "04_data/gis/"
OUT = W1 + "02_figures/maps/"
TPL = BASE + "Hydraulic/Dam Breack/Data/QGIS/QGIS layout template.qpt"
os.makedirs(OUT, exist_ok=True)
prj = QgsProject.instance()

SUBTITLE = "Wadi Majlas Flood Protection Dam - Dam Break Analysis Methodology | Renardet S.A. & Partners, 2026"

# ------------------------------------------------------------------ layers
LAYERS = {
    "catch":    ("Wadi Majlas catchment to the dam (571 km2)", BASE + "Hydrology/SHP/Majlas Catchment only.shp", "v"),
    "haifaz":   ("Haifaz dam catchment (40 km2)", BASE + "Hydrology/SHP/Basin Haifaz.shp", "v"),
    "streams":  ("Wadi network (Strahler order 4 and above)", BASE + "Hydrology/SHP/Streams NSA 5m.shp", "v"),
    "res":      ("Reservoir at full supply level (indicative)", BASE + "Hydrology/SHP/Majlas Reservoir.shp", "v"),
    "axis_old": ("Original arch dam axis", BASE + "Hydraulic/Dam Breack/Data/SHP/Dam Axis.shp", "v"),
    "axis_new": ("Straight dam axis, design review 2026 (indicative)", GIS + "dam_axis_straight_indicative.shp", "v"),
    "dikes":    ("Downstream training dikes (200-yr design)", BASE + "Hydraulic/Flood Protection/SHP/CH Dykes Majlas.shp", "v"),
    "outline":  ("Downstream protection works outline", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Project Outline.shp", "v"),
    "lu":       ("Use of the plot", BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Landuse Majlas Clip.shp", "v"),
    "pop":      ("People per 100 m cell (GHS-POP 2025)", BASE + "Hydraulic/Flood Protection/Risk/Data/Population/GHS POP 2025 Majlas.tif", "r"),
    "model":    ("Model extents", GIS + "model_extents.shp", "v"),
    "data":     ("Terrain and data coverage", GIS + "data_extents.shp", "v"),
    "places":   ("Town", GIS + "places.shp", "v"),
    "dtm":      ("Hillshade of the NSA 5 m terrain (downstream reach)", BASE + "Hydraulic/Flood Protection/Terrain/NSA 5m Majlas DS.tif", "r"),
}

def get_layer(key):
    name, path, kind = LAYERS[key]
    for l in prj.mapLayers().values():
        if l.name() == name:
            return l
    if kind == "v":
        l = QgsVectorLayer(path, name, "ogr")
    else:
        l = QgsRasterLayer(path, name)
    if not l.isValid():
        raise RuntimeError("invalid layer " + path)
    prj.addMapLayer(l)
    return l

def sat():
    for l in prj.mapLayers().values():
        if "Google Satellite" in l.name():
            return l
    return None

def line(color, width, style="solid"):
    s = QgsLineSymbol.createSimple({"color": color, "width": str(width), "line_style": style, "capstyle": "round"})
    return s

def fill(color, outline, ow=0.4, style="solid"):
    return QgsFillSymbol.createSimple({"color": color, "outline_color": outline, "outline_width": str(ow), "style": style, "outline_style": "solid"})

def style_layers():
    L = {k: get_layer(k) for k in LAYERS}
    L["catch"].setRenderer(QgsSingleSymbolRenderer(fill("0,0,0,0", "#eda100", 0.9)))
    L["haifaz"].setRenderer(QgsSingleSymbolRenderer(fill("0,0,0,0", "#1baf7a", 0.9)))
    L["streams"].setRenderer(QgsSingleSymbolRenderer(line("#2a78d6", 0.35)))
    L["streams"].setSubsetString('"StrahlerID" >= 4')
    L["res"].setRenderer(QgsSingleSymbolRenderer(fill("42,120,214,120", "#1c5cab", 0.5)))
    L["axis_old"].setRenderer(QgsSingleSymbolRenderer(line("#e87ba4", 0.9, "dash")))
    L["axis_new"].setRenderer(QgsSingleSymbolRenderer(line("#e34948", 1.6)))
    L["dikes"].setRenderer(QgsSingleSymbolRenderer(line("#eb6834", 1.1)))
    L["outline"].setRenderer(QgsSingleSymbolRenderer(fill("0,0,0,0", "#eb6834", 0.6, "solid")))
    # land use categorised
    cats = []
    for val, col, lab in [("Residential", "#e87ba4", "Residential"), ("Commercial", "#eda100", "Commercial"),
                          ("Industry", "#4a3aa7", "Industrial"), ("Agriculture", "#1baf7a", "Agricultural")]:
        cats.append(QgsRendererCategory(val, fill(col, "#404040", 0.1), lab))
    L["lu"].setRenderer(QgsCategorizedSymbolRenderer("NewLUClass", cats))
    # model extents categorised by Area (two features)
    cats = [QgsRendererCategory("Existing downstream 2D flow area (DS Protection, 12,680 cells)", fill("235,104,52,60", "#eb6834", 0.8), "Existing HEC-RAS 2D area (downstream, 12,680 cells)"),
            QgsRendererCategory("Proposed dam-break model extent (reservoir 2D area + downstream 2D area)", fill("0,0,0,0", "#e34948", 1.2), "Proposed dam-break model extent")]
    L["model"].setRenderer(QgsCategorizedSymbolRenderer("Area", cats))
    cats = [QgsRendererCategory("NSA 2 m DSM (national)", fill("0,0,0,0", "#4a3aa7", 0.8, "solid"), "NSA 2 m DSM (national, whole area)"),
            QgsRendererCategory("NSA 5 m DTM - existing downstream HEC-RAS model", fill("0,0,0,0", "#eb6834", 1.0), "NSA 5 m DTM used by the existing downstream model"),
            QgsRendererCategory("GHS-POP 2025 population grid (100 m)", fill("0,0,0,0", "#1baf7a", 0.8), "GHS-POP 2025 population grid (100 m)")]
    L["data"].setRenderer(QgsCategorizedSymbolRenderer("Dataset", cats))
    L["places"].setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#0b0b0b", "outline_color": "white", "size": "2.6"})))
    # labels for places
    pal = QgsPalLayerSettings(); pal.fieldName = "Name"; pal.enabled = True
    tf = QgsTextFormat(); tf.setFont(QFont("Arial")); tf.setSize(10); tf.setColor(QColor("#0b0b0b"))
    buf = QgsTextBufferSettings(); buf.setEnabled(True); buf.setSize(1.0); buf.setColor(QColor("white")); tf.setBuffer(buf)
    pal.setFormat(tf); pal.placement = QgsPalLayerSettings.OrderedPositionsAroundPoint
    L["places"].setLabelsEnabled(True); L["places"].setLabeling(QgsVectorLayerSimpleLabeling(pal))
    # population pseudocolour
    shader = QgsRasterShader(); ramp = QgsColorRampShader(); ramp.setColorRampType(QgsColorRampShader.Discrete)
    items = [QgsColorRampShader.ColorRampItem(1, QColor(0, 0, 0, 0), "under 1 (not shown)"),
             QgsColorRampShader.ColorRampItem(5, QColor("#cde2fb"), "1 to 5"),
             QgsColorRampShader.ColorRampItem(20, QColor("#86b6ef"), "5 to 20"),
             QgsColorRampShader.ColorRampItem(50, QColor("#3987e5"), "20 to 50"),
             QgsColorRampShader.ColorRampItem(100, QColor("#1c5cab"), "50 to 100"),
             QgsColorRampShader.ColorRampItem(10000, QColor("#0d366b"), "over 100")]
    ramp.setColorRampItemList(items); shader.setRasterShaderFunction(ramp)
    r = QgsSingleBandPseudoColorRenderer(L["pop"].dataProvider(), 1, shader); r.setOpacity(0.75)
    L["pop"].setRenderer(r)
    # hillshade
    hs = QgsHillshadeRenderer(L["dtm"].dataProvider(), 1, 315, 40); hs.setZFactor(1.5); hs.setOpacity(0.55)
    L["dtm"].setRenderer(hs)
    for l in L.values():
        l.triggerRepaint()
    return L

# ------------------------------------------------------------------ layouts
def load_template(name):
    mgr = prj.layoutManager()
    for l in list(mgr.printLayouts()):
        if l.name() == name:
            mgr.removeLayout(l)
    doc = QDomDocument()
    with open(TPL, "r", encoding="utf-8") as f:
        doc.setContent(f.read())
    lay = QgsPrintLayout(prj); lay.initializeDefaults()
    lay.loadFromTemplate(doc, QgsReadWriteContext())
    lay.setName(name); mgr.addLayout(lay)
    return lay

def items_of(lay):
    out = {"labels": [], "map": None, "legend": None, "table": None, "frame": None, "scalebar": None}
    for it in lay.items():
        if isinstance(it, QgsLayoutItemMap): out["map"] = it
        elif isinstance(it, QgsLayoutItemLegend): out["legend"] = it
        elif isinstance(it, QgsLayoutItemLabel): out["labels"].append(it)
        elif isinstance(it, QgsLayoutItemScaleBar): out["scalebar"] = it
        elif isinstance(it, QgsLayoutFrame) and isinstance(it.multiFrame(), QgsLayoutItemManualTable):
            out["table"] = it.multiFrame(); out["frame"] = it
    # labels: the 15 pt bold one is the title, 9 pt is the subtitle
    out["title"] = [l for l in out["labels"] if l.textFormat().size() >= 14][0]
    out["subtitle"] = [l for l in out["labels"] if 8 <= l.textFormat().size() < 10][0]
    return out

def fit_extent(m, xmin, ymin, xmax, ymax):
    """Extent centred on the box, expanded to the map item's aspect ratio."""
    w_mm, h_mm = m.sizeWithUnits().width(), m.sizeWithUnits().height()
    ar = w_mm / h_mm
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    w, h = xmax - xmin, ymax - ymin
    if w / h < ar: w = h * ar
    else: h = w / ar
    m.setExtent(QgsRectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))

def build_map(name, title, layer_keys, extent, scale, table_rows, legend_keys=None, hide_title_for=()):
    L = {k: get_layer(k) for k in LAYERS}
    lay = load_template(name)
    it = items_of(lay)
    it["title"].setText(title); it["subtitle"].setText(SUBTITLE)
    m = it["map"]
    layers = [L[k] for k in layer_keys]
    s = sat()
    if s is not None: layers.append(s)
    m.setLayers(layers); m.setKeepLayerSet(True)
    fit_extent(m, *extent)
    if scale: m.setScale(scale)
    # legend: only this map's layers
    lg = it["legend"]; lg.setAutoUpdateModel(False)
    root = lg.model().rootGroup(); root.removeAllChildren()
    for k in (legend_keys or layer_keys):
        node = root.addLayer(L[k])
        if k in hide_title_for:
            QgsLegendRenderer.setNodeLegendStyle(node, QgsLegendStyle.Hidden)
    lg.setLinkedMap(m); lg.updateLegend(); lg.adjustBoxSize()
    # information table: widen the frame so the second column is not clipped at the page edge
    tbl = it["table"]
    tbl.setTableContents([[QgsTableCell(a), QgsTableCell(b)] for a, b in table_rows])
    tbl.setColumnWidths([34.0, 30.0])
    fr = it["frame"]
    fr.attemptMove(QgsLayoutPoint(224.0, 160.0, QgsUnitTypes.LayoutMillimeters))
    fr.attemptResize(QgsLayoutSize(64.0, 42.0, QgsUnitTypes.LayoutMillimeters))
    # scale bar: two segments sized to the map scale (about 15-20 mm each)
    sb = it["scalebar"]
    if sb is not None:
        sb.setLinkedMap(m); sb.setNumberOfSegments(2); sb.setNumberOfSegmentsLeft(0)
        sb.setUnitsPerSegment({200000: 5.0, 60000: 1.0, 30000: 0.5}.get(scale, max(0.5, round(scale / 60000.0, 1))))
        sb.update()
    lay.refresh()
    exp = QgsLayoutExporter(lay)
    st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 250
    res = exp.exportToImage(OUT + name + ".png", st)
    print(name, "export", res, "scale 1:%d" % round(m.scale()))
    return lay

def build_all():
    style_layers()
    # Map 1: location, catchments, reach to Qurayat
    build_map("Map 01 Location and catchments",
              "Wadi Majlas dam: catchments, reservoir and the reach to Qurayat",
              ["places", "axis_new", "res", "outline", "haifaz", "catch", "streams"],
              (645000, 2555400, 702000, 2594100), 200000,
              [["Catchment to the dam", "571 km2"], ["Haifaz catchment", "40 km2"], ["Reservoir at FSL 84.5 m", "102.2 Mm3"],
               ["Dam to Qurayat town", "about 2 km"], ["Dam height above bed", "72.5 m"]],
              hide_title_for=())
    # Map 2: study reach and model extents
    build_map("Map 02 Study reach and model extent",
              "Study reach: existing HEC-RAS 2D area and proposed dam-break model extent",
              ["places", "axis_new", "axis_old", "dikes", "model", "res", "streams"],
              (681500, 2568150, 698500, 2579650), 60000,
              [["Existing 2D area (downstream)", "15.7 km2"], ["Existing mesh", "12,680 cells"], ["Proposed model extent", "about 27 km2"],
               ["Reservoir 2D area", "to be added"], ["Downstream limit", "the Gulf of Oman"]],
              hide_title_for=("model",))
    # Map 3: terrain and data coverage
    build_map("Map 03 Terrain and data coverage",
              "Terrain in hand: NSA 5 m terrain of the existing downstream model",
              ["places", "axis_new", "res", "data", "dtm"],
              (681500, 2568150, 698500, 2579650), 60000,
              [["NSA DSM, national", "2 m and 5 m"], ["Downstream model terrain", "NSA 5 m"], ["Dam and reservoir DTM", "2 m (design review)"],
               ["Dam site survey", "5 cm (design review)"], ["Population grid", "GHS-POP 2025, 100 m"]],
              legend_keys=["axis_new", "res", "data", "dtm"], hide_title_for=("data",))
    # legend of Map 03: only the terrain box that is inside the view
    L = {k: get_layer(k) for k in ("data",)}
    r = L["data"].renderer()
    for i, c in enumerate(r.categories()):
        r.updateCategoryRenderState(i, "5 m" in str(c.value()))
    L["data"].triggerRepaint()
    lay3 = prj.layoutManager().layoutByName("Map 03 Terrain and data coverage")
    it3 = items_of(lay3); it3["legend"].updateLegend(); it3["legend"].adjustBoxSize(); lay3.refresh()
    st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 250
    QgsLayoutExporter(lay3).exportToImage(OUT + "Map 03 Terrain and data coverage.png", st)
    # Map 4: population and land use downstream
    build_map("Map 04 Population and land use at Qurayat",
              "Qurayat below the dam: use of each plot, population grid and protection works",
              ["places", "axis_new", "dikes", "outline", "lu", "pop", "streams"],
              (690000, 2571200, 698000, 2576600), 30000,
              [["Residential plots", "2,598"], ["Commercial plots", "265"], ["Agricultural plots", "1,043"],
               ["Industrial plots", "5"], ["Population grid", "GHS-POP 2025"]],
              legend_keys=["axis_new", "dikes", "outline", "lu", "pop"], hide_title_for=("lu",))
    prj.write()
    print("saved project", prj.fileName())

if __name__ == "__main__" or True:
    build_all()
