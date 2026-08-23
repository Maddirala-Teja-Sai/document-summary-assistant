"""
Tests for summarizer.py and pdf_export.py (Component 4).

Also includes the end-to-end pipeline test (test_pipeline.py content
lives here for simplicity).

Run with:
    cd backend
    pytest tests/test_pipeline.py -v
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LONG_TEXT = """
Machine learning is a branch of artificial intelligence that focuses on building
systems that can learn from data. Unlike traditional programming, where explicit
rules are coded by hand, machine learning algorithms identify patterns in large
datasets automatically.

Supervised learning is one of the most common paradigms. In supervised learning,
models are trained on labelled examples — pairs of input features and their
corresponding target outputs. The model learns a mapping function that can
generalise to unseen inputs.

Unsupervised learning, by contrast, works with unlabelled data. Clustering
algorithms such as k-means group similar data points together without any prior
knowledge of the correct categories.

Reinforcement learning involves an agent that interacts with an environment,
receiving rewards or penalties for its actions. Over time, the agent learns a
policy that maximises cumulative reward, a process that has led to breakthroughs
in game-playing AI systems.

Deep learning uses multi-layered neural networks to learn hierarchical
representations of data. Convolutional neural networks excel at image
recognition tasks, while recurrent neural networks and transformers are widely
used for sequential data such as text and speech.

