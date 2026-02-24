from planet_overlap.utils import estimate_scenes_by_area, should_tile


def test_scene_estimation():
    area_km2 = 5000
    scenes_per_km2 = 0.5
    count = estimate_scenes_by_area(area_km2, scenes_per_km2)
    assert count == 2500


def test_temporal_tiling_trigger():
    # Should tile if scenes exceed threshold
    assert should_tile(2500, 2000) is True
    assert should_tile(1500, 2000) is False
