# exeqpdal

**A Python API for PDAL that works everywhere** - especially in QGIS plugins and environments where python-pdal bindings aren't available.

**Status**: Alpha (v0.1.0a1) - Ready for testing and feedback!

## Why exeqpdal?

If you've ever wanted to process point cloud data in Python but struggled with:
- **QGIS plugin development** - python-pdal doesn't work in QGIS environments
- **Deployment headaches** - python-pdal requires C++ dependencies and complex builds
- **Platform compatibility** - Need something that works on Windows, Linux, and macOS

Then exeqpdal is for you! It provides a clean, Pythonic API that wraps the PDAL command-line tool, giving you all the power of PDAL without the installation headaches.

## Features

- **Familiar syntax** - Use native PDAL patterns like `Pipeline()` and stage chaining
- **Type-safe** - Complete type hints (passes mypy strict mode)
- **QGIS-ready** - Works seamlessly in QGIS 3.40+ plugin environments
- **Pure Python** - No C++ dependencies, just subprocess calls
- **Complete coverage** - All PDAL readers, writers, filters, and applications

## Installation

### Step 1: Install exeqpdal

```bash
pip install exeqpdal
```

That's it! Well, almost...

### Step 2: Install PDAL CLI

exeqpdal needs the PDAL command-line tool to be installed on your system. Don't worry, it's straightforward:

**Linux** (Ubuntu/Debian):
```bash
sudo apt install pdal
```

**macOS** (Homebrew):
```bash
brew install pdal
```

**Windows** (easiest - via QGIS):
- Install [QGIS 3.40+](https://qgis.org/download/) (includes PDAL)
- PDAL is automatically at: `C:\Program Files\QGIS 3.x\bin\pdal.exe`
- exeqpdal will find it automatically!

**Windows** (standalone):
```bash
conda install -c conda-forge pdal
```

### Step 3: Verify Everything Works

```python
import exeqpdal as pdal

# Check that exeqpdal can find PDAL
pdal.validate_pdal()
print(f"Success! Using PDAL version: {pdal.get_pdal_version()}")
```

**Having trouble?** Check our [troubleshooting guide](docs/troubleshooting.md) for common issues and solutions.

## Quick Start

Let's process some point cloud data! Here are the most common tasks:

### Convert a File (in 2 lines!)

```python
import exeqpdal as pdal

# Convert LAS to LAZ (compressed)
pdal.translate("input.las", "output.laz")
```

### Filter Ground Points

```python
import exeqpdal as pdal

# Extract ground points (classification 2) from a LAS file
pipeline = pdal.Pipeline(
    pdal.Reader.las("input.las")
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.las("ground_only.las")
)
pipeline.execute()
print(f"Done! Processed {pipeline._point_count:,} points")
```

### Get File Information

```python
from exeqpdal import info, get_count, get_bounds

# Get detailed info about a file
info_data = info("input.las", stats=True)

# Quick queries
print(f"Points: {get_count('input.las'):,}")
print(f"Bounds: {get_bounds('input.las')}")
```

### Merge Multiple Files

```python
from exeqpdal import merge

# Combine multiple LAS files into one
merge(["tile1.las", "tile2.las", "tile3.las"], "merged.las")
```

### Real-World Example: Ground Classification

```python
import exeqpdal as pdal

# Classify ground points and create a DTM raster
pipeline = pdal.Pipeline(
    pdal.Reader.las("lidar_data.las")
    | pdal.Filter.smrf()  # Simple Morphological Filter for ground classification
    | pdal.Filter.range(limits="Classification[2:2]")  # Keep only ground points
    | pdal.Writer.gdal(filename="dtm.tif", resolution=1.0, output_type="mean")
)
count = pipeline.execute()
print(f"Created DTM from {count:,} ground points")
```

**Want more examples?** See [EXAMPLES.md](EXAMPLES.md) for batch processing, QGIS integration, and advanced workflows.

## Supported Components

### Readers
`las`, `copc`, `e57`, `ept`, `text`, `bpf`, `draco`, `gdal`, `hdf`, `i3s`, `las`, `matlab`, `mbio`, `mrsid`, `nitf`, `obj`, `optech`, `pcd`, `pgpointcloud`, `ply`, `pts`, `qfit`, `rdb`, `rxp`, `sbet`, `slpk`, `stac`, `tindex`, `terrasolid`, `tiledb`, and 10+ more.

### Filters
Ground classification: `smrf`, `pmf`, `csf`
Outlier removal: `outlier`, `iqr`, `lof`
Features: `normal`, `eigenvalues`, `covariancefeatures`
Clustering: `dbscan`, `cluster`
Transform: `reprojection`, `transformation`
Decimation: `decimation`, `voxeldownsize`, `fps`
And 80+ more filters.

### Writers
`las`, `copc`, `gdal`, `ply`, `text`, `bpf`, `draco`, `e57`, `fbx`, `gltf`, `matlab`, `nitf`, `null`, `pcd`, `pgpointcloud`, `raster`, `sbet`, `tiledb`, and more.

### Applications
`info`, `translate`, `merge`, `split`, `tile`, `tindex`, `pipeline`

## Error Handling

exeqpdal provides clear, actionable error messages to help you fix issues quickly:

```python
import exeqpdal as pdal

try:
    pipeline = pdal.Pipeline(
        pdal.Reader.las("input.las") | pdal.Writer.las("output.las")
    )
    pipeline.execute()

except pdal.PDALNotFoundError:
    # PDAL CLI isn't installed or can't be found
    print("PDAL not found. Please install PDAL or set PDAL_EXECUTABLE environment variable.")

except pdal.PDALExecutionError as e:
    # PDAL ran but failed (bad file, invalid options, etc.)
    print(f"PDAL execution failed: {e.stderr}")

except pdal.PipelineError as e:
    # Pipeline configuration is invalid
    print(f"Pipeline configuration error: {e}")
```

Most errors include helpful context like the command that failed and the actual PDAL error message.

## Configuration

### Custom PDAL Path

If PDAL isn't being auto-detected, or you want to use a specific version:

```python
import exeqpdal as pdal

# Option 1: Set path in code
pdal.set_pdal_path("/usr/local/bin/pdal")

# Option 2: Set environment variable (recommended for deployment)
# export PDAL_EXECUTABLE=/path/to/pdal

# Verify it worked
pdal.validate_pdal()
print(f"Using PDAL {pdal.get_pdal_version()}")
```

### Verbose Output (for debugging)

```python
import exeqpdal as pdal

# Enable verbose PDAL output to see what's happening
pdal.set_verbose(True)

# Now PDAL will print detailed execution info
pipeline = pdal.Pipeline(pdal.Reader.las("input.las") | pdal.Writer.las("output.las"))
pipeline.execute()
```

## Development

```bash
# Tests
pytest tests/

# Type checking
mypy exeqpdal/

# Linting and formatting
ruff check .
ruff format .
```

For detailed development guidance, see [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/exeqpdal_dev.md](docs/exeqpdal_dev.md).

## Documentation

- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow
- [docs/exeqpdal_dev.md](docs/exeqpdal_dev.md) - Complete developer reference
- [docs/troubleshooting.md](docs/troubleshooting.md) - Installation and runtime issues

## License

MIT License
