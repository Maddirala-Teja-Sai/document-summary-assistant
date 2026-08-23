"""
Named Entity Recognition (NER) service.

Uses spaCy's ``en_core_web_sm`` model — lightweight (~50 MB RAM),
fast (~5 000–10 000 words/sec on CPU), and fits Render's free tier.

The spaCy ``nlp`` object is shared from ``app.state.nlp`` (loaded at
startup in ``main.py``) to avoid reloading the model on every request.
If ``app.state.nlp`` is unavailable (e.g. during unit tests), the
service falls back to loading the model directly.

Entity categories extracted
---------------------------
spaCy label → response key
  PERSON → persons
  ORG    → organizations
  GPE    → locations   (geo-political entities: cities, countries)
  DATE   → dates
  MONEY  → money

Return contract
---------------
``extract_entities(text)`` → ``dict`` matching :class:`app.api.schemas.EntityResult`::

    {
        "persons":       list[str],
        "organizations": list[str],
        "dates":         list[str],
        "locations":     list[str],
        "money":         list[str],
    }
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# spaCy entity labels we care about → response key
_LABEL_MAP: dict[str, str] = {
    "PERSON": "persons",
    "ORG":    "organizations",
    "GPE":    "locations",
    "DATE":   "dates",
    "MONEY":  "money",
}

# Minimum character length for an entity to be included
_MIN_ENTITY_LEN: int = 2

# Common technical terms often misclassified as PERSON or LOCATION by small models
_TECH_FALSE_POSITIVES: set[str] = {
    "java", "python", "javascript", "react", "html", "css", "c++", "c#",
    "sql", "nosql", "mongodb", "mysql", "postgresql", "docker", "kubernetes",
    "keras", "tensorflow", "scikit", "scikit-learn", "pytorch", "pandas",
    "numpy", "ai", "ml", "dl", "nlp", "cnn", "rnn", "lstm", "svm", "knn",
    "git", "github", "gitlab", "jupyter", "vscode", "intellij", "vercel",
    "aws", "azure", "gcp", "linux", "rest", "api", "json", "xml", "atlas",
    "view website", "read full paper", "code", "leetcode", "ui", "ux",
}

# Maximum characters of input text sent to spaCy
# (prevents very long docs from being slow; NER is applied to first N chars)
_MAX_NER_CHARS: int = 50_000


def _get_nlp():
    """
    Return the shared spaCy ``Language`` object.

    Tries ``app.state.nlp`` first (set during FastAPI lifespan startup).
    Falls back to loading the model directly if not available.
    """
    try:
        # Works inside a running FastAPI request context
        from fastapi import Request  # noqa: PLC0415
        # We can't access `request` here, so try the global app state
        from app.main import app  # noqa: PLC0415
        nlp = getattr(app.state, "nlp", None)
        if nlp is not None:
            return nlp
    except Exception:  # noqa: BLE001
        pass

    # Fallback: load directly (used in tests / scripts)
    import spacy  # noqa: PLC0415
    from app.config import SPACY_MODEL  # noqa: PLC0415

    logger.info("Loading spaCy model '%s' directly (not from app.state).", SPACY_MODEL)
    nlp = spacy.load(
        SPACY_MODEL,
        disable=["tagger", "parser", "lemmatizer", "attribute_ruler"],
    )
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")
    return nlp


def _clean_entity(text: str) -> str:
    """Strip whitespace and normalise internal spaces."""
    return " ".join(text.split())


def extract_entities(text: str) -> dict[str, list[str]]:
    """
    Extract and categorise named entities from *text*.

    Args:
        text: The full extracted document text.

    Returns:
        A dict with keys ``persons``, ``organizations``, ``dates``,
        ``locations``, ``money`` — each a deduplicated, sorted list of strings.
        Empty lists are returned for categories with no matches.
    """
    # Initialise result buckets
    result: dict[str, set[str]] = {key: set() for key in _LABEL_MAP.values()}

    if not text or not text.strip():
        return {k: [] for k in result}

    nlp = _get_nlp()

    # Truncate to avoid long-running NER on huge documents
    truncated = text[:_MAX_NER_CHARS]
    doc = nlp(truncated)

    for ent in doc.ents:
        key = _LABEL_MAP.get(ent.label_)
        if key is None:
            continue  # Skip entity types we don't care about

        cleaned = _clean_entity(ent.text)
        lower_cleaned = cleaned.lower().strip()

        if len(cleaned) < _MIN_ENTITY_LEN:
            continue

        # Avoid tagging common tools/frameworks/headings as persons or locations
        if key in ("persons", "locations") and lower_cleaned in _TECH_FALSE_POSITIVES:
            continue

        result[key].add(cleaned)

    # Convert sets → sorted lists for deterministic JSON output
    final: dict[str, list[str]] = {k: sorted(v) for k, v in result.items()}

    logger.debug(
        "NER complete: %d persons, %d orgs, %d dates, %d locations, %d money",
        len(final["persons"]),
        len(final["organizations"]),
        len(final["dates"]),
        len(final["locations"]),
        len(final["money"]),
    )
    return final
