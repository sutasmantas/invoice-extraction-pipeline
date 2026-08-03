from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import pytesseract
import regex
from invoice2data.extract.invoice_template import InvoiceTemplate
from invoice2data.extract.loader import read_templates
from invoice2data.input import pdfium as invoice_pdfium
from invoice2data.input import text as invoice_text
from PIL import Image
from pytesseract import Output

from ledger_lens.config import PROJECT_ROOT
from ledger_lens.schemas import ExtractedField, ExtractedLineItem, SourceReference

SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".tiff"}
SUPPORTED_TEXT = {".txt", ".md"}
DEFAULT_TEMPLATE_DIR = PROJECT_ROOT / "ledger_lens" / "templates"

FIELD_NAMES = {
    "amount": ("total", "Total"),
    "amount_tax": ("tax", "Tax"),
    "amount_untaxed": ("subtotal", "Subtotal"),
    "date": ("invoice_date", "Invoice date"),
    "invoice_number": ("invoice_number", "Invoice number"),
    "partner_name": ("vendor", "Vendor"),
    "purchase_order": ("po_number", "Purchase order"),
    "payment_terms": ("payment_terms", "Payment terms"),
    "vat": ("vat_id", "VAT ID"),
}
RESULT_METADATA = {"desc", "template_name"}
LINE_KEYS = {"lines", "line_items"}


@dataclass(frozen=True)
class ReadResult:
    pages: tuple[str, ...]
    method: str
    routing_score: float

    @property
    def text(self) -> str:
        return "\n".join(self.pages)


@dataclass(frozen=True)
class ExtractionResult:
    fields: list[ExtractedField]
    line_items: list[ExtractedLineItem]
    schema_id: str
    method: str


def read_document(path: Path, tesseract_cmd: str = "") -> ReadResult:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        document = pdfium.PdfDocument(path)
        try:
            pages = tuple(_page_text(page) for page in document)
            if any(page.strip() for page in pages):
                return ReadResult(pages=pages, method="pdf_text", routing_score=0.94)
            ocr_pages: list[str] = []
            scores: list[float] = []
            for page in document:
                image = page.render(scale=300 / 72).to_pil()
                text, score = _ocr_image(image, tesseract_cmd)
                ocr_pages.append(text)
                scores.append(score)
            if not any(page.strip() for page in ocr_pages):
                raise ValueError("OCR produced no text from the image-only PDF.")
            return ReadResult(
                pages=tuple(ocr_pages),
                method="pdf_ocr",
                routing_score=min(scores, default=0.0),
            )
        finally:
            document.close()
    if suffix in SUPPORTED_IMAGES:
        with Image.open(path) as image:
            text, score = _ocr_image(image, tesseract_cmd)
        if not text.strip():
            raise ValueError("OCR produced no text from the image.")
        return ReadResult(pages=(text,), method="image_ocr", routing_score=score)
    if suffix in SUPPORTED_TEXT:
        return ReadResult(
            pages=(path.read_text(encoding="utf-8"),),
            method="plain_text",
            routing_score=0.94,
        )
    raise ValueError("Supported types are PDF, PNG, JPG, WEBP, TIFF, TXT and Markdown.")


def extract_document(
    path: Path,
    threshold: float,
    tesseract_cmd: str = "",
    template_dir: Path = DEFAULT_TEMPLATE_DIR,
) -> ExtractionResult:
    read_result = read_document(path, tesseract_cmd)
    return _extract_transcript(read_result, path, threshold, template_dir)


def extract_invoice(
    text: str,
    threshold: float,
    template_dir: Path = DEFAULT_TEMPLATE_DIR,
) -> list[ExtractedField]:
    """Compatibility adapter for seeded text records and existing callers."""
    result = _extract_transcript(
        ReadResult(pages=(text,), method="plain_text", routing_score=0.94),
        Path("inline.txt"),
        threshold,
        template_dir,
    )
    return result.fields


