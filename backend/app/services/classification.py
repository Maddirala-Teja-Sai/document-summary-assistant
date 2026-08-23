"""
Document type classification service.

Uses keyword-based heuristic matching — no ML model, no external calls,
runs in microseconds and fits comfortably in Render's free tier.

Strategy
--------
Each document type has a set of discriminating keywords. We lowercase
the input text and count how many keywords appear. The score for each
type is ``matches / total_keywords`` (normalised hit-rate). The type
with the highest score wins; ties are broken by the order in
``DOCUMENT_PATTERNS`` (most-specific first).

Return contract
---------------
``classify_document(text)`` → ``(label: str, confidence: float)``

  - *label*:      human-readable document type, e.g. ``"resume"``
  - *confidence*: normalised hit-rate in ``[0.0, 1.0]``
                  (0.0 means no keyword matched → "general document")
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword patterns
# Order matters for tie-breaking — more specific types listed first.
# ---------------------------------------------------------------------------
DOCUMENT_PATTERNS: dict[str, list[str]] = {
    "resume": [
        "experience", "education", "skills", "objective", "references",
        "certifications", "gpa", "internship", "achievements", "projects",
        "summary", "work history", "employment", "volunteer", "linkedin",
    ],
    "cover letter": [
        "dear hiring manager", "dear recruiter", "i am writing",
        "position", "enclosed", "application", "sincerely", "regards",
        "enthusiasm", "opportunity", "interview", "look forward",
    ],
    "research paper": [
        "abstract", "methodology", "findings", "conclusion", "hypothesis",
        "literature review", "doi", "keywords", "introduction", "results",
        "discussion", "references", "citations", "journal", "experiment",
        "data analysis", "statistical", "figure", "table",
    ],
    "contract": [
        "agreement", "party", "clause", "whereas", "obligations",
        "termination", "governing law", "herein", "indemnification",
        "liability", "breach", "confidentiality", "jurisdiction",
        "effective date", "hereinafter", "warranties", "consideration",
    ],
    "invoice": [
        "invoice", "bill to", "due date", "subtotal", "tax",
        "total", "payment terms", "qty", "quantity", "unit price",
        "amount due", "purchase order", "vendor", "remit", "receipt",
    ],
    "report": [
        "executive summary", "recommendations", "analysis", "overview",
        "key findings", "metrics", "performance", "quarterly",
        "annual report", "dashboard", "kpi", "forecast",
    ],
    "letter": [
        "dear", "sincerely", "regards", "to whom it may concern",
        "yours truly", "faithfully", "best regards", "warmly",
    ],
    "article": [
        "published", "editor", "columnist", "journalist", "byline",
        "headline", "subheading", "reported by", "staff writer",
    ],
    "manual": [
        "installation", "instructions", "step", "chapter", "appendix",
        "troubleshooting", "user guide", "configuration", "setup",
        "prerequisites", "warning", "note", "tip", "caution",
    ],
}


def _normalise(text: str) -> str:
    """Lower-case and collapse whitespace for reliable keyword matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify_document(text: str) -> tuple[str, float]:
    """
    Classify a document by keyword frequency.

    Args:
        text: The full extracted text of the document.

    Returns:
        A ``(label, confidence)`` tuple where:
          - *label* is the detected document type (string).
          - *confidence* is a float in ``[0.0, 1.0]`` representing the
            normalised keyword hit-rate of the winning category.
          - If no keywords match, returns ``("general document", 0.0)``.
    """
    if not text or not text.strip():
        return ("general document", 0.0)

    normalised = _normalise(text)
    scores: dict[str, float] = {}

    for doc_type, keywords in DOCUMENT_PATTERNS.items():
        hits = sum(1 for kw in keywords if kw in normalised)
        scores[doc_type] = hits / len(keywords)

    best_type = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_score = scores[best_type]

    if best_score == 0.0:
        logger.debug("No keyword matches — defaulting to 'general document'.")
        return ("general document", 0.0)

    logger.debug(
        "Classified as '%s' (confidence=%.2f). All scores: %s",
        best_type, best_score,
        {k: round(v, 3) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
    )
    return (best_type, round(best_score, 4))


def get_summary_focus(doc_type: str) -> str:
    """
    Return a short focus hint for the given document type.
    Used to prepend context when displaying or labelling the summary.

    Args:
        doc_type: Label returned by :func:`classify_document`.

    Returns:
        A short descriptive string, e.g. ``"Skills, experience & education"``.
    """
    _FOCUS_MAP: dict[str, str] = {
        "resume":         "Skills, experience & education",
        "cover letter":   "Intent, qualifications & fit",
        "research paper": "Objective, methodology & findings",
        "contract":       "Parties, obligations & key terms",
        "invoice":        "Vendor, items, amounts & due dates",
        "report":         "Key findings & recommendations",
        "letter":         "Purpose & main message",
        "article":        "Main argument & key points",
        "manual":         "Steps, configuration & warnings",
        "general document": "Main ideas & key points",
    }
    return _FOCUS_MAP.get(doc_type, "Main ideas & key points")
