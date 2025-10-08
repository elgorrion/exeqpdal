# Contributing to exeqpdal

Development guide for contributors.

## Setup

```bash
git clone https://github.com/elgorrion/exeqpdal.git
cd exeqpdal
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
python -c "import exeqpdal; print(exeqpdal.__version__)"
```

**Prerequisites**: Python 3.12+, uv 0.9.0+, PDAL CLI, Git

## Workflow

```bash
# Create branch
git checkout -b feature/feature-name

# Make changes, run tests
pytest tests/
pytest tests/ --cov=exeqpdal --cov-report=term-missing

# Type checking
mypy exeqpdal/

# Linting
ruff check .
ruff format .

# Commit
git add .
git commit -m "feat: description"

# Push and create PR
git push origin feature/feature-name
```

## Commit Format

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

## Code Standards

### Type Hints (Required)

```python
def process(input_path: Path | str, options: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Process file."""
    ...
```

### Docstrings (Public APIs)

```python
def method(param: str, count: int = 10) -> dict[str, Any]:
    """Brief description.

    Args:
        param: Parameter description
        count: Optional with default

    Returns:
        Return value description

    Raises:
        ValueError: When invalid
    """
```

### Error Handling

```python
try:
    result = operation()
except SpecificError as e:
    raise CustomError(f"Failed: {e}") from e
```

### Testing

```python
def test_feature_works(self) -> None:
    """Test feature."""
    result = feature("input")
    assert result == "expected"

def test_edge_case(self) -> None:
    """Test edge case."""
    with pytest.raises(ValueError):
        feature("")
```

## Adding Features

### Reader

```python
# stages/readers.py
@staticmethod
def new_reader(filename: str, **options: Any) -> ReaderStage:
    """Read format."""
    return ReaderStage("readers.format", filename=filename, **options)

# tests/test_exeqpdal.py
def test_reader_format(self) -> None:
    """Test reader."""
    reader = pdal.Reader.new_reader("input.format")
    assert reader.stage_type == "readers.format"
```

### Filter

```python
# stages/filters.py
@staticmethod
def new_filter(**options: Any) -> FilterStage:
    """Filter description."""
    return FilterStage("filters.name", **options)

# tests/test_exeqpdal.py
def test_filter_name(self) -> None:
    """Test filter."""
    filter_stage = pdal.Filter.new_filter(param=value)
    assert filter_stage.stage_type == "filters.name"
```

### Application

```python
# apps/newapp.py
from __future__ import annotations
from pathlib import Path
from exeqpdal.core.executor import executor

def new_app(input_file: str | Path, **options: Any) -> None:
    """Application description."""
    args = [str(input_file)]
    executor.execute_application("newapp", args)

# Export in apps/__init__.py and main __init__.py
# Add tests
```

## Documentation Updates

Update when adding features:
- Feature list in README
- Quick start examples
- Supported components list
- Add examples to EXAMPLES.md

## Testing

### Run Tests

```bash
pytest tests/                                           # All
pytest tests/test_file.py -v                           # File
pytest tests/test_file.py::TestClass::test_method -v   # Specific
pytest tests/ --cov=exeqpdal --cov-report=html         # Coverage
```

### Coverage Target

Aim for >80% coverage:
```bash
pytest tests/ --cov=exeqpdal --cov-report=html
open htmlcov/index.html
```

## Pull Request Process

1. Update documentation
2. Add tests for new code
3. Pass all checks (pytest, mypy, ruff)
4. Address review feedback
5. Maintainer merges when approved

## Style Principles

1. Clarity over cleverness
2. Explicit over implicit
3. Type hints everywhere
4. Comprehensive error handling
5. Concise documentation

## Common Commands

```bash
# Specific test
pytest tests/test_exeqpdal.py::TestPipeline::test_name -v

# Type checking
mypy exeqpdal/ --strict

# Format all
ruff format .

# Auto-fix issues
ruff check --fix .
```

## License

MIT License - contributions licensed under same terms.
