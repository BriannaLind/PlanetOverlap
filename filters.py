"""
filters.py
Builds Planet API search filters dynamically for multiple AOIs, multiple date ranges,
cloud cover, and sun angle thresholds.
"""

from datetime import datetime
from typing import List, Tuple, Dict, Any
from shapely.geometry import Polygon, mapping


def geometry_filter(aoi: Polygon) -> Dict[str, Any]:
    """
    Convert a shapely Polygon into a Planet GeometryFilter.

    Args:
        aoi (Polygon): The area of interest.

    Returns:
        dict: GeometryFilter for Planet API.
    """
    return {"type": "GeometryFilter", "field_name": "geometry", "config": mapping(aoi)}


def date_range_filter(start: datetime, end: datetime) -> Dict[str, Any]:
    """
    Convert a start/end datetime into a Planet DateRangeFilter.

    Args:
        start (datetime): Start date.
        end (datetime): End date.

    Returns:
        dict: DateRangeFilter for Planet API.
    """
    return {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gte": start.strftime("%Y-%m-%dT00:00:00.000Z"),
            "lte": end.strftime("%Y-%m-%dT23:59:59.999Z"),
        },
    }


def cloud_cover_filter(max_cloud: float) -> Dict[str, Any]:
    """
    Filter scenes by maximum cloud cover fraction.

    Args:
        max_cloud (float): Max cloud fraction (0.0-1.0).

    Returns:
        dict: RangeFilter for cloud_cover.
    """
    return {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {"lte": max_cloud},
    }


def sun_angle_filter(min_sun_angle: float) -> Dict[str, Any]:
    """
    Filter scenes by minimum sun angle.

    Args:
        min_sun_angle (float): Minimum sun angle in degrees.

    Returns:
        dict: RangeFilter for sun elevation.
    """
    return {
        "type": "RangeFilter",
        "field_name": "sun_elevation",
        "config": {"gte": min_sun_angle},
    }


def build_filters(
    aois: List[Polygon],
    date_ranges: List[Tuple[datetime, datetime]],
    max_cloud: float = 0.5,
    min_sun_angle: float = 0.0,
) -> Dict[str, Any]:
    """
    Build a Planet API search filter combining multiple AOIs, date ranges,
    cloud cover, and sun angle constraints.

    Args:
        aois (List[Polygon]): List of AOI polygons.
        date_ranges (List[Tuple[datetime, datetime]]): List of start/end date tuples.
        max_cloud (float): Maximum cloud fraction.
        min_sun_angle (float): Minimum sun elevation in degrees.

    Returns:
        dict: Combined Planet API filter ready for pagination.
    """
    # Combine multiple AOIs with OrFilter
    if len(aois) == 1:
        geom_filter = geometry_filter(aois[0])
    else:
        geom_filter = {"type": "OrFilter", "config": [geometry_filter(a) for a in aois]}

    # Combine multiple date ranges with OrFilter
    if len(date_ranges) == 1:
        date_filter = date_range_filter(date_ranges[0][0], date_ranges[0][1])
    else:
        date_filter = {
            "type": "OrFilter",
            "config": [date_range_filter(start, end) for start, end in date_ranges],
        }

    # Combine quality filters
    quality_filters = [cloud_cover_filter(max_cloud), sun_angle_filter(min_sun_angle)]

    # Combine everything with AndFilter
    combined_filter = {
        "type": "AndFilter",
        "config": [geom_filter, date_filter] + quality_filters,
    }

    return combined_filter