def _extract_transcript(
    read_result: ReadResult,
    source_path: Path,
    threshold: float,
    template_dir: Path,
) -> ExtractionResult:
    templates = read_templates(str(template_dir)) + read_templates()
    template = _match_template(read_result.text, templates)
    if template is None:
        raise ValueError("No configured extraction template matched this document.")
    input_module = invoice_pdfium if read_result.method == "pdf_text" else invoice_text
    try:
        extracted = template.extract(
            template.prepare_input(read_result.text),
            str(source_path),
            input_module,
        )
    except Exception as exc:
        raise ValueError(f"The matched template could not extract required fields: {exc}") from exc
    schema_id = str(extracted.get("template_name") or template.get("template_name") or "")
    fields = _build_fields(extracted, template, read_result, threshold, schema_id)
    line_items = _build_line_items(extracted, read_result, schema_id)
    if not fields:
        raise ValueError("The matched template returned no reviewable scalar fields.")
    return ExtractionResult(
        fields=fields,
        line_items=line_items,
        schema_id=schema_id,
        method=read_result.method,
    )


def _page_text(page: Any) -> str:
    text_page = page.get_textpage()
    try:
        text = text_page.get_text_bounded()
        return text.replace("\r\n", "\n").replace("\r", "\n").replace("ï»¿", "").replace("ï¿¾", "")
    finally:
        text_page.close()


