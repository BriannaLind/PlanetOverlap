# PlanetOverlap
Find and organize satellite images for area/time of interest (tailored for Planet Labs Imagery)

**planet_overlap** is a scalable satellite imagery query engine for retrieving and filtering Planet Labs imagery (PSScene and SkySatScene) over large areas and long time periods.

It supports:

- 🛰 **Imagery Types**: PSScene (PlanetScope) and SkySatScene
- 📍 Multiple Areas of Interest (AOIs)
- 📌 Automatic buffering of point inputs
- 🗺 Automatic spatial tiling (in degrees)
- 📅 Flexible date range filtering
- ☁ Cloud cover filtering (0–1 fraction)
- ☀ Sun angle filtering (degrees)
- 📊 Progress tracking
- 🔁 Retry + timeout handling
- 🧠 Runtime and memory profiling
- 🧪 Automated testing (CI-enabled)

---

# 🚀 What It Does

You provide:

- A geographic area (GeoJSON file)
- A date range (YYYY-MM-DD format)
- Image quality filters (cloud cover, sun angle)
- An output directory

The system:

1. Connects to the Planet API with your API key
2. Searches for **PSScene** and **SkySatScene** imagery
3. Filters imagery by date and quality
4. Automatically tiles large areas (if needed)
5. Tracks progress during execution
6. Logs runtime (seconds) and peak memory usage (MB)
7. Saves structured results (GeoJSON and JSON files)


---

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/your-username/planet_overlap.git
cd planet_overlap
```
Install locally:

```bash
pip install .
```
---
## 🔑 Planet API Key

This tool requires a valid Planet API key to search and retrieve imagery. You can obtain an API key from the [Planet Developer Portal](https://www.planet.com/developer/).

Set your API key as an environment variable:

#### macOS/Linux

```bash
export PLANET_API_KEY=your_api_key_here
```

To make this permanent, add it to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export PLANET_API_KEY=your_api_key_here' >> ~/.bashrc
source ~/.bashrc
```

#### Windows (PowerShell)

```powershell
setx PLANET_API_KEY "your_api_key_here"
```

Restart your terminal or PowerShell session to apply the changes.

#### Verify API Key

To verify your API key is set correctly:

```bash
echo $PLANET_API_KEY  # macOS/Linux
echo $env:PLANET_API_KEY  # PowerShell
```
---
## 🛰 Basic Usage

Run from CLI:
```bash
planet_overlap \
  --aoi-file aoi.geojson \
  --start-date 2023-01-01 \
  --end-date 2023-01-31 \
  --output-dir ./output
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--aoi-file` | Path to GeoJSON file containing Area of Interest | **required** |
| `--start-date` | Start date in YYYY-MM-DD format | **required** |
| `--end-date` | End date in YYYY-MM-DD format | **required** |
| `--output-dir` | Output directory for results | **required** |
| `--max-cloud` | Maximum cloud cover fraction (0.0-1.0) | `0.5` |
| `--min-sun-angle` | Minimum sun angle in degrees (0.0-90.0) | `0.0` |
| `--tile-size` | Spatial tile size in decimal degrees | `1.0` |
| `--point-buffer` | Buffer size for point inputs in degrees | `0.001` |

### Example with Filters

```bash
planet_overlap \
  --aoi-file colorado.geojson \
  --start-date 2023-01-01 \
  --end-date 2023-01-31 \
  --max-cloud 0.3 \
  --min-sun-angle 30 \
  --output-dir ./output
```

## 📅 Date Filtering

Dates must be provided in ISO format:
```bash
YYYY-MM-DD
```
Example: 
```bash
2023-01-01
```
**The system calculates the total date span in days. If the date range exceeds 30 days, spatial tiling is automatically applied.**


---
## ☁ Cloud Cover Filtering
Cloud cover is expressed as a fraction between 0.0 and 1.0:
| Value | Meaning          |
| ----- | ---------------- |
| 0.0   | 0% cloud cover   |
| 0.5   | 50% cloud cover  |
| 1.0   | 100% cloud cover |

```bash
--max-cloud 0.5
```
---
## ☀ Sun Angle Filtering
Sun angle is measured in degrees (°) above the horizon. Lower values may produce long shadows.
| Sun Angle (°) | Interpretation |
| ------------- | -------------- |
| 0°            | Sun at horizon |
| 10°           | Low sun        |
| 30°           | Moderate sun   |
| 60°+          | High sun       |


```bash
--min-sun-angle 10
```

---
## 🛰 Imagery Types

The tool searches for the following Planet imagery types:

