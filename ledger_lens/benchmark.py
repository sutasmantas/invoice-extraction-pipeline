from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tempfile
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytesseract
from PIL import Image

from ledger_lens.extractor import extract_document
from ledger_lens.schemas import ExtractedField
from ledger_lens.store import DocumentStore

EXPECTED_HASHES = {
    "coolblue1.pdf": "3932539b71338f0c73d6ade499a2a00cd2f9056c60f5a87b1ef623af095e1607",
    "AmazonWebServices.pdf": "2e21d50f59a97b8c3778b238d14c9d7d15f74b8d021f819f1d2ede1f5412f81b",
    "AmazonWebServices.png": "fec56e365019c348986bfe1a6c16db13b1d16fc5962be83835bb4ac533466d6c",
}
EXPECTED_LINES = {
    "Apple iPad Air Wifi 16 GB Zilver",
    "Decoded Leather Slim Cover Apple iPad Air 2 Zwart",
    "Nintendo 3DS XL Wit + Blauw",
    "Nintendo AC-adapter",
    "Mario Kart 7 3DS",
}


def run_benchmark(fixture_dir: Path) -> dict[str, Any]:
    hashes = {
        name: hashlib.sha256((fixture_dir / name).read_bytes()).hexdigest()
        for name in EXPECTED_HASHES
    }
    hash_gate = hashes == EXPECTED_HASHES

    started = time.perf_counter()
    text_result = extract_document(fixture_dir / "coolblue1.pdf", threshold=0.8)
    text_ms = round((time.perf_counter() - started) * 1000, 1)
    text_values = _field_values(text_result.fields)
    line_names = {
        str(item.values["name"]) for item in text_result.line_items if item.values.get("name")
    }
    text_gate = (
        text_values.get("invoice_number") == "993548900"
        and text_values.get("invoice_date") == "2014-04-19"
        and text_values.get("total") == 717.97
        and EXPECTED_LINES.issubset(line_names)
    )
    provenance_gate = all(item.provenance for item in text_result.line_items) and all(
        field.provenance
        for field in text_result.fields
        if field.name in {"invoice_number", "invoice_date", "total"}
    )

    with tempfile.TemporaryDirectory(prefix="ledger-benchmark-") as directory:
        runtime = Path(directory)
        scanned_pdf = runtime / "amazon-scan.pdf"
        with Image.open(fixture_dir / "AmazonWebServices.png") as image:
            image.convert("RGB").save(scanned_pdf, "PDF", resolution=150.0)
        started = time.perf_counter()
        scan_result = extract_document(scanned_pdf, threshold=0.7)
        scan_ms = round((time.perf_counter() - started) * 1000, 1)
        scan_values = _field_values(scan_result.fields)
        scan_gate = (
            scan_result.method == "pdf_ocr"
            and scan_result.schema_id == "aws-ocr.yml"
            and scan_values.get("invoice_number") == "42183017"
            and scan_values.get("total") == 4.11
        )
        store = DocumentStore(runtime / "corrections.sqlite3")
        try:
            document = store.add(
                "correction.txt",
                [
                    ExtractedField(
                        name="invoice_number",
                        label="Invoice number",
                        value="AB-100",
                        normalized_value="AB-100",
                        confidence=0.7,
                        status="needs_review",
                        source_text="Invoice AB-100",
                    )
                ],
            )
            store.correct(document.id, "invoice_number", "AB-101")
            store.correct(document.id, "invoice_number", "AB-102")
            history = store.corrections(document.id)
            history_gate = [(row.prior_value, row.corrected_value) for row in history] == [
                ("AB-100", "AB-101"),
                ("AB-101", "AB-102"),
            ] and store.export(document.id).data["invoice_number"] == "AB-102"
        finally:
            store.close()

    gates = {
        "fixture_hashes": hash_gate,
        "text_fields_and_lines": text_gate,
        "source_provenance": provenance_gate,
        "real_scanned_pdf_ocr": scan_gate,
        "append_only_corrections": history_gate,
    }
    return {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "gates": gates,
        "fixtures": hashes,
        "text_pdf": {
            "schema": text_result.schema_id,
            "method": text_result.method,
            "elapsed_ms_observation": text_ms,
            "invoice_number": text_values.get("invoice_number"),
            "date": text_values.get("invoice_date"),
            "amount": text_values.get("total"),
            "named_line_items": sorted(line_names),
        },
        "scanned_pdf": {
            "schema": scan_result.schema_id,
            "method": scan_result.method,
            "elapsed_ms_observation": scan_ms,
            "invoice_number": scan_values.get("invoice_number"),
            "amount": scan_values.get("total"),
        },
        "environment": {
            "python": platform.python_version(),
            "invoice2data": version("invoice2data"),
            "pypdfium2": version("pypdfium2"),
            "tesseract": str(pytesseract.get_tesseract_version()).splitlines()[0],
        },
        "claim_boundary": (
            "Fixed public fixtures only; no arbitrary-layout, calibrated-confidence, "
            "production-accuracy, scale, or client-data claim."
        ),
    }


def _field_values(fields: list[ExtractedField]) -> dict[str, Any]:
    return {
        field.name: (field.normalized_value if field.normalized_value is not None else field.value)
        for field in fields
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the fixed LedgerLens depth benchmark.")
    parser.add_argument("fixture_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_benchmark(args.fixture_dir)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
