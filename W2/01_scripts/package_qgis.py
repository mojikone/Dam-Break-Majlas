# -*- coding: utf-8 -*-
"""Build the QGIS project of the hand-over package inside QGIS (through the MCP, in steps of under a minute each):

    exec(open(r"...\package_qgis.py", encoding="utf-8").read()); step_base()
    ...; step_results(["S1D", "S1N", "S1D-W51"]); ...; step_finish()

Every layer of the package goes in, organised in groups and subgroups (user, 2026-09-24): Base map / Dam and works /
Catchments and hydrology / Model as built / Results > one subgroup per run. Styles: the report's palettes for depth, hazard class,
arrival and population; simple ramps for velocity, depth x velocity and duration. Paths are stored relative to the project file.
"""
import os, glob, json
from qgis.core import (QgsProject, QgsRasterLayer, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsLineSymbol, QgsFillSymbol, QgsMarkerSymbol,
                       QgsSingleSymbolRenderer, QgsRasterShader, QgsColorRampShader, QgsSingleBandPseudoColorRenderer, QgsPalLayerSettings,
                       QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings, QgsLayerTreeGroup)
from qgis.PyQt.QtGui import QColor, QFont

PKG = r"D:\Mojtaba\Renardet\2224 WS11\Majlas\Hydraulic\Dam Breack\Majlas Dam Break files"
L = os.path.join(PKG, "layers"); QGZ = os.path.join(L, "qgis", "Majlas Dam Break.qgz")
prj = QgsProject.instance()
ORDER = ["S1D", "S1N", "S1D-W51", "S1D-W153", "S1D-C1.44", "S1D-T3m", "S1D-T18m", "S2D", "S2D-W119", "S2D-F10000", "S3D", "S3D-F10000"]
DESC = {"S1D": "sunny-day failure, dikes in place", "S1N": "sunny-day failure, no dikes", "S2D": "flood-day (PMF) failure, dikes in place",
        "S3D": "PMF without failure, dikes in place", "S1D-W51": "sunny-day failure, breach 51 m", "S1D-W153": "sunny-day failure, breach 153 m",
        "S1D-C1.44": "sunny-day failure, weir coefficient 1.44", "S1D-T3m": "sunny-day failure, breach formed in 3 min",
        "S1D-T18m": "sunny-day failure, breach formed in 18 min", "S2D-W119": "flood-day failure, breach 119 m",
        "S2D-F10000": "flood-day failure, 10,000-year flood", "S3D-F10000": "10,000-year flood without failure"}
CRS = QgsCoordinateReferenceSystem("EPSG:32640")

# ---------------------------------------------------------------- styles (the report's palettes)
HAZ = [(1, "#0000ff", "H1 generally safe"), (2, "#00ecff", "H2 unsafe: small vehicles"), (3, "#00a504", "H3 unsafe: vehicles, children"),
       (4, "#00ff30", "H4 unsafe for people"), (5, "#fff900", "H5 unsafe; buildings damaged"), (6, "#f41f1f", "H6 unsafe; buildings fail")]
DEPTH = [(0.3, "#e0f3ff", "0 - 0.3"), (1, "#9ecae1", "0.3 - 1"), (2, "#4292c6", "1 - 2"), (5, "#08519c", "2 - 5"), (10, "#08306b", "5 - 10"), (1000, "#000033", "over 10")]
VEL = [(0.5, "#ffffcc", "0 - 0.5"), (1, "#c7e9b4", "0.5 - 1"), (2, "#7fcdbb", "1 - 2"), (4, "#41b6c4", "2 - 4"), (8, "#2c7fb8", "4 - 8"), (1000, "#253494", "over 8")]
DV = [(0.3, "#fee5d9", "0 - 0.3 (H1)"), (0.6, "#fcae91", "0.3 - 0.6"), (1, "#fb6a4a", "0.6 - 1"), (4, "#de2d26", "1 - 4"), (1000, "#a50f15", "over 4")]
DUR = [(1, "#f7fbff", "0 - 1 h"), (3, "#c6dbef", "1 - 3 h"), (6, "#6baed6", "3 - 6 h"), (12, "#2171b5", "6 - 12 h"), (24, "#08306b", "12 - 24 h"), (1000, "#000033", "over 24 h")]
ARR_FAIL = [(5 / 60, "#7f0000", "0 - 5 min"), (10 / 60, "#b30000", "5 - 10 min"), (0.25, "#e8432f", "10 - 15 min"), (0.5, "#f28e2b", "15 - 30 min"), (1.0, "#f2d13d", "30 - 60 min"), (1000, "#9ecae1", "over 1 h")]
ARR_PMF = [(1.0, "#7f0000", "0 - 1 h"), (2.0, "#b30000", "1 - 2 h"), (3.0, "#e8432f", "2 - 3 h"), (6.0, "#f28e2b", "3 - 6 h"), (12.0, "#f2d13d", "6 - 12 h"), (1000, "#9ecae1", "over 12 h")]
POP = [(0.5, QColor(252, 253, 191, 0), "none"), (5, "#fec98d", "1 - 5"), (10, "#fd9668", "5 - 10"), (25, "#f1605d", "10 - 25"), (50, "#cd4071", "25 - 50"), (100, "#9e2f7f", "50 - 100"), (200, "#721f81", "100 - 200"), (400, "#440f76", "200 - 400"), (100000, "#180f3e", "over 400")]

