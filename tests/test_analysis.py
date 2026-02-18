import pytest
import numpy as np
from shapely.geometry import Polygon
from planet_overlap.analysis import compute_intersections

def test_intersection_area():
    poly1 = Polygon([(-1,0), (0,1), (1,0), (0,-1)])
    poly2 = Polygon([(0,0), (1,1), (2,0), (1,-1)])
    area_matrix = compute_intersections([poly1, poly2])
    assert area_matrix.shape == (2,2)
    assert area_matrix[0,1] > 0
    assert area_matrix[1,0] == area_matrix[0,1]
