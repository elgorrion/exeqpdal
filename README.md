# exeqpdal

Type-safe Python API for PDAL CLI commands. Designed for QGIS plugin development and environments where python-pdal bindings are unavailable.

**Status**: Development (v0.1.0-dev) - GitHub installation only, not on PyPI.

## Features

- Native PDAL syntax support (`Pipeline()`, stage chaining)
- Complete type hints (mypy strict mode)
- QGIS 3.40+ compatible
- Pure Python (subprocess-based, no C++ dependencies)
- All PDAL readers, writers, filters, and applications

## Installation

**Prerequisites**: Python 3.12+, PDAL CLI binary installed

```bash
git clone https://github.com/elgorrion/exeqpdal.git
cd exeqpdal
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

**PDAL Installation**:
- Linux: `sudo apt install pdal`
- macOS: `brew install pdal`
- Windows: Bundled with QGIS 3.40+ at `{QGIS_ROOT}/bin/pdal.exe`

## Quick Start

### Pipeline Execution

```python
import exeqpdal as pdal

# JSON pipeline
pipeline = pdal.Pipeline('{"pipeline": ["input.las", {"type": "filters.range", "limits": "Classification[2:2]"}, "output.las"]}')
count = pipeline.execute()

# Stage chaining
pipeline = (
    pdal.Reader.las("input.las")
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.las("output.las")
)
pipeline.execute()
```

### Applications

```python
from exeqpdal import info, translate, merge

info_data = info("input.las", stats=True)
translate("input.las", "output.laz")
merge(["file1.las", "file2.las"], "merged.las")
```

### Point Data Access

```python
import exeqpdal as pdal

pipeline = pdal.Reader.las("input.las") | pdal.Filter.range(limits="Classification[2:2]")
pipeline.execute()

arrays = pipeline.arrays
points = arrays[0]
x, y, z = points['X'], points['Y'], points['Z']
ground = points[points['Classification'] == 2]
```

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

```python
import exeqpdal as pdal

try:
    pipeline = pdal.Reader.las("input.las") | pdal.Writer.las("output.las")
    pipeline.execute()
except pdal.PDALNotFoundError:
    print("PDAL binary not found")
except pdal.PDALExecutionError as e:
    print(f"Execution failed: {e.stderr}")
except pdal.PipelineError as e:
    print(f"Configuration error: {e}")
```

## Configuration

```python
import exeqpdal as pdal

# Set custom PDAL path
pdal.set_pdal_path("/usr/local/bin/pdal")

# Or use environment variable: export PDAL_EXECUTABLE=/path/to/pdal

# Validate installation
pdal.validate_pdal()
version = pdal.get_pdal_version()
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

See [CLAUDE.md](CLAUDE.md) for detailed development guidance.

## Documentation

- [INSTALL.md](INSTALL.md) - Installation and troubleshooting
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow

## License

MIT License
