import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import geopandas as gpd

from planet_overlap.geometry import load_aoi, buffer_points
from planet_overlap.pagination import fetch_planet_data, tile_aoi, tile_dates
from planet_overlap.analysis import process_tiles
from planet_overlap.filters import build_filters
from planet_overlap.performance import track_performance
from planet_overlap.logger import setup_logger
from planet_overlap.io import save_json
from planet_overlap.client import create_session, search_planet_items


def parse_args(args=None):
    """Parse command line arguments.
    
    Args:
        args: Optional list of arguments to parse. If None, uses sys.argv[1:].
              This allows for easier testing.
    """
    parser = argparse.ArgumentParser(
        description="Find and organize PlanetScope satellite imagery for area/time of interest."
    )
    
    parser.add_argument(
        "--aoi-file",
        required=True,
        help="Path to GeoJSON file containing Area of Interest"
    )
    
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format"
    )
    
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format"
    )
    
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--max-cloud",
        type=float,
        default=0.5,
        help="Maximum cloud cover fraction (0.0-1.0, default: 0.5)"
    )
    
    parser.add_argument(
        "--min-sun-angle",
        type=float,
        default=0.0,
        help="Minimum sun angle in degrees (default: 0.0)"
    )
    
    parser.add_argument(
        "--tile-size",
        type=float,
        default=1.0,
        help="Spatial tile size in decimal degrees (default: 1.0)"
    )
    
    parser.add_argument(
        "--point-buffer",
        type=float,
        default=0.001,
        help="Buffer size for point inputs in degrees (default: 0.001)"
    )
    
    return parser.parse_args(args)


def validate_dates(start_date: str, end_date: str) -> tuple[datetime, datetime]:
    """Validate and parse date strings."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start > end:
            raise ValueError("Start date must be before end date")
            
        return start, end
    except ValueError as e:
        logging.error(f"Invalid date format: {e}")
        sys.exit(1)


def create_output_directory(output_dir: str) -> Path:
    """Create output directory if it doesn't exist."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


@track_performance
def main():
    """Main CLI entry point."""
    args = parse_args()
    
    setup_logger()
    
    logging.info("Starting planet_overlap CLI")
    logging.info(f"AOI file: {args.aoi_file}")
    logging.info(f"Date range: {args.start_date} to {args.end_date}")
    logging.info(f"Output directory: {args.output_dir}")
    
    # Validate and parse dates
    start_date, end_date = validate_dates(args.start_date, args.end_date)
    
    # Create output directory
    output_dir = create_output_directory(args.output_dir)
    
    # Load AOI
    logging.info("Loading AOI...")
    try:
        aois = load_aoi([args.aoi_file])
        logging.info(f"Loaded {len(aois)} AOI(s)")
    except Exception as e:
        logging.error(f"Failed to load AOI: {e}")
        sys.exit(1)
    
    # Buffer points if needed
    from shapely.geometry import Point
    point_aois = [aoi for aoi in aois if isinstance(aoi, Point)]
    polygon_aois = [aoi for aoi in aois if not isinstance(aoi, Point)]
    
    if point_aois:
        logging.info(f"Buffering {len(point_aois)} point(s)...")
        buffered_points = buffer_points(point_aois, args.point_buffer)
        polygon_aois.extend(buffered_points)
    
    # Tile AOIs if needed
    all_tiles = []
    for aoi in polygon_aois:
        tiles = tile_aoi(aoi)
        all_tiles.extend(tiles)
    
    logging.info(f"Created {len(all_tiles)} spatial tile(s)")
    
    # Tile dates if needed
    date_ranges = tile_dates(start_date, end_date, is_point=bool(point_aois))
    logging.info(f"Created {len(date_ranges)} date range(s)")
    
    # Fetch Planet data
    logging.info("Fetching Planet data...")

    # Create authenticated session
    try:
        session = create_session()
        logging.info("Planet API session created successfully")
    except ValueError as e:
        logging.error(f"Failed to create Planet API session: {e}")
        sys.exit(1)

    all_properties = []
    all_geometries = []
    all_ids = []

    # Fetch data for each tile/date combination
    total_combinations = len(all_tiles) * len(date_ranges)
    logging.info(f"Processing {total_combinations} tile/date combinations")

    for i, tile in enumerate(all_tiles, 1):
        for j, (s_date, e_date) in enumerate(date_ranges, 1):
            logging.info(
                f"Processing tile {i}/{len(all_tiles)}, "
                f"date range {j}/{len(date_ranges)}"
            )

            # Make actual API call
            props, geoms, ids = search_planet_items(
                session=session,
                geometry=tile,
                start_date=s_date,
                end_date=e_date,
                max_cloud=args.max_cloud,
                min_sun_angle=args.min_sun_angle,
                limit=100,
            )

            all_properties.extend(props)
            all_geometries.extend(geoms)
            all_ids.extend(ids)

    logging.info(f"Total items fetched: {len(all_ids)}")
    
    if not all_properties:
        logging.warning("No data found matching criteria")
        # Create empty results
        empty_gdf = gpd.GeoDataFrame(
            columns=[
                "name", "geometry", "view_angle", "acquired",
                "cloud_cover", "sun_elevation", "sun_angle",
                "satellite_id", "central_lon", "central_lat",
                "local_times", "max_sun_diff"
            ]
        )
        empty_gdf.to_file(output_dir / "results.geojson", driver="GeoJSON")
        save_json([], output_dir / "properties.json")
        
        logging.info(f"Empty results saved to {output_dir}")
        return
    
    # Process tiles and create GeoDataFrame
    logging.info("Processing results...")
    gdf = process_tiles(
        [all_properties],
        [all_geometries],
        [all_ids],
        min_view_angle=3,
        min_sun_angle=args.min_sun_angle
    )
    
    # Save results
    results_file = output_dir / "results.geojson"
    gdf.to_file(results_file, driver="GeoJSON")
    logging.info(f"Results saved to {results_file}")
    
    # Save properties as JSON
    properties_file = output_dir / "properties.json"
    save_json(all_properties, properties_file)
    logging.info(f"Properties saved to {properties_file}")
    
    # Log summary
    logging.info(f"Total scenes found: {len(gdf)}")
    if len(gdf) > 0:
        logging.info(f"Date range covered: {gdf['acquired'].min()} to {gdf['acquired'].max()}")
        logging.info(f"Average cloud cover: {gdf['cloud_cover'].mean():.2%}")
        logging.info(f"Average sun angle: {gdf['sun_angle'].mean():.1f}°")
    
    logging.info("planet_overlap CLI completed successfully")


if __name__ == "__main__":
    main()
