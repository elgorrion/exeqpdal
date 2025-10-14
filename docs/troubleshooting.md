# Troubleshooting Guide

This document covers common installation and runtime issues for exeqpdal.

## Table of Contents

1. [PDAL Not Found](#pdal-not-found)
2. [QGIS Integration](#qgis-integration)
3. [Permission Issues](#permission-issues)
4. [Pipeline Execution Errors](#pipeline-execution-errors)

## PDAL Not Found

**Symptom**: `PDALNotFoundError: PDAL executable not found`

**Solution**: Set explicit PDAL path

```python
import exeqpdal as pdal

# Option 1: Set in code
pdal.set_pdal_path("/path/to/pdal")

# Option 2: Environment variable
# export PDAL_EXECUTABLE=/path/to/pdal
```

**Platform-specific installations**:

Linux (Ubuntu/Debian):
```bash
sudo apt install pdal
```

macOS (Homebrew):
```bash
brew install pdal
```

Windows (QGIS bundle):
- Install QGIS 3.40+ from qgis.org
- PDAL included at `C:\Program Files\QGIS 3.x\bin\pdal.exe`
- exeqpdal auto-detects QGIS installations

Windows (standalone):
```bash
conda install -c conda-forge pdal
```

## QGIS Integration

**QGIS Plugin Setup**:

Create `requirements.txt` in your plugin directory:
```
exeqpdal>=0.1.0a1
```

**Usage in QGIS Plugin**:

```python
from qgis.core import QgsMessageLog, Qgis
import exeqpdal as pdal

def process_lidar(input_file, output_file):
    try:
        pipeline = pdal.Pipeline(
            pdal.Reader.las(input_file)
            | pdal.Filter.outlier(method="statistical")
            | pdal.Writer.las(output_file)
        )
        count = pipeline.execute()
        QgsMessageLog.logMessage(
            f"Processed {count} points", "LiDAR", Qgis.Success
        )
    except pdal.PDALNotFoundError:
        QgsMessageLog.logMessage(
            "PDAL CLI not found. Install QGIS bundle includes PDAL.",
            "LiDAR",
            Qgis.Critical
        )
    except pdal.PDALExecutionError as e:
        QgsMessageLog.logMessage(
            f"Execution failed: {e.stderr}", "LiDAR", Qgis.Critical
        )
```

**QGIS-specific PDAL paths**:
- Windows: `C:\Program Files\QGIS 3.40\bin\pdal.exe`
- macOS: `/Applications/QGIS.app/Contents/MacOS/bin/pdal`
- Linux: `/usr/bin/pdal` (via package manager)

## Permission Issues

**Symptom**: `PermissionError` when executing PDAL

**Solution**: Ensure PDAL binary is executable

Linux/macOS:
```bash
chmod +x /path/to/pdal
```

Windows:
- Right-click PDAL binary → Properties → Security
- Ensure "Read & Execute" permissions enabled

## Pipeline Execution Errors

**Enable detailed logging**:

```python
import exeqpdal as pdal
import logging

logging.basicConfig(level=logging.DEBUG)
pdal.set_verbose(True)

pipeline = pdal.Pipeline(pipeline_json)
try:
    pipeline.validate()  # Check before execution
    count = pipeline.execute()
except pdal.ValidationError as e:
    print(f"Invalid pipeline: {e}")
except pdal.PDALExecutionError as e:
    print(f"Execution failed: {e.stderr}")
```

**Common pipeline errors**:

1. **Invalid JSON**: Validate pipeline JSON syntax
2. **Missing files**: Check input file paths exist
3. **Unsupported operations**: Verify PDAL version supports stage
4. **Memory issues**: Process large files in chunks with `filters.splitter`

**Verify pipeline before execution**:

```python
pipeline = pdal.Pipeline(pipeline_json)
pipeline.validate()  # Raises ValidationError if invalid
```

## Additional Resources

- [PDAL Documentation](https://pdal.io/) - Official PDAL reference
- [GitHub Issues](https://github.com/elgorrion/exeqpdal/issues) - Report bugs
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guide
