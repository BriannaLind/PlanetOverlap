from shapely.geometry import box
from planet_overlap.geometry import generate_tiles

def test_tile_generation():
    geom = box(0, 0, 2, 2)
    tiles = generate_tiles([geom], 1.0)
    assert len(tiles) == 4
