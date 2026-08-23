"""
Pydantic request/response schemas for the Document Summary Assistant API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class SummaryResponse(BaseModel):
    """Response for a single document summarization request."""
    filename: str = Field(description="Original uploaded filename")
    document_type: str = Field(description="Detected document type (e.g. resume, contract)")
    document_type_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for the detected document type (0–1)"
    )
    summary: str = Field(description="Bullet-point summary of the document")
    key_sentences: list[str] = Field(
        description="Key sentences (verbatim from document)"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable improvement suggestions for the document"
    )
    word_count: int = Field(description="Word count of the extracted text")
    processing_time_ms: int = Field(description="Total server-side processing time in milliseconds")
    analysis_source: str = Field(
        default="groq",
        description="'groq' if powered by Groq LLM, 'local_fallback' if API was unavailable"
    )


class BatchResponse(BaseModel):
    """Response for a batch (multiple documents) summarization request."""
    total_files: int = Field(description="Number of files processed")
    successful: int = Field(description="Number of files successfully summarized")
    failed: int = Field(description="Number of files that failed processing")
    results: list[SummaryResponse | ErrorResponse] = Field(
        description="Per-file results. Failed files return an ErrorResponse."
    )
    total_processing_time_ms: int = Field(description="Total time for the entire batch")


class PDFExportRequest(BaseModel):
    """Request body for the /api/export-pdf endpoint."""
    filename: str
    document_type: str
    summary: str
    key_sentences: list[str]
    suggestions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Structured error response returned for failed requests."""
    filename: str | None = Field(default=None, description="Filename if error is file-specific")
    detail: str = Field(description="Human-readable error message")
    error_code: str = Field(description="Machine-readable error code")
