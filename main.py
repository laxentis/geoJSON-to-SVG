import json
import svgwrite
from shapely.geometry import shape

def geojson_to_svg(geojson_file, svg_file, width=800, height=600):
    # Load GeoJSON data
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)

    # Extract bounds of all geometries in the GeoJSON to scale to SVG canvas
    all_shapes = [shape(feature["geometry"]) for feature in geojson_data["features"]]
    min_x, min_y, max_x, max_y = (
        min(shp.bounds[0] for shp in all_shapes),
        min(shp.bounds[1] for shp in all_shapes),
        max(shp.bounds[2] for shp in all_shapes),
        max(shp.bounds[3] for shp in all_shapes),
    )
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
                points = [
                    ((x - min_x) * scale, height - (y - min_y) * scale) for x, y in polygon.exterior.coords
                ]
                dwg.add(dwg.polygon(points))
        elif geom.geom_type == "MultiPolygon":
            for polygon in geom:
                for ring in [polygon] + list(polygon.interiors):
                    points = [
                        ((x - min_x) * scale, height - (y - min_y) * scale) for x, y in ring.exterior.coords
                    ]
                    dwg.add(dwg.polygon(points))
        elif geom.geom_type == "Point":
            x, y = geom.x, geom.y
            dwg.add(dwg.circle(center=((x - min_x) * scale, height - (y - min_y) * scale), r=2))
        elif geom.geom_type == "MultiPoint":
            for point in geom:
                x, y = point.x, point.y
                dwg.add(dwg.circle(center=((x - min_x) * scale, height - (y - min_y) * scale), r=2))
        elif geom.geom_type == "LineString":
            points = [
                ((x - min_x) * scale, height - (y - min_y) * scale) for x, y in geom.coords
            ]
            dwg.add(dwg.polyline(points))
        elif geom.geom_type == "MultiLineString":
            for line in geom:
                points = [
                    ((x - min_x) * scale, height - (y - min_y) * scale) for x, y in line.coords
                ]
                dwg.add(dwg.polyline(points))

    # Save SVG file
    dwg.save()

# Usage example
geojson_to_svg("input.geojson", "output.svg")
