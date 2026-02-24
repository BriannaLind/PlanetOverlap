# tests/test_filters.py
from datetime import datetime
from shapely.geometry import Polygon
from planet_overlap.filters import build_filters


def test_single_geojson_and_single_date():
    """Test a single AOI with a single date."""
    aoi = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 1)
    filters = build_filters([aoi], [(start_date, end_date)])
    assert "GeometryFilter" in str(filters)
    assert "DateRangeFilter" in str(filters)


def test_multiple_geojson_and_multiple_date_ranges():
    """Test multiple AOIs with multiple date ranges."""
    aois = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
    ]
    date_ranges = [
        (datetime(2023, 1, 1), datetime(2023, 1, 15)),
        (datetime(2023, 2, 1), datetime(2023, 2, 10))
    ]
    filters = build_filters(aois, date_ranges)
    # Config includes: geom_or_filter, date_or_filter, cloud_filter, sun_filter
    assert len(filters["config"]) == 4
    assert filters["type"] == "AndFilter"


def test_mixed_single_and_range_dates():
    """Test handling of a mix of single dates and date ranges."""
    aois = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
    ]
    date_ranges = [
        (datetime(2023, 1, 1), datetime(2023, 1, 1)),  # single date as range
        (datetime(2023, 2, 1), datetime(2023, 2, 10)),
    ]
    filters = build_filters(aois, date_ranges)
    assert len(filters["config"]) == 4
    assert filters["type"] == "AndFilter"
