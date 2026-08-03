import shutil
from pathlib import Path

import pytest
from PIL import Image

from ledger_lens.extractor import extract_document
from ledger_lens.schemas import ExtractedField
from ledger_lens.store import DocumentStore

FIXTURES = Path(__file__).parent / "fixtures" / "invoice2data"


def field_values(fields: list[ExtractedField]) -> dict[str, object]:
    return {
        field.name: (field.normalized_value if field.normalized_value is not None else field.value)
        for field in fields
    }


def test_public_text_pdf_uses_configurable_template_lines_and_provenance() -> None:
    result = extract_document(FIXTURES / "coolblue1.pdf", threshold=0.8)

    values = field_values(result.fields)
    assert result.schema_id == "nl.be.coolblue.yml"
    assert result.method == "pdf_text"
    assert values["invoice_number"] == "993548900"
    assert values["invoice_date"] == "2014-04-19"
    assert values["total"] == 717.97
    assert [item.values.get("name") for item in result.line_items] == [
        "Apple iPad Air Wifi 16 GB Zilver",
        "Decoded Leather Slim Cover Apple iPad Air 2 Zwart",
        "Nintendo 3DS XL Wit + Blauw",
        "Nintendo AC-adapter",
        "Mario Kart 7 3DS",
    ]
    assert all(item.provenance is not None for item in result.line_items)
    assert all(
        field.provenance is not None
        for field in result.fields
        if field.name in {"invoice_number", "invoice_date", "total"}
    )
    invoice_number = next(field for field in result.fields if field.name == "invoice_number")
    assert invoice_number.provenance is not None
    assert invoice_number.provenance.page == 1
    assert invoice_number.provenance.method == "pdf_text"
    assert invoice_number.provenance.template == "nl.be.coolblue.yml"


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not on PATH")
def test_public_image_fixture_runs_real_image_only_pdf_ocr(tmp_path: Path) -> None:
    scanned_pdf = tmp_path / "amazon-scan.pdf"
    with Image.open(FIXTURES / "AmazonWebServices.png") as image:
        image.convert("RGB").save(scanned_pdf, "PDF", resolution=150.0)

    result = extract_document(scanned_pdf, threshold=0.7)
    values = field_values(result.fields)

    assert result.method == "pdf_ocr"
    assert result.schema_id == "aws-ocr.yml"
    assert values["invoice_number"] == "42183017"
    assert values["total"] == 4.11
    assert next(field for field in result.fields if field.name == "invoice_number").provenance


def test_unsupported_template_fails_explicitly(tmp_path: Path) -> None:
    unknown = tmp_path / "unknown.txt"
    unknown.write_text("This unrelated report has no configured layout.", encoding="utf-8")

    with pytest.raises(ValueError, match="No configured extraction template"):
        extract_document(unknown, threshold=0.8)


def test_correction_history_is_append_only_and_export_uses_latest(tmp_path: Path) -> None:
    store = DocumentStore(tmp_path / "ledger.sqlite3")
    try:
        document = store.add(
            "invoice.txt",
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
        assert [(row.prior_value, row.corrected_value) for row in history] == [
            ("AB-100", "AB-101"),
            ("AB-101", "AB-102"),
        ]
        assert store.export(document.id).data["invoice_number"] == "AB-102"
    finally:
        store.close()
