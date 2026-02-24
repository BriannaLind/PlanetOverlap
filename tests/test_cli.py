from planet_overlap.cli import parse_args


def test_cli_defaults(tmp_path):
    args = parse_args(
        [
            "--aoi-file",
            "test.geojson",
            "--start-date",
            "2023-01-01",
            "--end-date",
            "2023-01-31",
            "--output-dir",
            str(tmp_path),
            "--max-cloud",
            "0.3",
            "--min-sun-angle",
            "10",
        ]
    )
    assert args.aoi_file == "test.geojson"
    assert args.start_date == "2023-01-01"
    assert args.end_date == "2023-01-31"
    assert args.output_dir == str(tmp_path)
    assert args.max_cloud == 0.3
    assert args.min_sun_angle == 10