The quality of a machine learning model depends heavily on the quantity and
quality of the training data. Data preprocessing steps such as normalisation,
feature engineering, and handling of missing values are critical to good
performance.
""".strip()


# ---------------------------------------------------------------------------
# summarizer.py tests
# ---------------------------------------------------------------------------

class TestExtractiveSummary:
    @pytest.fixture(autouse=True)
    def require_sumy(self):
        pytest.importorskip("sumy")

    def test_returns_list(self):
        from app.services.summarizer import extractive_summary
        result = extractive_summary(LONG_TEXT, sentence_count=3)
        assert isinstance(result, list)

    def test_respects_sentence_count(self):
        from app.services.summarizer import extractive_summary
        result = extractive_summary(LONG_TEXT, sentence_count=3)
        # May return up to 3 (could be less if short sentences filtered)
        assert len(result) <= 3

    def test_returns_more_for_larger_count(self):
        from app.services.summarizer import extractive_summary
        short = extractive_summary(LONG_TEXT, sentence_count=3)
        long  = extractive_summary(LONG_TEXT, sentence_count=7)
        assert len(long) >= len(short)

    def test_empty_text_returns_empty_list(self):
        from app.services.summarizer import extractive_summary
        assert extractive_summary("") == []
        assert extractive_summary("   ") == []

    def test_short_document_does_not_raise(self):
        from app.services.summarizer import extractive_summary
        # Only 2 sentences — asking for 7 should not crash
        result = extractive_summary(
            "Machine learning is powerful. It learns from data.",
            sentence_count=7,
        )
        assert isinstance(result, list)
        assert len(result) <= 2

    def test_sentences_are_strings(self):
        from app.services.summarizer import extractive_summary
        result = extractive_summary(LONG_TEXT, sentence_count=5)
        assert all(isinstance(s, str) for s in result)

    def test_sentences_have_minimum_words(self):
        from app.services.summarizer import extractive_summary
        result = extractive_summary(LONG_TEXT, sentence_count=7)
        for s in result:
            assert len(s.split()) >= 5, f"Sentence too short: {s!r}"


# ---------------------------------------------------------------------------
# pdf_export.py tests
# ---------------------------------------------------------------------------

class TestGenerateSummaryPDF:
    @pytest.fixture(autouse=True)
    def require_reportlab(self):
        pytest.importorskip("reportlab")

    def _make_payload(self, sentences=None):
        """Build a minimal PDFExportRequest-like object."""
        from types import SimpleNamespace
        entities = SimpleNamespace(
            persons=["Alice Smith"],
            organizations=["Acme Corp"],
            dates=["January 2026"],
            locations=["New York"],
            money=["$50,000"],
        )
        return SimpleNamespace(
            filename="test_resume.pdf",
            document_type="resume",
            summary="• Alice Smith is a senior engineer.\n• She joined Acme Corp in January 2026.",
            key_sentences=sentences or [
                "Alice Smith is a senior engineer.",
                "She joined Acme Corp in January 2026.",
            ],
            entities=entities,
        )

    def test_returns_bytes(self):
        from app.utils.pdf_export import generate_summary_pdf
        pdf = generate_summary_pdf(self._make_payload())
        assert isinstance(pdf, bytes)

    def test_is_valid_pdf(self):
        from app.utils.pdf_export import generate_summary_pdf
        pdf = generate_summary_pdf(self._make_payload())
        # All PDFs start with the %PDF magic bytes
        assert pdf[:4] == b"%PDF"

    def test_non_empty_output(self):
        from app.utils.pdf_export import generate_summary_pdf
        pdf = generate_summary_pdf(self._make_payload())
        assert len(pdf) > 1024, "PDF should be at least 1 KB"

    def test_handles_empty_entities(self):
        from types import SimpleNamespace
        from app.utils.pdf_export import generate_summary_pdf
        payload = SimpleNamespace(
            filename="blank.pdf",
            document_type="general document",
            summary="• No specific entities found.",
            key_sentences=["No specific entities found."],
            entities=SimpleNamespace(
                persons=[], organizations=[], dates=[],
                locations=[], money=[],
            ),
        )
        pdf = generate_summary_pdf(payload)
        assert pdf[:4] == b"%PDF"

    def test_handles_xml_special_chars(self):
        from types import SimpleNamespace
        from app.utils.pdf_export import generate_summary_pdf
        payload = SimpleNamespace(
            filename="special.pdf",
            document_type="contract",
            summary="• Revenue > $500k & profit < 10%.",
            key_sentences=["Revenue > $500k & profit < 10%."],
            entities=SimpleNamespace(
                persons=[], organizations=[], dates=[], locations=[], money=["$500k"],
            ),
        )
        # Should not raise despite & < > in text
        pdf = generate_summary_pdf(payload)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# End-to-end pipeline smoke test
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:
    """
    Runs the full pipeline (extract → classify → NER → summarise) on a
    synthetic in-memory PDF. Requires all backend dependencies to be installed.
    """

    @pytest.fixture(autouse=True)
    def require_deps(self):
        pytest.importorskip("PyPDF2")
        pytest.importorskip("sumy")
        pytest.importorskip("spacy")
        import spacy
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            pytest.skip("spaCy model 'en_core_web_sm' not installed.")

    def _make_pdf(self, text: str) -> bytes:
        import io
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        # Write text in chunks (canvas has a line-length limit)
        y = 750
        for line in text.splitlines():
            c.drawString(50, y, line[:90])
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        return buf.getvalue()

    def test_full_pipeline_on_resume(self):
        from app.utils.file_handler import detect_file_type
        from app.services.text_extraction import extract_text
        from app.services.classification import classify_document
        from app.services.ner import extract_entities
        from app.services.summarizer import extractive_summary

        resume_text = (
            "Jane Doe — Senior Data Scientist\n"
            "Experience: 6 years at Google working on recommendation systems.\n"
            "Education: M.S. in Computer Science from Stanford University, 2020.\n"
            "Skills: Python, TensorFlow, PyTorch, SQL, and distributed computing.\n"
            "She led a team of five engineers to deliver a 20% improvement in CTR.\n"
            "Certifications: Google Professional Data Engineer, AWS Solutions Architect.\n"
            "She is based in San Francisco and open to remote opportunities.\n"
            "References available upon request."
        )

        pdf_bytes = self._make_pdf(resume_text)

        # Step 1 — detect file type
        file_type = detect_file_type(pdf_bytes)
        assert file_type == "pdf"

        # Step 2 — extract text
        extraction = extract_text(pdf_bytes, file_type)
        assert extraction["source"] == "pdf"
        assert len(extraction["text"]) > 0

        # Step 3 — classify
        label, confidence = classify_document(extraction["text"])
        assert label == "resume"
        assert confidence > 0.0

        # Step 4 — NER
        entities = extract_entities(extraction["text"])
        assert isinstance(entities, dict)
        assert set(entities.keys()) == {"persons", "organizations", "dates", "locations", "money"}

        # Step 5 — summarise
        sentences = extractive_summary(extraction["text"], sentence_count=3)
        assert isinstance(sentences, list)
        # Should find at least 1 sentence from a non-trivial text
        assert len(sentences) >= 1
