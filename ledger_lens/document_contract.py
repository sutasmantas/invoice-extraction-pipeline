from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import Any

from portfolio_document_contract import (
    Budget,
    Capabilities,
    DocumentRequest,
    MalformedDocumentError,
    ParsedDocument,
    ParsedPage,
    ParserIdentity,
    ParserOutcome,
    ParserUnavailableError,
    UnsupportedFormatError,
    execute,
)


def _media_type(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }.get(path.suffix.lower(), "application/octet-stream")


def normalize_path(
    path: Path,
    reader: Callable[[], Any],
    *,
    budget: Budget | None = None,
) -> tuple[dict, Any | None]:
    """Run Ledger's selected reader through the Atlas-owned shared contract."""

    request = DocumentRequest(path.read_bytes(), path.name, _media_type(path))
    declared = ParserIdentity("ledger-reader", "1", "none")
    captured: list[Any] = []

    def adapt(_request: DocumentRequest) -> ParserOutcome:
        try:
            read_result = reader()
        except ValueError as error:
            message = str(error)
            if "Supported types" in message:
                raise UnsupportedFormatError(message) from error
            if "Tesseract is required" in message:
                raise ParserUnavailableError(message) from error
            if "produced no text" in message:
                from portfolio_document_contract import EmptyDocumentError

                raise EmptyDocumentError(message) from error
            raise MalformedDocumentError(message) from error
        except Exception as error:
            raise MalformedDocumentError(
                f"{type(error).__name__}: document could not be read"
            ) from error
        captured.append(read_result)
        method = str(read_result.method)
        is_ocr = method in {"pdf_ocr", "image_ocr"}
        route = "quality" if is_ocr else "fast"
        if method == "pdf_ocr":
            parser_version = (
                f"pypdfium2={version('pypdfium2')};pytesseract={version('pytesseract')}"
            )
        elif is_ocr:
            parser_version = f"pytesseract={version('pytesseract')}"
        elif method == "pdf_text":
            parser_version = f"pypdfium2={version('pypdfium2')}"
        else:
            parser_version = "ledger-text=1"
        identity = ParserIdentity(method, parser_version, route)
        pages = tuple(
            ParsedPage(page_number=index, text=text, markdown=text)
            for index, text in enumerate(read_result.pages, start=1)
        )
        paged_formats = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff"}
        page_boundaries = "exact" if path.suffix.lower() in paged_formats else "inferred"
        document = ParsedDocument(
            document_format=path.suffix.lower().lstrip(".") or "unknown",
            pages=pages,
            capabilities=Capabilities(
                page_boundaries=page_boundaries,
                tables="flattened",
                coordinates="unavailable",
                ocr=is_ocr,
            ),
        )
        return ParserOutcome(identity, document)

    result = execute(
        request,
        adapt,
        declared_parser=declared,
        budget=budget,
    )
    return result, captured[0] if captured else None
