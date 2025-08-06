# Unified OCR Pipeline - Testing Guide

## Running Tests
- All main scripts should have unit tests using `pytest`.
- To run all tests:

```bash
pytest scripts/
```

## Example Test (extract_fields)
Create a file `test_extract_fields.py` in `scripts/`:

```python
import pytest
from extract_fields import extract_fields

def test_po_extraction():
    text = "PO Number: 4551234567\nMJO NO: 12345678"
    result = extract_fields(text)
    assert result["PO Number"] == "4551234567"
    assert result["MJO NO"] == "12345678"
```

## Linting
Run `flake8` to check code style:

```bash
flake8 scripts/
```

## Adding More Tests
- Add tests for PDF splitting, error handling, and integration logic.
- Place all test files in `scripts/` or a dedicated `tests/` folder.
