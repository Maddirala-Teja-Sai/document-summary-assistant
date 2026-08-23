"""
File type detection and validation utilities.

Responsibilities:
  - Detect true file type via magic bytes (not just extension)
  - Validate file size (enforced upstream in routes, double-checked here)
  - Provide a safe temp-file context manager for OCR operations
"""

from __future__ import annotations

import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Magic byte signatures for supported file types
# ---------------------------------------------------------------------------
# Each entry: (offset, bytes_to_match, label)
_MAGIC_SIGNATURES: list[tuple[int, bytes, str]] = [
    (0, b"%PDF",              "pdf"),
    (0, b"\x89PNG\r\n\x1a\n", "image"),   # PNG
    (0, b"\xff\xd8\xff",      "image"),   # JPEG / JFIF / EXIF
    (0, b"II\x2a\x00",        "image"),   # TIFF little-endian
    (0, b"MM\x00\x2a",        "image"),   # TIFF big-endian
    (0, b"BM",                "image"),   # BMP
]


def detect_file_type(file_bytes: bytes) -> str:
    """
    Inspect the file's magic bytes and return ``"pdf"`` or ``"image"``.

    Args:
        file_bytes: Raw bytes of the uploaded file.

    Returns:
        ``"pdf"`` or ``"image"``.

    Raises:
        ValueError: If the byte signature does not match any supported format.
    """
    header = file_bytes[:16]

    for offset, signature, label in _MAGIC_SIGNATURES:
        if header[offset: offset + len(signature)] == signature:
            logger.debug("Detected file type: %s", label)
            return label

    raise ValueError(
        "Unsupported or unrecognised file format. "
        "Only PDF, PNG, JPEG, TIFF, and BMP files are accepted."
    )


def validate_file_size(file_bytes: bytes, max_bytes: int) -> None:
    """
    Raise ValueError if the file exceeds the maximum allowed size.

    Args:
        file_bytes: Raw bytes of the file.
        max_bytes:  Maximum permitted size in bytes.
    """
    size = len(file_bytes)
    if size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size / (1024 * 1024)
        raise ValueError(
            f"File size {actual_mb:.1f} MB exceeds the {max_mb:.0f} MB limit."
        )


@contextmanager
def temp_file(
    file_bytes: bytes,
    suffix: str = "",
) -> Generator[Path, None, None]:
    """
    Write *file_bytes* to a named temporary file and yield its :class:`Path`.

    The file is automatically deleted when the context exits, even if an
    exception is raised.

    Args:
        file_bytes: Bytes to write to the temp file.
        suffix:     File extension suffix (e.g. ``".png"``).

    Yields:
        :class:`pathlib.Path` pointing to the temporary file.

    Example::

        with temp_file(raw_bytes, suffix=".png") as path:
            text = pytesseract.image_to_string(str(path))
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(file_bytes)
        tmp.flush()
        tmp.close()
        yield Path(tmp.name)
    finally:
        try:
            Path(tmp.name).unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Could not delete temp file %s: %s", tmp.name, exc)
