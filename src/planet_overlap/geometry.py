from pathlib import Path
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import geopandas as gpd
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

(
    " geometry.py Handles AOI (Area of Interest) loading, "
    " point detection, buffering, and preparation for"
    " Planet API requests. Supports single/multiple"
    " AOIs, points, and polygons."
)


def normalize_geometry(geom: Union[Point, Polygon], buffer_deg: float = 0.01) -> Polygon:
    """
    Normalize geometry to polygon, buffering points if needed.

    Args:
        geom: Point or Polygon geometry
        buffer_deg: Buffer size in degrees for points

    Returns:
        Polygon geometry
    """
    if isinstance(geom, Point):
        return geom.buffer(buffer_deg)
    return geom


def load_aoi(paths: List[Union[str, Path]]) -> List[Polygon]:
    (
        " Load AOIs from multiple GeoJSON files or single"
        " polygons.  Args: paths(List[str | Path]): List "
        "of GeoJSON file paths  Returns: List[Polygon]: List of "
        "polygons representing AOIs"
    )
    aois: List[Polygon] = []
    for path in paths:
        path = Path(path)
        if not path.exists():
            logger.error(f"AOI file not found: {path}")
            raise FileNotFoundError(f"AOI file not found: {path}")
        gdf = gpd.read_file(path)
        if gdf.empty:
            logger.warning(f"AOI file is empty: {path}")
            continue
        for geom in gdf.geometry:
            if isinstance(geom, (Polygon, Point)):
                aois.append(geom)
    if not aois:
        raise ValueError("No valid AOIs loaded.")
    return aois


def buffer_points(points: List[Point], buffer_deg: float = 0.01) -> List[Polygon]:
    (
        "Converts points into small polygons (buffers) "
        "for Planet requests.  Args: "
        "points (List[Point]): list of shapely Point objects. "
        "buffer_deg (float): buffer radius in degrees "
        "(default 0.01 ~1 km). "
        "Returns: List[Polygon]: buffered polygons."
    )
    buffered = [pt.buffer(buffer_deg) for pt in points]
    logger.info(
        "Buffered %d points into polygons with %.2f° radius",
        len(points),
        buffer_deg,
    )
    return buffered


def unify_aois(aois: List[Polygon]) -> Polygon:
    (
        " Merge multiple AOIs into a single polygon "
        " if needed.  Args: aois (List[Polygon]): "
        "List of polygons  Returns: Polygon: "
        "Single merged polygon"
    )
    merged = unary_union(aois)
    if isinstance(merged, Polygon):
        return merged
    # If union returns MultiPolygon, pick convex hull
    logger.warning("AOI union resulted in MultiPolygon; using convex hull")
    return merged.convex_hull
