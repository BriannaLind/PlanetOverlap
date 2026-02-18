import unittest
import numpy as np
from planet_overlap import analysis


class TestAnalysisMultiTile(unittest.TestCase):

    def setUp(self):
        # Example mock data: 2 tiles, 2 scenes each
        self.all_properties = [
            [
                {
                    "ground_control": True,
                    "quality_category": "standard",
                    "view_angle": 2.5,
                    "acquired": "2023-06-15T10:15:00Z",
                    "sun_elevation": 45.0,
                    "cloud_cover": 0.2,
                    "satellite_id": "A",
                    "instrument": "Planetscope",
                },
                {
                    "ground_control": True,
                    "quality_category": "standard",
                    "view_angle": 1.0,
                    "acquired": "2023-06-15T11:00:00Z",
                    "sun_elevation": 50.0,
                    "cloud_cover": 0.1,
                    "satellite_id": "B",
                    "instrument": "Planetscope",
                },
            ],
            [
                {
                    "ground_control": True,
                    "quality_category": "standard",
                    "view_angle": 2.0,
                    "acquired": "2023-06-16T09:45:00Z",
                    "sun_elevation": 60.0,
                    "cloud_cover": 0.3,
                    "satellite_id": "C",
                    "instrument": "Planetscope",
                },
                {
                    "ground_control": True,
                    "quality_category": "standard",
                    "view_angle": 1.5,
                    "acquired": "2023-06-16T10:30:00Z",
                    "sun_elevation": 55.0,
                    "cloud_cover": 0.4,
                    "satellite_id": "D",
                    "instrument": "Planetscope",
                },
            ],
        ]

        self.all_geometries = [
            [
                {
                    "coordinates": [
                        [
                            [-121, 38],
                            [-121, 38.1],
                            [-120.9, 38.1],
                            [-120.9, 38],
                            [-121, 38],
                        ]
                    ]
                },
                {
                    "coordinates": [
                        [
                            [-121, 38.2],
                            [-121, 38.3],
                            [-120.9, 38.3],
                            [-120.9, 38.2],
                            [-121, 38.2],
                        ]
                    ]
                },
            ],
            [
                {
                    "coordinates": [
                        [
                            [-121.5, 38.5],
                            [-121.5, 38.6],
                            [-121.4, 38.6],
                            [-121.4, 38.5],
                            [-121.5, 38.5],
                        ]
                    ]
                },
                {
                    "coordinates": [
                        [
                            [-121.6, 38.7],
                            [-121.6, 38.8],
                            [-121.5, 38.8],
                            [-121.5, 38.7],
                            [-121.6, 38.7],
                        ]
                    ]
                },
            ],
        ]

        self.all_ids = [
            ["tile1_scene1", "tile1_scene2"],
            ["tile2_scene1", "tile2_scene2"],
        ]

    def test_multi_tile_processing(self):
        gdf = analysis.process_tiles(
            self.all_properties, self.all_geometries, self.all_ids
        )
        self.assertEqual(len(gdf), 4)
        self.assertIn("view_angle", gdf.columns)
        self.assertIn("sun_angle", gdf.columns)
        self.assertTrue(np.all(gdf["view_angle"] < 3))
        self.assertTrue(np.all(gdf["max_sun_diff"] >= 0))


if __name__ == "__main__":
    unittest.main()
