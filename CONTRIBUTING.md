# Contributing

## Development setup

Install Tesseract, then run:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest --cov=ledger_lens --cov-report=term-missing
```

New extractors should keep source text, normalized values, validation, and
confidence routing separate. Add fixtures for both successful extraction and
review-triggering failure cases.
