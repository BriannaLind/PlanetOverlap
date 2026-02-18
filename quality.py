from typing import List, Dict


def filter_quality(
    properties: List[Dict], min_view_angle: float, max_cloud: float
) -> List[Dict]:

    return [
        p
        for p in properties
        if p["view_angle"] < min_view_angle and p["cloud_cover"] <= max_cloud
    ]
