# Contributing to exeqpdal

**Thank you for considering contributing to exeqpdal!**

We're excited to have you here. Whether you're fixing a bug, adding a feature, improving documentation, or just asking questions - your contributions make this project better for everyone.

**New to open source?** Don't worry! This guide will walk you through everything.

## Quick Start: Get the Code Running

### 1. Fork and clone the repository

```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR-USERNAME/exeqpdal.git
cd exeqpdal
```

### 2. Set up your development environment

```bash
# Create a virtual environment
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Verify it works
python -c "import exeqpdal; print(f'Installed version: {exeqpdal.__version__}')"
```

### 3. Make sure tests pass

```bash
# Run all tests
pytest tests/

# Everything passing? Great! You're ready to contribute.
```

**Prerequisites**: Python 3.12+, uv 0.9.0+, PDAL CLI installed, Git

**Having setup issues?** Open an issue and we'll help you get started!

## How to Contribute

### Step 1: Pick something to work on

**Good first issues** (look for the "good first issue" label):
- Documentation improvements
- Adding examples
- Fixing typos
- Writing tests

**Bigger contributions**:
- New reader/writer/filter support
- Bug fixes
- Performance improvements

Not sure where to start? Ask in an issue or discussion!

### Step 2: Create a branch

```bash
# Create a branch for your changes
git checkout -b feature/my-awesome-feature

# Branch naming:
# - feature/xxx for new features
# - fix/xxx for bug fixes
# - docs/xxx for documentation
```

### Step 3: Make your changes

Write your code, add tests, update documentation as needed.

### Step 4: Run quality checks

```bash
# Run tests (make sure they all pass!)
pytest tests/

# Check test coverage
pytest tests/ --cov=exeqpdal --cov-report=term-missing

# Type checking (strict mode)
mypy exeqpdal/

# Linting and formatting
ruff check .
ruff format .
```

**All checks must pass** before your PR can be merged.

### Step 5: Commit your changes

```bash
git add .
git commit -m "feat: add support for XYZ filter"
```

See [Commit Format](#commit-format) below for commit message guidelines.

### Step 6: Push and create a Pull Request

```bash
# Push your branch
git push origin feature/my-awesome-feature

# Then go to GitHub and create a Pull Request
```

### Step 7: Address review feedback

A maintainer will review your PR and may ask for changes. Don't worry - this is normal! We'll work with you to get your contribution merged.

## Commit Format

We use conventional commits to keep the history clean and make releases easier.

**Format**: `type: description`

**Types**:
- `feat:` - New feature (e.g., "feat: add support for filters.csf")
- `fix:` - Bug fix (e.g., "fix: handle missing PDAL_EXECUTABLE gracefully")
- `docs:` - Documentation only (e.g., "docs: add example for batch processing")
- `test:` - Tests only (e.g., "test: add integration test for Writer.copc")
- `refactor:` - Code refactoring (no functional changes)
- `chore:` - Maintenance tasks (e.g., "chore: update dependencies")

**Examples of good commit messages**:
```
feat: add support for filters.eigenvalues
fix: correctly handle Windows paths with spaces
docs: improve QGIS integration examples
test: add tests for error handling in Pipeline.execute()
```

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

## Pull Request Checklist

Before submitting your PR, make sure:

- [ ] **Tests pass**: `pytest tests/` runs without errors
- [ ] **Type checking passes**: `mypy exeqpdal/` shows no errors
- [ ] **Code is formatted**: `ruff format .` has been run
- [ ] **Linting passes**: `ruff check .` shows no errors
- [ ] **Documentation updated**: If you added features, update relevant docs
- [ ] **Tests added**: New features have tests
- [ ] **Commit message follows format**: Using conventional commits

### What happens after you submit?

1. **Automated checks run** - CI will test your code on multiple platforms
2. **Maintainer reviews** - We'll look at your code and may suggest changes
3. **You address feedback** - Make requested changes if needed
4. **PR is merged** - Your contribution becomes part of exeqpdal!

**Review time**: Most PRs are reviewed within a few days. Larger changes may take longer.

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

## Code of Conduct

Be kind and respectful. We want everyone to feel welcome.

- **Be friendly and patient**
- **Be welcoming** - we're here to learn from each other
- **Be considerate** - your work will be used by others
- **Be respectful** - disagreement is okay, but be professional
- **Be careful with words** - we're a diverse community

If you experience or witness unacceptable behavior, please report it by opening an issue.

## Questions?

- **Not sure how to start?** Open an issue titled "Question: ..." and we'll help
- **Want to discuss a big change?** Open a discussion before starting work
- **Found a bug?** Open an issue with steps to reproduce
- **Have a feature idea?** Open an issue to discuss it first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