def discrete(layer, steps, opacity=0.85):
    sh = QgsRasterShader(); r = QgsColorRampShader(); r.setColorRampType(QgsColorRampShader.Discrete)
    r.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, c if isinstance(c, QColor) else QColor(c), lab) for v, c, lab in steps]); sh.setRasterShaderFunction(r)
    rr = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, sh); rr.setOpacity(opacity); layer.setRenderer(rr)

def add_raster(group, name, path, steps=None, opacity=0.85, visible=True):
    if not os.path.exists(path): print("missing", path); return None
    l = QgsRasterLayer(path, name); l.setCrs(CRS)
    if steps: discrete(l, steps, opacity)
    prj.addMapLayer(l, False); node = group.addLayer(l); node.setItemVisibilityChecked(visible); return l

def add_vector(group, name, path, symbol, label=None, visible=True):
    if not os.path.exists(path): print("missing", path); return None
    l = QgsVectorLayer(path, name, "ogr")
    if not l.isValid(): print("invalid", path); return None
    if l.crs().authid() != "EPSG:32640": l.setCrs(CRS)
    l.setRenderer(QgsSingleSymbolRenderer(symbol))
    if label:
        s = QgsPalLayerSettings(); s.fieldName = label; s.placement = QgsPalLayerSettings.Line if l.geometryType() == 1 else QgsPalLayerSettings.AroundPoint
        tf = QgsTextFormat(); tf.setSize(8); f = QFont("Arial"); tf.setFont(f); b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(1.0); b.setColor(QColor(255, 255, 255)); tf.setBuffer(b); s.setFormat(tf)
        l.setLabelsEnabled(True); l.setLabeling(QgsVectorLayerSimpleLabeling(s))
    prj.addMapLayer(l, False); node = group.addLayer(l); node.setItemVisibilityChecked(visible); return l

def line(color, width=0.6, style="solid"): return QgsLineSymbol.createSimple({"color": color, "width": str(width), "line_style": style})
def outline(color, width=0.6, style="solid"): return QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": color, "outline_width": str(width), "outline_style": style})
def fill(color, outline_color="#555555"): return QgsFillSymbol.createSimple({"color": color, "outline_color": outline_color, "outline_width": "0.2"})
def point(color, size=2.5): return QgsMarkerSymbol.createSimple({"color": color, "outline_color": "#ffffff", "size": str(size)})

def group(name, parent=None):
    parent = parent or prj.layerTreeRoot(); g = parent.findGroup(name); return g or parent.addGroup(name)

