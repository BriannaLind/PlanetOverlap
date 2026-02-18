from planet_overlap.cli import parse_args


def test_cli_defaults(tmp_path):
    args = parse_args(
        ["--output-dir", str(tmp_path), "--max-cloud", "0.3", "--min-sun-angle", "10"]
    )
    assert args.output_dir == str(tmp_path)
    assert args.max_cloud == 0.3
    assert args.min_sun_angle == 10
