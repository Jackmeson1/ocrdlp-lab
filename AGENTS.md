# Repository Guidelines

## Style Guide
- Use **Black** with the settings in `pyproject.toml` (line length 100, Python 3.11).
- Run **Ruff** to lint the code. Fix any errors reported.
- Write all comments and docstrings in **English**.

## Development Workflow
1. Install dependencies with `pip install -r requirements.txt`.
2. Before committing, run:
   ```bash
   ruff .
   pytest
   ```
   Make a best effort to ensure both succeed.

## Testing Notes
- Tests mock all network calls. No real API access should be required.
- Python scripts are expected to run with Python 3.11 or later.

