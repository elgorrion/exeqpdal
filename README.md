# exeqpdal

A Pythonic API for the Point Data Abstraction Library (PDAL).

`exeqpdal` provides a simple and intuitive way to execute PDAL operations from Python, especially in environments where the standard `python-pdal` bindings are not available, such as in QGIS plugins.

## Features

-   **Pythonic Interface:** Chain PDAL stages together using the `|` operator.
-   **Type-Safe:** Fully type-hinted for better editor support and code quality.
-   **QGIS-Ready:** Works out-of-the-box in QGIS 3.40+ plugins.
-   **Pure Python:** No C++ dependencies, just `subprocess` calls to the `pdal` command-line tool.
-   **Full PDAL Coverage:** Access to all PDAL readers, writers, filters, and applications.

## Prerequisites

-   Python 3.12+
-   PDAL command-line tool installed and accessible in your system's PATH.

## Installation

```bash
pip install exeqpdal
```

## Quick Start

### Convert a File

```python
import exeqpdal as pdal

pdal.translate("input.las", "output.laz")
```

### Filter Ground Points

```python
import exeqpdal as pdal

pipeline = (
    pdal.Reader.las("input.las")
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.las("ground_only.las")
)
pipeline.execute()
```

### Get File Information

```python
from exeqpdal import info

info_data = info("input.las", stats=True)
print(info_data)
```

For more examples, see the [examples documentation](docs/examples.md).

## Supported Components

`exeqpdal` supports all PDAL readers, writers, filters, and applications. For a full list, please refer to the official [PDAL documentation](https://pdal.io/en/stable/stages/index.html).

## Error Handling

`exeqpdal` provides a set of custom exceptions to handle errors related to PDAL execution, pipeline configuration, and more.

```python
import exeqpdal as pdal

try:
    pipeline = pdal.Pipeline(
        pdal.Reader.las("non_existent_file.las") | pdal.Writer.las("output.las")
    )
    pipeline.execute()
except pdal.PDALExecutionError as e:
    print(f"PDAL execution failed: {e.stderr}")
```

## Configuration

### Custom PDAL Path

If PDAL is not in your system's PATH, you can set the path to the `pdal` executable manually:

```python
import exeqpdal as pdal

pdal.set_pdal_path("/path/to/your/pdal")
```

### Verbose Output

Enable verbose output to see the PDAL command being executed and its output:

```python
import exeqpdal as pdal

pdal.set_verbose(True)
```

## License

`exeqpdal` is licensed under the MIT License.

This project is a wrapper around the PDAL command-line tool, which is licensed under the BSD license. When using `exeqpdal`, you are also using PDAL, and you should be aware of its license.

If you are using `exeqpdal` in a QGIS plugin, you should also be aware of the QGIS license (GPLv2+).
