"""
Extractive summarization service using TextRank (via sumy).

TextRank builds a graph of sentence similarities using TF-IDF cosine
distance, then ranks sentences by their centrality (like PageRank for
text). The top-N sentences are returned in document order.

Key fix
-------
PDF-extracted text from resumes/docs often has NO spaces after periods
and uses newlines as sentence separators instead of `. `.
_preprocess_pdf_text() normalises this before handing off to sumy,
so the tokeniser sees proper sentence boundaries.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_MIN_SENTENCE_WORDS: int = 6       # discard very short / noisy sentences
_MAX_SENTENCE_WORDS: int = 80      # discard run-on "sentences" (whole paragraph)
_MAX_INPUT_CHARS: int = 100_000


def _preprocess_pdf_text(text: str) -> str:
    """
    Normalise PDF-extracted text so sumy's sentence tokeniser works correctly.

    Problems in raw PDF text:
    - Sections / bullet lines separated by \\n with no period
    - Periods immediately followed by capital letters and no space ("ML.Python")
    - Unicode bullets, dashes, and special chars
    - Multiple blank lines

    Strategy:
    1. Replace bullet/dash list markers with newlines
    2. Ensure each non-empty line ends with a period
    3. Collapse multiple newlines, then join lines with a space
    4. Fix missing spaces after periods
    """
    # Normalise unicode bullets and line-separating dashes
    text = re.sub(r'[•·▪‣⁃–—]\s*', '\n', text)

    # Remove soft-hyphen continuations
    text = re.sub(r'-\n\s*', '', text)

    # Split into lines and ensure each non-empty line ends with a period
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Add period if line doesn't end with sentence-terminating punctuation
        if line and not line[-1] in '.!?:;':
            line = line + '.'
        lines.append(line)

    # Rejoin with space so sumy sees one stream of `. `-terminated sentences
    joined = ' '.join(lines)

    # Fix missing space after period before capital letter
    # e.g. "ML.Python" → "ML. Python"
    joined = re.sub(r'\.([A-Z])', r'. \1', joined)

    # Collapse multiple spaces
    joined = re.sub(r' {2,}', ' ', joined)

    return joined.strip()


def _clean_text(text: str) -> str:
    """Light whitespace normalisation (used by tests and general input)."""
    text = re.sub(r'[\x0c\x0b]', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extractive_summary(text: str, sentence_count: int = 5) -> list[str]:
    """
    Return the *sentence_count* most central sentences from *text*,
    in document order, using TextRank.

    Args:
        text:           Full extracted document text.
        sentence_count: Number of sentences to return (clamped to available).

    Returns:
        List of sentence strings in document order.
        Returns [] if text is blank or has no parseable sentences.
    """
    import nltk
    from sumy.nlp.stemmers import Stemmer
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.summarizers.text_rank import TextRankSummarizer
    from sumy.utils import get_stop_words

    # Ensure NLTK data
    for resource in ('punkt', 'punkt_tab'):
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            nltk.download(resource, quiet=True)

    if not text or not text.strip():
        return []

    # Pre-process to give sumy proper sentence boundaries
    processed = _preprocess_pdf_text(text[:_MAX_INPUT_CHARS])

    parser = PlaintextParser.from_string(processed, Tokenizer('english'))
    all_sentences = list(parser.document.sentences)
    available = len(all_sentences)

    if available == 0:
        return []

    n = min(sentence_count, available)

    stemmer = Stemmer('english')
    summariser = TextRankSummarizer(stemmer)
    summariser.stop_words = get_stop_words('english')

    ranked = summariser(parser.document, n)

    # Restore document order
    sentence_texts = [str(s) for s in all_sentences]
    ranked_set = {str(s) for s in ranked}

    ordered: list[str] = []
    seen: set[str] = set()

    for s in sentence_texts:
        if s not in ranked_set or s in seen:
            continue
        words = s.split()
        word_count = len(words)
        # Filter: too short (noise) or too long (entire paragraph / bad parse)
        if _MIN_SENTENCE_WORDS <= word_count <= _MAX_SENTENCE_WORDS:
            ordered.append(s)
            seen.add(s)

    # Fallback: if all filtered out, return top-N by rank without word limit
    if not ordered:
        ordered = [str(s) for s in ranked if len(str(s).split()) >= _MIN_SENTENCE_WORDS]
        # If still nothing, include everything ranked
        if not ordered:
            ordered = [str(s) for s in ranked]

    logger.debug(
        'extractive_summary: requested=%d  available=%d  returned=%d',
        sentence_count, available, len(ordered),
    )
    return ordered
