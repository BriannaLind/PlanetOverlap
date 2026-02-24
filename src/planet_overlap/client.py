# client.py

import logging
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from shapely.geometry import Polygon, mapping

from planet_overlap.filters import build_filters
from planet_overlap.geometry import load_aoi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLANET_API_URL = "https://api.planet.com/data/v1"


def get_api_key() -> str:
    """Get Planet API key from environment variable."""
    api_key = os.environ.get("PLANET_API_KEY")
    if not api_key:
        raise ValueError(
            "PLANET_API_KEY environment variable not set. "
            "Please set it: export PLANET_API_KEY=your_api_key"
        )
    return api_key


def create_session() -> requests.Session:
    """Create authenticated session for Planet API."""
    session = requests.Session()
    api_key = get_api_key()
    session.auth = (api_key, "")
    return session


def search_planet_items(
    session: requests.Session,
    geometry: Polygon,
    start_date: datetime,
    end_date: datetime,
    item_types: List[str] = None,
    max_cloud: float = 0.5,
    min_sun_angle: float = 0.0,
    limit: int = 100,
) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Search Planet API for items matching criteria.

    Args:
        session: Authenticated requests session
        geometry: AOI polygon
        start_date: Start date for search
        end_date: End date for search
        item_types: List of item types to search (e.g., ['PSScene'])
        max_cloud: Maximum cloud cover (0.0-1.0)
        min_sun_angle: Minimum sun angle in degrees
        limit: Maximum number of items to return

    Returns:
        Tuple of (properties list, geometries list, ids list)
    """
    if item_types is None:
        item_types = ["PSScene", "SkySatScene"]

    # Build the search request
    geometry_filter = {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": mapping(geometry),
    }

    date_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gte": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lte": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }

    cloud_filter = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {"lte": max_cloud},
    }

    sun_filter = {
        "type": "RangeFilter",
        "field_name": "sun_elevation",
        "config": {"gte": min_sun_angle},
    }

    combined_filter = {
        "type": "AndFilter",
        "config": [geometry_filter, date_filter, cloud_filter, sun_filter],
    }

    search_request = {
        "item_types": item_types,
        "filter": combined_filter,
    }

    try:
        response = session.post(
            f"{PLANET_API_URL}/quick-search",
            json=search_request,
            params={"_page_size": min(limit, 250)},
        )
        response.raise_for_status()
        result = response.json()

        features = result.get("features", [])
        properties = []
        geometries = []
        ids = []

        for feature in features:
            properties.append(feature.get("properties", {}))
            geometries.append(feature.get("geometry", {}))
            ids.append(feature.get("id", ""))

        logger.info(f"Found {len(features)} items for search")
        return properties, geometries, ids

    except requests.exceptions.HTTPError as e:
        logger.error(f"Planet API HTTP error: {e}")
        logger.error(f"Response: {e.response.text if e.response else 'No response'}")
        return [], [], []
    except Exception as e:
        logger.error(f"Error searching Planet API: {e}")
        return [], [], []


def prepare_filters(
    geojson_paths: List[str],
    date_ranges: List[Tuple[str, str]],
) -> Dict:
    """
    Build filters for multiple AOIs and date ranges.

    Args:
        geojson_paths: List of file paths to AOI GeoJSONs.
        date_ranges: List of (start_date, end_date) tuples
        as strings.

    Returns:
        Dictionary containing combined filters.
    """
    # Convert string dates to datetime tuples
    parsed_ranges: List[Tuple[datetime, datetime]] = [
        (
            datetime.strptime(start, "%Y-%m-%d"),
            datetime.strptime(end, "%Y-%m-%d"),
        )
        for start, end in date_ranges
    ]

    filters = build_filters(geojson_paths, parsed_ranges)

    logger.info(
        "Filters prepared for %d AOIs/date ranges",
        len(parsed_ranges),
    )

    return filters


def load_aois(geojson_paths: List[str]):
    """
    Load AOIs from GeoJSON files.

    Args:
        geojson_paths: List of AOI GeoJSON paths.

    Returns:
        List of AOI geometries.
    """
    # load_aoi expects List[str | Path]
    path_objects: List[Path] = [Path(p) for p in geojson_paths]

    aois = load_aoi(path_objects)

    logger.info("Loaded %d AOIs", len(aois))

    return aois


def run_client(
    geojson_paths: List[str],
    date_ranges: List[Tuple[str, str]],
):
    """
    Full client workflow: load AOIs, prepare filters.

    Args:
        geojson_paths: List of AOI GeoJSON paths.
        date_ranges: List of (start_date, end_date) tuples.

    Returns:
        Tuple of (filters dict, list of AOI geometries)
    """
    aois = load_aois(geojson_paths)
    filters = prepare_filters(geojson_paths, date_ranges)

    logger.info("Client run complete")

    return filters, aois
