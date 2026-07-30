from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytesseract
from PIL import Image
from pypdf import PdfReader

from ledger_lens.schemas import ExtractedField

MONEY = r"[$€£]?\s*[\d,.]+"
PATTERNS = {
    "invoice_number": (
        "Invoice number",
        re.compile(r"(?:invoice\s*(?:number|no\.?|#)?\s*[:#]?\s*)([A-Z0-9-]{4,})", re.I),
    ),
    "vendor": (
        "Vendor",
        re.compile(r"(?:from|vendor)\s*:?\s*([A-Z][^\n]{3,80})", re.I),
    ),
    "vat_id": (
        "VAT ID",
        re.compile(r"(?:VAT\s*(?:ID|number)?\s*:?\s*)([A-Z]{2}[A-Z0-9]{8,12})", re.I),
    ),
    "invoice_date": (
        "Invoice date",
        re.compile(
            r"(?:invoice\s*date\s*:?\s*)(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2})", re.I
        ),
    ),
    "po_number": (
        "Purchase order",
        re.compile(r"(?:purchase\s*order|PO)\s*(?:number|no\.?|#)?\s*:?\s*([A-Z0-9-]{3,})", re.I),
    ),
    "payment_terms": (
        "Payment terms",
        re.compile(r"(?:payment\s*)?terms\s*:?\s*(Net\s+\d+\s+days?)", re.I),
    ),
    "subtotal": ("Subtotal", re.compile(rf"subtotal\s*:?\s*({MONEY})", re.I)),
    "tax": ("Tax", re.compile(rf"(?:tax|VAT)\s*:?\s*({MONEY})", re.I)),
    "total": ("Total", re.compile(rf"^\s*total\s*(?:due)?\s*:?\s*({MONEY})", re.I | re.M)),
}


def read_text(path: Path, tesseract_cmd: str = "") -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
        if text.strip():
            return text
        raise ValueError("The PDF has no text layer. Convert its pages to images for OCR.")
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".tiff"}:
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        try:
            return pytesseract.image_to_string(Image.open(path))
        except pytesseract.TesseractNotFoundError as exc:
            raise ValueError("Tesseract is required for image OCR but was not found.") from exc
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    raise ValueError("Supported types are PDF, PNG, JPG, WEBP, TIFF, TXT and Markdown.")


def normalize_money(value: str) -> float | None:
    cleaned = re.sub(r"[^\d,.-]", "", value).replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_invoice(text: str, threshold: float) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    for name, (label, pattern) in PATTERNS.items():
        match = pattern.search(text)
        value = match.group(1).strip() if match else ""
        confidence = 0.94 if match else 0.0
        normalized: str | float | None = value or None
        if name in {"subtotal", "tax", "total"}:
            normalized = normalize_money(value)
            if normalized is None:
                confidence = min(confidence, 0.55)
        elif name == "vat_id" and value:
            if not re.fullmatch(r"[A-Z]{2}\d{9,12}", value):
                confidence = 0.71
        elif name == "invoice_date" and value:
            try:
                normalized = datetime.strptime(value, "%d %b %Y").date().isoformat()
            except ValueError:
                normalized = value
        elif name == "payment_terms" and value:
            confidence = 0.91
        fields.append(
            ExtractedField(
                name=name,
                label=label,
                value=value,
                normalized_value=normalized,
                confidence=confidence,
                status="confirmed" if confidence >= threshold else "needs_review",
                source_text=match.group(0).strip() if match else "Not found",
            )
        )
    return fields
