from shapely.geometry import Polygon
import geopandas as gpd
import numpy as np
from typing import List, Dict, Any, Tuple


# Reusable functions
def filter_quality(
    properties: List[Dict[str, Any]],
    geometries: List[Dict[str, Any]],
    ids: List[str],
    min_points: int = 5,
    min_view_angle: float = 3,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Filter out scenes with insufficient points or bad quality."""
    index_sub = [
        i
        for i, prop in enumerate(properties)
        if prop.get("ground_control", False)
        and prop.get("quality_category", "") == "standard"
        and prop.get("view_angle", 0) < min_view_angle
        and len(geometries[i]["coordinates"][0]) >= min_points
    ]

    return (
        [properties[i] for i in index_sub],
        [geometries[i] for i in index_sub],
        [ids[i] for i in index_sub],
    )


def compute_central_coordinates(
    geometries: List[Dict[str, Any]]
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute central latitude and longitude for each polygon."""
    central_lon = np.array(
        [np.mean([pt[0] for pt in geom["coordinates"][0]]) for geom in geometries]
    )
    central_lat = np.array(
        [np.mean([pt[1] for pt in geom["coordinates"][0]]) for geom in geometries]
    )
    return central_lon, central_lat


def compute_local_times(
    properties: List[Dict[str, Any]], central_lon: np.ndarray
) -> np.ndarray:
    """Compute local times from UTC and central longitude."""
    hours = np.array(
        [
            int(p["acquired"].split("T")[1].split("Z")[0].split(":")[0])
            for p in properties
        ]
    )
    minutes = np.array(
        [
            int(p["acquired"].split("T")[1].split("Z")[0].split(":")[1])
            for p in properties
        ]
    )
    seconds = np.array(
        [
            float(p["acquired"].split("T")[1].split("Z")[0].split(":")[2])
            for p in properties
        ]
    )
    utc_times = hours + minutes / 60 + seconds / 3600
    local_times = utc_times + central_lon / 15
    return local_times


def geometries_to_polygons(geometries: List[Dict[str, Any]]) -> List[Polygon]:
    """Convert GeoJSON geometries to Shapely Polygons."""
    return [Polygon(sub["coordinates"][0]) for sub in geometries]


def calculate_intersections(
    polygons: List[Polygon],
    properties: List[Dict[str, Any]],
    min_sun_angle: float = 0,
    area_threshold: float = 25.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute pairwise intersected areas and sun angle differences between polygons.
    Only compares polygons from the same instrument and different satellites.
    """
    n = len(polygons)
    area_2d = np.zeros((n, n), dtype=np.float32)
    sun_diff_2d = np.zeros((n, n), dtype=np.float32)
    sun_angles = np.array([90 - p["sun_elevation"] for p in properties])
    instruments = [p["instrument"] for p in properties]
    satellite_ids = [p["satellite_id"] for p in properties]

    for i in range(n):
        for j in range(i + 1, n):
            if (
                instruments[i] == instruments[j]
                and satellite_ids[i] != satellite_ids[j]
            ):
                if (
                    polygons[i].bounds[2] >= polygons[j].bounds[0]
                    and polygons[i].bounds[3] >= polygons[j].bounds[1]
                ):
                    intersection = polygons[i].intersection(polygons[j])
                    if intersection.area > 0:
                        area_2d[i, j] = intersection.area
                        area_2d[j, i] = area_2d[i, j]
                        sun_diff_2d[i, j] = abs(sun_angles[i] - sun_angles[j])
                        sun_diff_2d[j, i] = sun_diff_2d[i, j]
    return area_2d, sun_diff_2d


def process_tiles(
    all_properties: List[List[Dict[str, Any]]],
    all_geometries: List[List[Dict[str, Any]]],
    all_ids: List[List[str]],
    min_view_angle: float = 3,
    min_sun_angle: float = 0,
) -> gpd.GeoDataFrame:
    """
    Process multiple tiles/datasets and return a unified GeoDataFrame.
    """
    merged_properties = []
    merged_geometries = []
    merged_ids = []

    # Step 1: Filter and merge tiles
    for props, geoms, ids in zip(all_properties, all_geometries, all_ids):
        f_props, f_geoms, f_ids = filter_quality(
            props, geoms, ids, min_view_angle=min_view_angle
        )
        merged_properties.extend(f_props)
        merged_geometries.extend(f_geoms)
        merged_ids.extend(f_ids)

    # Step 2: Compute central coordinates and local times
    central_lon, central_lat = compute_central_coordinates(merged_geometries)
    local_times = compute_local_times(merged_properties, central_lon)

    # Step 3: Convert to Shapely Polygons
    polygons = geometries_to_polygons(merged_geometries)

    # Step 4: Compute intersections and sun differences
    area_2d, sun_diff_2d = calculate_intersections(
        polygons, merged_properties, min_sun_angle=min_sun_angle
    )

    # Step 5: Create GeoDataFrame
    gdf = gpd.GeoDataFrame(
        {
            "id": list(range(len(merged_ids))),
            "name": merged_ids,
            "geometry": polygons,
            "view_angle": [p["view_angle"] for p in merged_properties],
            "acquired": [p["acquired"] for p in merged_properties],
            "cloud_cover": [p["cloud_cover"] for p in merged_properties],
            "sun_elevation": [p["sun_elevation"] for p in merged_properties],
            "sun_angle": [90 - p["sun_elevation"] for p in merged_properties],
            "satellite_id": [p["satellite_id"] for p in merged_properties],
            "central_lon": central_lon,
            "central_lat": central_lat,
            "local_times": local_times,
            "max_sun_diff": [sun_diff_2d[i, :].max() for i in range(len(polygons))],
        }
    )
    gdf.set_index("id", inplace=True)
    return gdf
