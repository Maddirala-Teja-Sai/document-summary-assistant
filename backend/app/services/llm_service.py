"""
LLM analysis service — powered by Groq.

A single API call to Groq replaces separate local services
(TextRank summarization, keyword classification) and produces
abstractive summaries, accurate document type detection, and
actionable improvement suggestions.

Fallback
--------
If GROQ_API_KEY is not set or the API call fails for any reason,
``llm_analyse`` raises ``LLMUnavailableError`` and the caller
(routes.py) falls back to the local pipeline automatically.

Return contract
---------------
``llm_analyse(text, length)`` → ``dict`` matching SummaryResponse fields::

    {
        "document_type":            str,
        "document_type_confidence": float,
        "summary":                  str,   # bullet-point formatted
        "key_sentences":            list[str],
        "suggestions":              list[str],
    }
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

# Sentence counts per length setting (mirrors config.SUMMARY_LENGTHS)
_SENTENCE_COUNTS: dict[str, int] = {
    "short":  4,
    "medium": 7,
    "long":   12,
}

_MAX_INPUT_WORDS = 6_000   # stay well within token limits

# Candidate models in order of priority
FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound-mini",
]


class LLMUnavailableError(Exception):
    """Raised when the LLM service cannot be reached or is not configured."""


def _build_prompt(text: str, length: str) -> str:
    """Build the structured analysis prompt sent to the LLM."""
    sentence_count = _SENTENCE_COUNTS.get(length, 7)

    # Truncate very long documents
    words = text.split()
    if len(words) > _MAX_INPUT_WORDS:
        text = " ".join(words[:_MAX_INPUT_WORDS]) + "\n[Document truncated for brevity]"

    return f"""You are a precise document analysis and review assistant. Analyse the document below and respond with ONLY a valid JSON object — no markdown, no explanation, no code fences.

Required JSON schema:
{{
  "document_type": "<one of: resume, cover_letter, research_paper, contract, invoice, report, letter, article, manual, general_document>",
  "document_type_confidence": <float 0.0 to 1.0>,
  "summary": "<abstractive summary — {sentence_count} sentences capturing key points in clean professional language>",
  "key_sentences": ["<verbatim key sentence 1 from document>", "<verbatim key sentence 2>", ...],
  "suggestions": [
    "<actionable suggestion 1 to improve content, clarity, structure, or completeness>",
    "<actionable suggestion 2>",
    "<actionable suggestion 3>"
  ]
}}

Rules:
- "summary" must be abstractive (rewritten concisely in your own words, capturing the actual core information)
- "key_sentences" should be {sentence_count} of the most important verbatim sentences directly from the document
- "suggestions" should be 3 to 4 specific, actionable tips tailored to this document type (e.g., adding metrics to resume bullets, clarifying clauses in a contract, formatting headers)
- Output valid JSON only

DOCUMENT:
{text}"""


def _parse_response(raw: str) -> dict:
    """
    Extract and parse the JSON object from the LLM response.
    Handles cases where the model wraps the JSON in markdown fences.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find a JSON object within the response
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse JSON from LLM response: {cleaned[:200]}")

    return data


def _validate_and_normalise(data: dict, length: str) -> dict:
    """
    Ensure the parsed response has all required fields with correct types.
    Fills in safe defaults for any missing/malformed fields.
    """
    # Normalise document_type
    doc_type = str(data.get("document_type", "general_document")).lower().replace(" ", "_")
    valid_types = {
        "resume", "cover_letter", "research_paper", "contract",
        "invoice", "report", "letter", "article", "manual", "general_document",
    }
    if doc_type not in valid_types:
        doc_type = "general_document"
    # Convert underscores back to spaces for display
    doc_type_display = doc_type.replace("_", " ")

    confidence = float(data.get("document_type_confidence", 0.85))
    confidence = max(0.0, min(1.0, confidence))

    # Summary — should be a string
    summary_raw = data.get("summary", "")
    if not isinstance(summary_raw, str):
        summary_raw = str(summary_raw)

    # Key sentences — should be a list of strings
    key_sentences = data.get("key_sentences", [])
    if not isinstance(key_sentences, list):
        key_sentences = [str(key_sentences)]
    key_sentences = [str(s).strip() for s in key_sentences if str(s).strip()]

    # Suggestions — should be a list of strings
    suggestions = data.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = [str(suggestions)]
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()]

    # If summary is empty but we have key sentences, build it from them
    if not summary_raw.strip() and key_sentences:
        summary_raw = " ".join(key_sentences)

    # Format summary as bullet points
    summary_bullets = "\n".join(f"• {s.strip()}" for s in summary_raw.split(". ") if s.strip())
    if not summary_bullets:
        summary_bullets = f"• {summary_raw}"

    return {
        "document_type":            doc_type_display,
        "document_type_confidence": round(confidence, 4),
        "summary":                  summary_bullets,
        "key_sentences":            key_sentences,
        "suggestions":              suggestions,
    }


def llm_analyse(text: str, length: str = "medium") -> dict:
    """
    Send the document to Groq for analysis.

    Args:
        text:   Extracted document text.
        length: "short" | "medium" | "long" — controls summary verbosity.

    Returns:
        Dict with keys: document_type, document_type_confidence, summary,
        key_sentences, suggestions.

    Raises:
        LLMUnavailableError: If GROQ_API_KEY is not set or the API fails.
    """
    try:
        from groq import Groq, APIError, APIConnectionError, RateLimitError
    except ImportError:
        raise LLMUnavailableError(
            "groq package not installed. Run: pip install groq"
        )

    from app.config import GROQ_API_KEY, GROQ_MODEL, GROQ_TIMEOUT

    if not GROQ_API_KEY:
        raise LLMUnavailableError(
            "GROQ_API_KEY environment variable is not set. "
            "Get a free key at https://console.groq.com"
        )

    if not text or not text.strip():
        raise ValueError("Cannot analyse empty document text.")

    client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT)
    prompt = _build_prompt(text, length)

    models_to_try = [GROQ_MODEL] + [m for m in FALLBACK_MODELS if m != GROQ_MODEL]
    last_error = None

    for model in models_to_try:
        try:
            logger.info("Calling Groq API (model=%s, length=%s)", model, length)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise document analysis assistant. "
                            "You always respond with valid JSON only — no markdown, "
                            "no explanation, no code fences."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content or ""
            parsed = _parse_response(raw_content)
            return _validate_and_normalise(parsed, length)
        except (RateLimitError, APIError, APIConnectionError, Exception) as e:
            logger.warning("Groq call failed with model %s: %s", model, e)
            last_error = e
            continue

    raise LLMUnavailableError(f"All Groq models failed. Last error: {last_error}") from last_error
