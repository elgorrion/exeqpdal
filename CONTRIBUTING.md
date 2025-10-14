# Contributing to exeqpdal

Thank you for your interest in contributing to `exeqpdal`! All contributions are welcome, from bug reports to new features.

## Development Setup

1.  Fork and clone the repository:

    ```bash
    git clone https://github.com/YOUR-USERNAME/exeqpdal.git
    cd exeqpdal
    ```

2.  Create a virtual environment and install the dependencies:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    ```

3.  Run the tests to make sure everything is set up correctly:

    ```bash
    pytest
    ```

## Development Workflow

-   Create a new branch for your changes.
-   Make your changes and add tests for them.
-   Make sure all tests pass, including the linters and type checkers:

    ```bash
    pytest
    mypy exeqpdal
    ruff check .
    ruff format .
    ```

-   Commit your changes and push them to your fork.
-   Create a pull request.

## Code Style

This project uses `ruff` for linting and formatting. Please make sure your code conforms to the `ruff` configuration in the `pyproject.toml` file.

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
