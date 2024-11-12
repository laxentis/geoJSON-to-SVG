import json

import dearpygui.dearpygui as dpg
import svgwrite
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform


def geojson_to_svg(geojson_file, svg_file, width=800, height=600, src_crs="EPSG:4326", tgt_crs="EPSG:3857"):
    # Create a transformer for CRS conversion
    transformer = Transformer.from_crs(src_crs, tgt_crs, always_xy=True)

    # Load GeoJSON data
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)

    # Convert geometries to target CRS
    all_shapes = []
    for feature in geojson_data["features"]:
        geom = shape(feature["geometry"])
        transformed_geom = transform(transformer.transform, geom)
        all_shapes.append(transformed_geom)
        feature["geometry"] = mapping(transformed_geom)  # Update GeoJSON geometry with transformed coordinates

    # Extract bounds of all transformed geometries
    min_x, min_y, max_x, max_y = (min(shp.bounds[0] for shp in all_shapes), min(shp.bounds[1] for shp in all_shapes),
                                  max(shp.bounds[2] for shp in all_shapes), max(shp.bounds[3] for shp in all_shapes),)
    x_scale = width / (max_x - min_x)
    y_scale = height / (max_y - min_y)
    scale = min(x_scale, y_scale)  # uniform scaling for both axes

    # Create SVG file
    dwg = svgwrite.Drawing(svg_file, size=(width, height))
    for feature in geojson_data["features"]:
        geom = shape(feature["geometry"])

        # Convert geometries to SVG path commands
        if geom.geom_type == "Polygon":
            for polygon in [geom] + list(geom.interiors):
                points = [((x - min_x) * scale, height - (y - min_y) * scale) for x, y in polygon.exterior.coords]
                dwg.add(dwg.polygon(points))
        elif geom.geom_type == "MultiPolygon":
            for polygon in geom:
                for ring in [polygon] + list(polygon.interiors):
                    points = [((x - min_x) * scale, height - (y - min_y) * scale) for x, y in ring.exterior.coords]
                    dwg.add(dwg.polygon(points))
        elif geom.geom_type == "Point":
            x, y = geom.x, geom.y
            dwg.add(dwg.circle(center=((x - min_x) * scale, height - (y - min_y) * scale), r=2))
        elif geom.geom_type == "MultiPoint":
            for point in geom:
                x, y = point.x, point.y
                dwg.add(dwg.circle(center=((x - min_x) * scale, height - (y - min_y) * scale), r=2))
        elif geom.geom_type == "LineString":
            points = [((x - min_x) * scale, height - (y - min_y) * scale) for x, y in geom.coords]
            dwg.add(dwg.polyline(points))
        elif geom.geom_type == "MultiLineString":
            for line in geom:
                points = [((x - min_x) * scale, height - (y - min_y) * scale) for x, y in line.coords]
                dwg.add(dwg.polyline(points))

    # Save SVG file
    dwg.save()


def converter_wrapper():
    in_file = dpg.get_value("input_file")
    out_file = dpg.get_value("output_file")
    in_crs = dpg.get_value("src_crs")
    out_crs = dpg.get_value("tgt_crs")
    w = dpg.get_value("width")
    h = dpg.get_value("height")
    geojson_to_svg(in_file, out_file, width=w, height=h, src_crs=in_crs, tgt_crs=out_crs)
    dpg.configure_item("done", show=True)

def input_file_callback(sender, app_data, user_data):
    dpg.set_value("input_file", app_data['file_path_name'])

def output_file_callback(sender, app_data_user_data):
    dpg.set_value("output_file", app_data_user_data['file_path_name'])


if __name__ == "__main__":
    dpg.create_context()
    dpg.create_viewport(title="GeoJSON to SVG converter", width=600, height=600)
    with dpg.window(tag="main_window"):
        dpg.add_input_text(label="Input CRS", default_value="EPSG:4326", tag="src_crs")
        dpg.add_input_text(label="Output CRS", default_value="EPSG:3857", tag="tgt_crs")
        dpg.add_input_int(label="Width", default_value=800, tag="width")
        dpg.add_input_int(label="Height", default_value=600, tag="height")
        with dpg.group(horizontal=True):
            dpg.add_input_text(label="Input file", default_value="input.geojson", tag="input_file")
            dpg.add_button(label="...", width=30, callback=lambda: dpg.show_item("select_in_file"))
        with dpg.group(horizontal=True):
            dpg.add_input_text(label="Output file", default_value="output.svg", tag="output_file")
            dpg.add_button(label="...", width=30, callback=lambda: dpg.show_item("select_out_file"))
        dpg.add_button(label="Convert", callback=converter_wrapper, tag="convert_button")
    with dpg.window(tag="done", modal=True, show=False, no_title_bar=True, pos=(300,200)):
        dpg.add_text("Done!")
        dpg.add_button(label="OK", callback = lambda: dpg.configure_item("done", show=False))
    with dpg.file_dialog(show=False, tag="select_in_file", width=400, height=400, callback=input_file_callback):
        dpg.add_file_extension(".geojson")
    with dpg.file_dialog(show=False, tag="select_out_file", width=400, height=400, callback=output_file_callback):
        dpg.add_file_extension(".svg")
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main_window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()
