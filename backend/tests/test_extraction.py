"""
Tests for text_extraction.py and file_handler.py (Component 2).

Run with:
    cd backend
    pytest tests/test_extraction.py -v
"""

from __future__ import annotations

import io

import pytest


# ---------------------------------------------------------------------------
# Helpers — build minimal valid file bytes for testing
# ---------------------------------------------------------------------------

def _minimal_pdf_bytes(text: str = "Hello, world!") -> bytes:
    """
    Generate a minimal but valid single-page PDF containing *text*.
    Uses ReportLab so no external fixtures are needed.
    """
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


def _png_bytes() -> bytes:
    """Return a tiny 1×1 white PNG."""
    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# file_handler tests
# ---------------------------------------------------------------------------

class TestDetectFileType:
    def test_detects_pdf(self):
        from app.utils.file_handler import detect_file_type
        pdf = _minimal_pdf_bytes()
        assert detect_file_type(pdf) == "pdf"

    def test_detects_png(self):
        from app.utils.file_handler import detect_file_type
        png = _png_bytes()
        assert detect_file_type(png) == "image"

    def test_rejects_unknown(self):
        from app.utils.file_handler import detect_file_type
        with pytest.raises(ValueError, match="Unsupported"):
            detect_file_type(b"this is not a real file")


class TestValidateFileSize:
    def test_passes_under_limit(self):
        from app.utils.file_handler import validate_file_size
        validate_file_size(b"x" * 100, max_bytes=1000)  # should not raise

    def test_raises_over_limit(self):
        from app.utils.file_handler import validate_file_size
        with pytest.raises(ValueError, match="exceeds"):
            validate_file_size(b"x" * 1001, max_bytes=1000)


class TestTempFile:
    def test_creates_and_cleans_up(self, tmp_path):
        from app.utils.file_handler import temp_file
        from pathlib import Path

        captured_path: list[Path] = []

        with temp_file(b"test data", suffix=".txt") as p:
            captured_path.append(p)
            assert p.exists()
            assert p.read_bytes() == b"test data"

        # After context exits the file must be gone
        assert not captured_path[0].exists()


# ---------------------------------------------------------------------------
# text_extraction tests
# ---------------------------------------------------------------------------

class TestExtractTextPDF:
    def test_extracts_text_from_pdf(self):
        from app.services.text_extraction import extract_text
        pdf = _minimal_pdf_bytes("Unit test PDF content")
        result = extract_text(pdf, "pdf")
        assert result["source"] == "pdf"
        assert result["page_count"] == 1
        # ReportLab embeds the text; PyPDF2 should find at least part of it
        assert len(result["text"]) > 0

    def test_returns_correct_keys(self):
        from app.services.text_extraction import extract_text
        result = extract_text(_minimal_pdf_bytes(), "pdf")
        assert {"text", "source", "page_count"} <= result.keys()

    def test_raises_on_unknown_type(self):
        from app.services.text_extraction import extract_text
        with pytest.raises(ValueError, match="Unknown file type"):
            extract_text(b"data", "video")


class TestExtractTextImage:
    def test_returns_ocr_source_for_image(self):
        """
        OCR on a blank 1×1 image won't find text, but it should return
        the correct source key without raising.
        """
        from app.services.text_extraction import extract_text
        png = _png_bytes()
        result = extract_text(png, "image")
        assert result["source"] == "ocr"
        assert result["page_count"] == 1
        assert isinstance(result["text"], str)