| Type | Description | Resolution |
|------|-------------|------------|
| **PSScene** | PlanetScope imagery (3-band and 4-band) | ~3.7m per pixel |
| **SkySatScene** | High-resolution satellite imagery | ~0.5m per pixel |

Both imagery types are searched simultaneously and results are combined in the output.

---
## 🗺 Spatial Tiling
Large AOIs are automatically divided into grid tiles. This can also occur for long date ranges and memory-sensitive runs. Tile size is specified in decimal degrees (°):

```bash
--tile-size 1.0
```
Meaning:

* 1.0° latitude ≈ 111 km
* 1.0° longitude ≈ 111 km × cos(latitude)

At mid-latitudes (e.g., California):

* 1° ≈ ~80–111 km per side
* So a 1.0° tile is roughly: ~80–111 km × ~111 km

---
## 📌 Point Inputs
If your AOI contains:

* Point
* MultiPoint

They are automatically buffered into polygons.

Buffer size is specified in decimal degrees (°):


```bash
--point-buffer 0.001
```
0.001° ≈ 111 meters (latitude direction)

---
## 📂 Output Files

The CLI generates the following files in your output directory:

| File | Description |
|------|-------------|
| `results.geojson` | GeoJSON file with filtered satellite imagery (contains geometry, timestamps, cloud cover, sun angle, etc.) |
| `properties.json` | JSON file with all scene properties for further analysis |

Each scene in `results.geojson` includes:
- `name`: Scene ID
- `geometry`: Scene footprint as a polygon
- `view_angle`: View angle of the scene
- `acquired`: Acquisition timestamp
- `cloud_cover`: Cloud cover fraction (0.0-1.0)
- `sun_elevation`: Sun elevation angle
- `sun_angle`: Sun angle above horizon (90° - sun_elevation)
- `satellite_id`: Satellite identifier
- `central_lon`/`central_lat`: Scene center coordinates
- `local_times`: Local acquisition time
- `max_sun_diff`: Maximum sun angle difference with overlapping scenes

---
## 📊 Performance Tracking
Each run reports:

* Total runtime (seconds)
* Peak memory usage (megabytes, MB)
* Number of spatial tiles processed
* Progress percentage

Example log:


```yaml
Starting: run_pagination
Processing 138 tiles
Completed: run_pagination | Runtime: 270.41s | Peak Memory: 184.73 MB
```

---
## 🧪 Running Tests
Tests verify:

* Geometry handling
* Tiling behavior
* Point buffering
* Filter construction
* CLI argument parsing
* Planet API integration

Run all tests with pytest:

```bash
pytest tests/
```

Run tests with verbose output:

```bash
pytest tests/ -v
```

---
## 🔄 Continuous Integration (CI)
This repository includes GitHub Actions. On every push:
* Tests are executed
* Linting is performed (automatically analyzing your code (or configuration files) for errors, stylistic issues, or potential bugs as part of a workflow)
* Failures prevent merge

Workflow file:

```bash
.github/workflows/ci.yml
```

---
## 📂 Project Structure

```bash
README.md                 # Project documentation
pyproject.toml            # Project configuration
.gitignore                # Files Git should ignore
src/
└── planet_overlap/
    ├── __init__.py
    ├── cli.py            # CLI interface and argument parsing
    ├── geometry.py       # AOI loading, point detection, buffering
    ├── filters.py        # Planet API filter construction
    ├── pagination.py    # Spatial and temporal tiling
    ├── quality.py        # Quality filtering functions
    ├── analysis.py      # Analysis and processing pipeline
    ├── performance.py    # Runtime and memory profiling
    ├── logger.py        # Logging configuration
    ├── client.py        # Planet API client and session management
    ├── io.py            # File I/O operations
    └── utils.py         # Utility functions
tests/
    ├── __init__.py
    ├── test_geometry.py        # Test loading AOIs, point detection, buffering, polygons
    ├── test_filters.py         # Test single/multiple .geojson AOIs, date ranges, cloud/sun filters
    ├── test_analysis.py        # Test overall analysis pipeline logic, derived columns
    ├── test_cli.py             # Test CLI argument parsing, dynamic config, and default overrides
    ├── test_geometry.py        # Test geometry operations
    ├── test_points.py          # Test point handling and date tiling
    └── test_tiling.py         # Test automatic spatial and temporal tiling logic
```

---
## ⚙ Requirements
* Python ≥ 3.10
* requests
* geopandas
* shapely
* tqdm

### Installing Dependencies

After cloning the repository, install the package with its dependencies:

```bash
pip install .
```

Or install dependencies manually:

```bash
pip install geopandas shapely requests tqdm
```

