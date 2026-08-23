"""
Text extraction service.

Handles two document sources:
  1. PDF  — uses PyPDF2 to extract text directly from the PDF structure.
             If the extracted text is suspiciously short (< MIN_TEXT_CHARS),
             the PDF is assumed to be a scanned image and routed to OCR.
  2. Image — uses pytesseract (wrapping system Tesseract) to perform OCR.

Return contract
---------------
All public functions return a dict::

    {
        "text":       str,                  # extracted / OCR'd text
        "source":     "pdf" | "ocr",        # how the text was obtained
        "page_count": int,                  # number of pages (PDF) or 1 (image)
    }
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)

# Minimum number of characters extracted from a PDF page before we treat
# it as a scanned / image-only PDF and fall back to OCR.
MIN_TEXT_CHARS: int = 50


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def _extract_from_pdf(file_bytes: bytes) -> dict:
    """
    Extract text from a PDF using PyPDF2.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        Dict with keys ``text``, ``source``, ``page_count``.
    """
    import PyPDF2  # imported lazily to keep startup fast

    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)
    pages: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text.strip())

    full_text = "\n\n".join(p for p in pages if p)
    logger.debug("PDF extraction: %d pages, %d chars", page_count, len(full_text))

    return {
        "text": full_text,
        "source": "pdf",
        "page_count": page_count,
    }


# ---------------------------------------------------------------------------
# OCR extraction
# ---------------------------------------------------------------------------

def _extract_via_ocr(file_bytes: bytes, suffix: str = ".png") -> dict:
    """
    Run Tesseract OCR on an image (or scanned PDF page rendered as image).

    Args:
        file_bytes: Raw bytes of the image file.
        suffix:     File extension hint for the temp file (e.g. ``".jpg"``).

    Returns:
        Dict with keys ``text``, ``source`` (``"ocr"``), ``page_count`` (1).
    """
    import pytesseract
    from PIL import Image

    from app.utils.file_handler import temp_file

    try:
        # Try opening directly via PIL (works for PNG, JPEG, TIFF, BMP)
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        text = pytesseract.image_to_string(image, lang="eng")
    except Exception:  # noqa: BLE001
        # Fallback: write to disk and let Tesseract open it natively
        with temp_file(file_bytes, suffix=suffix) as path:
            text = pytesseract.image_to_string(str(path), lang="eng")

    cleaned = text.strip()
    logger.debug("OCR extraction: %d chars", len(cleaned))

    return {
        "text": cleaned,
        "source": "ocr",
        "page_count": 1,
    }


# ---------------------------------------------------------------------------
# Scanned-PDF OCR
# ---------------------------------------------------------------------------

def _ocr_scanned_pdf(file_bytes: bytes) -> dict:
    """
    Convert each page of a scanned PDF to an image, then OCR each page.

    Uses pdf2image (poppler) if available; falls back to extracting what
    PyPDF2 found (which may be empty) if pdf2image is not installed.

    Args:
        file_bytes: Raw bytes of the scanned PDF.

    Returns:
        Dict with keys ``text``, ``source`` (``"ocr"``), ``page_count``.
    """
    try:
        from pdf2image import convert_from_bytes  # optional dependency
        import pytesseract

        images = convert_from_bytes(file_bytes, dpi=200)
        page_texts: list[str] = []

        for img in images:
            page_text = pytesseract.image_to_string(img.convert("RGB"), lang="eng")
            page_texts.append(page_text.strip())

        full_text = "\n\n".join(t for t in page_texts if t)
        logger.debug(
            "Scanned-PDF OCR: %d pages, %d chars", len(images), len(full_text)
        )
        return {
            "text": full_text,
            "source": "ocr",
            "page_count": len(images),
        }

    except ImportError:
        # pdf2image / poppler not available — return what PyPDF2 found
        logger.warning(
            "pdf2image not installed. Scanned PDF will have limited text. "
            "Install pdf2image and poppler for full scanned-PDF support."
        )
        result = _extract_from_pdf(file_bytes)
        result["source"] = "ocr"
        return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def extract_text(file_bytes: bytes, file_type: str) -> dict:
    """
    Extract text from a document, routing to the correct strategy.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        file_type:  ``"pdf"`` or ``"image"`` as returned by
                    :func:`app.utils.file_handler.detect_file_type`.

    Returns:
        Dict::

            {
                "text":       str,
                "source":     "pdf" | "ocr",
                "page_count": int,
            }

    Raises:
        ValueError: If *file_type* is not recognised.
    """
    if file_type == "pdf":
        result = _extract_from_pdf(file_bytes)

        # If PDF yields almost no text it's likely scanned — try OCR
        if len(result["text"].strip()) < MIN_TEXT_CHARS:
            logger.info(
                "PDF text too short (%d chars) — treating as scanned PDF, running OCR.",
                len(result["text"].strip()),
            )
            ocr_result = _ocr_scanned_pdf(file_bytes)
            # Keep page_count from original PDF read
            ocr_result["page_count"] = result["page_count"]
            return ocr_result

        return result

    if file_type == "image":
        return _extract_via_ocr(file_bytes)

    raise ValueError(f"Unknown file type: '{file_type}'. Expected 'pdf' or 'image'.")
