FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY vendor/portfolio_document_contract-0.1.0-py3-none-any.whl /tmp/portfolio_document_contract-0.1.0-py3-none-any.whl
RUN pip install --no-cache-dir /tmp/portfolio_document_contract-0.1.0-py3-none-any.whl \
    && rm /tmp/portfolio_document_contract-0.1.0-py3-none-any.whl
COPY pyproject.toml README.md ./
COPY ledger_lens ./ledger_lens
RUN pip install --no-cache-dir .
COPY index.html app.js styles.css ./
RUN useradd --create-home --uid 10001 ledger && mkdir -p /app/data/runtime \
    && chown -R ledger:ledger /app
USER ledger
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "ledger_lens.main:app", "--host", "0.0.0.0", "--port", "8000"]
