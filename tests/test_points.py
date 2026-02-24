from datetime import datetime
from shapely.geometry import Point
from planet_overlap.geometry import normalize_geometry
from planet_overlap.pagination import tile_dates


def test_point_buffer():
    pt = Point(0, 0)
    poly = normalize_geometry(pt, 0.01)
    assert poly.geom_type == "Polygon"
    assert poly.area > 0


def test_point_no_tiling_under_3_years():
    start = datetime(2023, 1, 1)
    end = datetime(2025, 12, 30)  # Just under 3 years (1095 days)
    slices = tile_dates(start, end, is_point=True)
    assert len(slices) == 1  # Should not split under 3 years


def test_point_tiling_over_3_years():
    start = datetime(2020, 1, 1)
    end = datetime(2023, 12, 31)  # 4 years
    slices = tile_dates(start, end, is_point=True)
    assert len(slices) > 1  # Should split