# ---------------------------------------------------------------- steps
def step_base():
    prj.clear(); prj.setCrs(CRS); prj.setTitle("Wadi Majlas Dam Break Analysis: layers and results (Rev 01)")
    prj.writeEntry("Paths", "/Absolute", False)
    root = prj.layerTreeRoot()
    # base map
    g = group("Base map")
    bm = QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D{x}%26y%3D{y}%26z%3D{z}&zmax=20&zmin=0", "Google Satellite", "wms")
    if bm.isValid(): prj.addMapLayer(bm, False); g.addLayer(bm)
    # dam and works
    g = group("Dam and works")
    add_vector(g, "Dam axis, straight (design review, indicative)", os.path.join(L, "shp", "Dam axis straight (indicative).shp"), line("#000000", 1.4))
    add_vector(g, "Dam axis, original arch", os.path.join(L, "shp", "Dam axis original arch.shp"), line("#7f7f7f", 0.8, "dash"), visible=False)
    add_vector(g, "Training dikes (200-yr design)", os.path.join(L, "shp", "Training dikes.shp"), line("#eb6834", 0.9))
    add_vector(g, "Project outline", os.path.join(L, "shp", "Project outline.shp"), outline("#333333", 0.5, "dash"), visible=False)
    # catchments and hydrology
    g = group("Catchments and hydrology")
    for f in sorted(glob.glob(os.path.join(L, "shp", "hydrology", "*.shp"))):
        nm = os.path.splitext(os.path.basename(f))[0]; low = nm.lower()
        sym = line("#2a78d6", 0.5) if "stream" in low else outline("#1f5c99", 0.8)
        add_vector(g, nm, f, sym, visible=False)
    add_vector(g, "HEC-HMS sub-basins", os.path.join(L, "gis", "hms_subbasins.geojson"), outline("#4a3aa7", 0.5), visible=False)
    add_vector(g, "HEC-HMS reaches", os.path.join(L, "gis", "hms_reaches.geojson"), line("#4a3aa7", 0.8), visible=False)
    add_vector(g, "HEC-HMS elements (hydrograph points)", os.path.join(L, "gis", "hms_elements_v2.geojson"), point("#eb6834"), label="name", visible=False)
    # model as built
    g = group("Model as built")
    add_vector(g, "2D flow area", os.path.join(L, "gis", "model_2d_area.geojson"), outline("#1f5c99", 1.0))
    add_vector(g, "Boundary condition lines", os.path.join(L, "gis", "model_bc_lines.geojson"), line("#e34948", 1.2), label="name")
    add_vector(g, "Dam connection (weir with breach)", os.path.join(L, "gis", "model_dam_connection.geojson"), line("#000000", 1.6))
    add_vector(g, "Places", os.path.join(L, "gis", "places.shp"), point("#333333", 2.0), label="name", visible=False)
    add_vector(g, "Model extents (earlier study)", os.path.join(L, "gis", "model_extents.shp"), outline("#7f7f7f", 0.5, "dot"), visible=False)
    add_vector(g, "Land-use plots, Qurayat", os.path.join(L, "shp", "Land use plots Qurayat.shp"), fill("#f2d13d", "#8a6d00"), visible=False)
    add_raster(g, "Population, GHS-POP 2025 (people per 100 m cell)", os.path.join(L, "rasters", "base", "GHS-POP 2025 population (100 m).tif"), POP, 0.9, visible=False)
    add_raster(g, "Terrain, 5 m (m a.s.l.)", os.path.join(L, "terrain", "Majlas Terrain Dam Break.tif"), None, 1.0, visible=False)
    group("Results")
    prj.write(QGZ); return f"base: {len(prj.mapLayers())} layers"

def step_results(sids):
    res = group("Results")
    for sid in sids:
        d = os.path.join(L, "rasters", sid); g = group(f"{sid}: {DESC[sid]}", res)
        pmf = sid.startswith("S3")
        add_vector(g, f"{sid} flooded area (> 0.3 m)", os.path.join(d, "flood_extent.geojson"), outline("#000000", 0.6), visible=False)
        if os.path.exists(os.path.join(d, "isochrones.geojson")):
            add_vector(g, f"{sid} arrival isochrones", os.path.join(d, "isochrones.geojson"), line("#111111", 0.7), label="label", visible=False)
        if os.path.exists(os.path.join(d, "hazard_lines.geojson")):
            add_vector(g, f"{sid} hazard boundaries H4 and H6", os.path.join(d, "hazard_lines.geojson"), line("#ffffff", 0.7), label="label", visible=False)
        add_raster(g, f"{sid} hazard class (AIDR H1-H6)", os.path.join(d, "hazard_aidr.tif"), HAZ, 0.85, visible=(sid in ("S1D",)))
        add_raster(g, f"{sid} arrival of a 0.3 m rise ({'h after the storm starts' if pmf else 'h after the breach'})", os.path.join(d, "warning_arrival_h.tif"), ARR_PMF if pmf else ARR_FAIL, 0.85, visible=False)
        add_raster(g, f"{sid} arrival of 0.3 m depth (h)", os.path.join(d, "arrival_h.tif"), ARR_PMF if pmf else ARR_FAIL, 0.85, visible=False)
        add_raster(g, f"{sid} maximum depth (m)", os.path.join(d, "max_depth.tif"), DEPTH, 0.85, visible=False)
        add_raster(g, f"{sid} maximum velocity (m/s)", os.path.join(d, "max_velocity.tif"), VEL, 0.85, visible=False)
        add_raster(g, f"{sid} maximum depth x velocity (m2/s)", os.path.join(d, "max_dv.tif"), DV, 0.85, visible=False)
        add_raster(g, f"{sid} duration above 0.3 m (h)", os.path.join(d, "duration_h.tif"), DUR, 0.85, visible=False)
        g.setExpanded(False)
    prj.write(QGZ); return f"results {sids}: {len(prj.mapLayers())} layers"

def step_finish():
    root = prj.layerTreeRoot()
    for g in root.children():
        if isinstance(g, QgsLayerTreeGroup) and g.name() != "Results": g.setExpanded(True)
    prj.write(QGZ)
    n = len(prj.mapLayers()); return f"saved {QGZ}: {n} layers, {len(root.findGroups())} top groups"