def _ocr_image(image: Image.Image, tesseract_cmd: str) -> tuple[str, float]:
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    try:
        data = pytesseract.image_to_data(image.convert("RGB"), output_type=Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise ValueError("Tesseract is required for OCR but was not found.") from exc
    lines: dict[tuple[int, int, int], list[str]] = {}
    confidences: list[float] = []
    for index, word in enumerate(data["text"]):
        word = word.strip()
        if not word:
            continue
        key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
        lines.setdefault(key, []).append(word)
        try:
            confidence = float(data["conf"][index])
        except (TypeError, ValueError):
            continue
        if confidence >= 0:
            confidences.append(confidence)
    text = "\n".join(" ".join(words) for words in lines.values())
    mean_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.0
    return text, min(mean_confidence, 0.92)


def _match_template(text: str, templates: list[InvoiceTemplate]) -> InvoiceTemplate | None:
    folded = text.casefold()
    ordered = sorted(templates, key=lambda item: int(item.get("priority", 5)), reverse=True)
    for template in ordered:
        keywords = [str(keyword).casefold() for keyword in template.get("keywords", [])]
        excluded = [str(keyword).casefold() for keyword in template.get("exclude_keywords", [])]
        if all(keyword in folded for keyword in keywords) and not any(
            keyword in folded for keyword in excluded
        ):
            return template
    return None


def _build_fields(
    extracted: dict[str, Any],
    template: InvoiceTemplate,
    read_result: ReadResult,
    threshold: float,
    schema_id: str,
) -> list[ExtractedField]:
    output: list[ExtractedField] = []
    declared = template.get("ledger_fields") or []
    keys = (
        list(declared)
        if declared
        else [
            key
            for key, value in extracted.items()
            if key not in RESULT_METADATA
            and key not in LINE_KEYS
            and not isinstance(value, (dict, list))
        ]
    )
    if "partner_name" in keys and "issuer" in keys:
        keys.remove("issuer")
    for result_name in keys:
        field_name, label = FIELD_NAMES.get(
            result_name,
            (result_name, result_name.replace("_", " ").title()),
        )
        raw_value = extracted.get(result_name)
        display, normalized = _normalize_value(raw_value)
        provenance = _field_provenance(
            result_name,
            raw_value,
            template,
            read_result,
            schema_id,
        )
        confidence = read_result.routing_score if raw_value is not None else 0.0
        if field_name == "vat_id" and display and not re.fullmatch(r"[A-Z]{2}\d{9,12}", display):
            confidence = min(confidence, 0.71)
        output.append(
            ExtractedField(
                name=field_name,
                label=label,
                value=display,
                normalized_value=normalized,
                confidence=confidence,
                status="confirmed" if confidence >= threshold else "needs_review",
                source_text=provenance.text if provenance else "Not found",
                provenance=provenance,
            )
        )
    return output


def _build_line_items(
    extracted: dict[str, Any],
    read_result: ReadResult,
    schema_id: str,
) -> list[ExtractedLineItem]:
    raw_items: list[dict[str, Any]] = []
    for key in LINE_KEYS:
        value = extracted.get(key)
        if isinstance(value, list):
            raw_items.extend(item for item in value if isinstance(item, dict))
    output: list[ExtractedLineItem] = []
    for item in raw_items:
        values = {key: _json_value(value) for key, value in item.items()}
        candidates = sorted(
            (str(value) for value in values.values() if isinstance(value, str)),
            key=len,
            reverse=True,
        )
        provenance = next(
            (
                reference
                for candidate in candidates
                if (
                    reference := _find_text_reference(
                        read_result.pages,
                        candidate,
                        read_result.method,
                        schema_id,
                    )
                )
                is not None
            ),
            None,
        )
        output.append(ExtractedLineItem(values=values, provenance=provenance))
    return output


def _field_provenance(
    field_name: str,
    value: Any,
    template: InvoiceTemplate,
    read_result: ReadResult,
    schema_id: str,
) -> SourceReference | None:
    settings = template.get("fields", {}).get(field_name)
    patterns: list[str] = []
    if isinstance(settings, dict) and settings.get("parser") == "regex":
        raw_patterns = settings.get("regex", [])
        patterns = [raw_patterns] if isinstance(raw_patterns, str) else list(raw_patterns)
    elif isinstance(settings, str):
        patterns = [settings]
    elif isinstance(settings, list):
        patterns = [item for item in settings if isinstance(item, str)]
    for pattern in patterns:
        reference = _find_pattern_reference(
            read_result.pages,
            pattern,
            read_result.method,
            schema_id,
        )
        if reference:
            return reference
    display, _normalized = _normalize_value(value)
    return _find_text_reference(
        read_result.pages,
        display,
        read_result.method,
        schema_id,
    )


def _find_pattern_reference(
    pages: tuple[str, ...],
    pattern: str,
    method: str,
    schema_id: str,
) -> SourceReference | None:
    try:
        compiled = regex.compile(pattern, regex.MULTILINE)
    except regex.error:
        return None
    for page_number, page in enumerate(pages, start=1):
        match = compiled.search(page)
        if match:
            return _reference_at(page, match.start(), page_number, method, schema_id)
    return None


def _find_text_reference(
    pages: tuple[str, ...],
    value: str,
    method: str,
    schema_id: str,
) -> SourceReference | None:
    if not value:
        return None
    folded_value = value.casefold()
    for page_number, page in enumerate(pages, start=1):
        offset = page.casefold().find(folded_value)
        if offset >= 0:
            return _reference_at(page, offset, page_number, method, schema_id)
    return None


def _reference_at(
    page: str,
    offset: int,
    page_number: int,
    method: str,
    schema_id: str,
) -> SourceReference:
    line_number = page.count("\n", 0, offset) + 1
    lines = page.splitlines()
    source_line = lines[line_number - 1].strip() if line_number <= len(lines) else ""
    return SourceReference(
        page=page_number,
        line=line_number,
        text=source_line,
        method=method,
        template=schema_id,
    )


def _normalize_value(value: Any) -> tuple[str, str | float | None]:
    if value is None:
        return "", None
    if isinstance(value, datetime):
        normalized = value.date().isoformat()
        return normalized, normalized
    if isinstance(value, date):
        normalized = value.isoformat()
        return normalized, normalized
    if isinstance(value, bool):
        text = str(value).lower()
        return text, text
    if isinstance(value, (int, float)):
        return str(value), float(value)
    text = str(value).strip()
    return text, text or None


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value
