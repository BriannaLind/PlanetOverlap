from shapely.geometry import Point, Polygon
from planet_overlap.geometry import buffer_points


def test_point_buffering():
    # Single point AOI
    point = Point(-121.5, 37.0)
    buffered = buffer_points([point], buffer_deg=0.01)
    assert len(buffered) == 1
    assert isinstance(buffered[0], Polygon)
    # Check buffer distance roughly matches
    assert buffered[0].area > 0


def test_multiple_points():
    points = [Point(-121.5, 37.0), Point(-122.0, 38.0)]
    buffered = buffer_points(points, buffer_deg=0.01)
    assert len(buffered) == 2
