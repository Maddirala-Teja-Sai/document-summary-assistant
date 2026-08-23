"""
API route definitions for the Document Summary Assistant.

Primary path:  Groq Llama 3.3 70B (abstractive summary + classification + NER)
Fallback path: Local pipeline (TextRank + keywords + spaCy)

The fallback is triggered automatically if:
  - GROQ_API_KEY is not set
  - The Groq API returns an error or times out
  - The groq package is not installed
"""

from __future__ import annotations

import logging
import time
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from app.api.schemas import (
    BatchResponse,
    ErrorResponse,
    PDFExportRequest,
    SummaryResponse,
)
from app.config import (
    ALLOWED_EXTENSIONS,
    DEFAULT_SUMMARY_LENGTH,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_REQUEST,
    SUMMARY_LENGTHS,
)

router = APIRouter(prefix="/api", tags=["summarize"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File validation helpers
# ---------------------------------------------------------------------------

def _validate_extension(filename: str) -> None:
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )


async def _read_upload(file: UploadFile) -> bytes:
    _validate_extension(file.filename or "unknown")
    contents = bytearray()
    chunk_size = 1024 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        contents.extend(chunk)
        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"'{file.filename}' exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit.",
            )
    return bytes(contents)


# ---------------------------------------------------------------------------
# Local fallback pipeline
# ---------------------------------------------------------------------------

def _local_pipeline(raw_text: str, length: str) -> dict:
    """
    Run the local pipeline (TextRank + keyword classification).
    Used when Groq API is unavailable.
    """
    from app.services.classification import classify_document
    from app.services.summarizer import extractive_summary

    sentence_count = SUMMARY_LENGTHS.get(length, SUMMARY_LENGTHS[DEFAULT_SUMMARY_LENGTH])["sentences"]
    doc_type, confidence = classify_document(raw_text)
    key_sentences = extractive_summary(raw_text, sentence_count)
    summary = "\n".join(f"• {s}" for s in key_sentences)

    suggestions_by_type = {
        "resume": [
            "Add measurable metrics and quantified outcomes to key accomplishments.",
            "Ensure core technical skills and tools are prominently listed near the top.",
            "Verify contact links (GitHub, LinkedIn, Portfolio) are easily accessible."
        ],
        "contract": [
            "Ensure dispute resolution and termination clauses are clearly stated.",
            "Check that all payment milestones and deliverables have explicit dates.",
            "Review governing law and jurisdiction terms for enforceability."
        ],
        "research paper": [
            "Clarify the specific problem statement in the introductory sections.",
            "Provide quantitative benchmarks against state-of-the-art baselines.",
            "Include explicit discussion on methodology limitations and future work."
        ],
    }
    suggestions = suggestions_by_type.get(doc_type, [
        "Enhance document readability using structured headers and bullet points.",
        "Ensure the core purpose and key takeaways are clearly stated upfront.",
        "Review grammar, terminology consistency, and section formatting."
    ])

    return {
        "document_type":            doc_type,
        "document_type_confidence": confidence,
        "summary":                  summary,
        "key_sentences":            key_sentences,
        "suggestions":              suggestions,
        "analysis_source":         "local_fallback",
    }


# ---------------------------------------------------------------------------
# Core processing — Groq primary, local fallback
# ---------------------------------------------------------------------------

async def _process_single(
    file_bytes: bytes,
    filename: str,
    length: str,
) -> SummaryResponse:
    from app.services.llm_service import LLMUnavailableError, llm_analyse
    from app.services.text_extraction import extract_text
    from app.utils.file_handler import detect_file_type

    start = time.monotonic()

    # Step 1 — detect file type
    file_type = await run_in_threadpool(detect_file_type, file_bytes)

    # Step 2 — extract text (always local: PyPDF2 / pytesseract)
    extraction = await run_in_threadpool(extract_text, file_bytes, file_type)
    raw_text: str = extraction["text"]

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract any text from '{filename}'.",
        )

    # Step 3 — try Groq first, fall back to local pipeline
    analysis_source = "groq"
    try:
        result_data = await run_in_threadpool(llm_analyse, raw_text, length)
        result_data["analysis_source"] = "groq"
        logger.info("Groq analysis succeeded for '%s'", filename)
    except LLMUnavailableError as e:
        logger.warning("Groq unavailable (%s) — using local fallback for '%s'", e, filename)
        result_data = await run_in_threadpool(_local_pipeline, raw_text, length)
        analysis_source = "local_fallback"
    except Exception as e:
        logger.error("Unexpected error from Groq (%s) — using local fallback for '%s'", e, filename)
        result_data = await run_in_threadpool(_local_pipeline, raw_text, length)
        analysis_source = "local_fallback"

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return SummaryResponse(
        filename=filename,
        document_type=result_data["document_type"],
        document_type_confidence=result_data["document_type_confidence"],
        summary=result_data["summary"],
        key_sentences=result_data["key_sentences"],
        suggestions=result_data.get("suggestions", []),
        word_count=len(raw_text.split()),
        processing_time_ms=elapsed_ms,
        analysis_source=analysis_source,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health", summary="Health check")
async def health_check() -> dict:
    from app.config import GROQ_API_KEY
    return {
        "status": "ok",
        "version": "2.0.0",
        "groq_enabled": bool(GROQ_API_KEY),
    }


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    summary="Summarize a single document",
    status_code=status.HTTP_200_OK,
)
async def summarize(
    file: Annotated[UploadFile, File(description="PDF or image file to summarize")],
    length: Annotated[str, Form(description="Summary length: short | medium | long")] = DEFAULT_SUMMARY_LENGTH,
) -> SummaryResponse:
    if length not in SUMMARY_LENGTHS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid length '{length}'. Choose from: {list(SUMMARY_LENGTHS.keys())}",
        )
    file_bytes = await _read_upload(file)
    await file.close()
    return await _process_single(file_bytes, file.filename or "document", length)


@router.post(
    "/batch-summarize",
    response_model=BatchResponse,
    summary="Summarize multiple documents",
    status_code=status.HTTP_200_OK,
)
async def batch_summarize(
    files: Annotated[list[UploadFile], File(description="PDF or image files (max 5)")],
    length: Annotated[str, Form(description="Summary length: short | medium | long")] = DEFAULT_SUMMARY_LENGTH,
) -> BatchResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum is {MAX_FILES_PER_REQUEST}.",
        )
    if length not in SUMMARY_LENGTHS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid length '{length}'. Choose from: {list(SUMMARY_LENGTHS.keys())}",
        )

    batch_start = time.monotonic()
    results: list = []
    successful = 0
    failed = 0

    for file in files:
        try:
            file_bytes = await _read_upload(file)
            await file.close()
            result = await _process_single(file_bytes, file.filename or "document", length)
            results.append(result)
            successful += 1
        except HTTPException as exc:
            results.append(ErrorResponse(filename=file.filename, detail=exc.detail, error_code=f"HTTP_{exc.status_code}"))
            failed += 1
        except Exception as exc:
            results.append(ErrorResponse(filename=file.filename, detail=f"Unexpected error: {exc}", error_code="INTERNAL_ERROR"))
            failed += 1

    return BatchResponse(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=results,
        total_processing_time_ms=int((time.monotonic() - batch_start) * 1000),
    )


@router.post(
    "/export-pdf",
    summary="Export summary as a PDF",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
async def export_pdf(payload: PDFExportRequest) -> Response:
    from app.utils.pdf_export import generate_summary_pdf
    pdf_bytes: bytes = await run_in_threadpool(generate_summary_pdf, payload)
    safe_name = payload.filename.rsplit(".", 1)[0] + "_summary.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
