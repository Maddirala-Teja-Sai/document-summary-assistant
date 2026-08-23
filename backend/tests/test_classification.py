"""
Tests for classification.py and ner.py (Component 3).

Run with:
    cd backend
    pytest tests/test_classification.py -v
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# classification.py tests
# ---------------------------------------------------------------------------

class TestClassifyDocument:
    def test_classifies_resume(self):
        from app.services.classification import classify_document
        text = (
            "John Doe — Senior Software Engineer\n"
            "Experience: 7 years in Python, AWS, React.\n"
            "Education: B.S. Computer Science, MIT.\n"
            "Skills: FastAPI, Docker, PostgreSQL.\n"
            "Certifications: AWS Solutions Architect.\n"
            "References available on request."
        )
        label, confidence = classify_document(text)
        assert label == "resume"
        assert confidence > 0.0

    def test_classifies_contract(self):
        from app.services.classification import classify_document
        text = (
            "SERVICE AGREEMENT\n"
            "This agreement is entered into by the party of the first part (hereinafter 'Client')\n"
            "and the party of the second part (hereinafter 'Provider').\n"
            "Clause 1: Obligations of the Provider include...\n"
            "Termination: Either party may terminate with 30 days notice.\n"
            "Governing law: This agreement is subject to the laws of California.\n"
            "Indemnification: The Client shall indemnify the Provider.\n"
            "Jurisdiction: Disputes shall be resolved in San Francisco courts."
        )
        label, confidence = classify_document(text)
        assert label == "contract"
        assert confidence > 0.0

    def test_classifies_invoice(self):
        from app.services.classification import classify_document
        text = (
            "INVOICE #10045\n"
            "Bill To: Acme Corp\n"
            "Due Date: 2026-09-01\n"
            "Qty: 5 x Widget A — Unit Price: $20.00\n"
            "Subtotal: $100.00  Tax: $10.00  Total: $110.00\n"
            "Payment Terms: Net 30\n"
            "Vendor: TechSupplies Ltd."
        )
        label, confidence = classify_document(text)
        assert label == "invoice"
        assert confidence > 0.0

    def test_classifies_research_paper(self):
        from app.services.classification import classify_document
        text = (
            "Abstract: This paper investigates the effect of temperature on reaction rates.\n"
            "Keywords: thermodynamics, experiment, data analysis\n"
            "Methodology: We conducted controlled experiments using...\n"
            "Findings: Our results show a significant correlation.\n"
            "Conclusion: Further research is warranted.\n"
            "References: [1] Smith et al., Journal of Chemistry, 2024. DOI: 10.1000/xyz123"
        )
        label, confidence = classify_document(text)
        assert label == "research paper"
        assert confidence > 0.0

    def test_returns_general_on_empty_text(self):
        from app.services.classification import classify_document
        label, confidence = classify_document("")
        assert label == "general document"
        assert confidence == 0.0

    def test_returns_general_on_unrecognised_text(self):
        from app.services.classification import classify_document
        label, confidence = classify_document("xyzzy plugh blorb frob qux")
        assert label == "general document"
        assert confidence == 0.0

    def test_confidence_between_0_and_1(self):
        from app.services.classification import classify_document
        text = "experience education skills summary references certifications"
        _, confidence = classify_document(text)
        assert 0.0 <= confidence <= 1.0

    def test_case_insensitive(self):
        from app.services.classification import classify_document
        lower_label, _ = classify_document("experience education skills")
        upper_label, _ = classify_document("EXPERIENCE EDUCATION SKILLS")
        assert lower_label == upper_label


class TestGetSummaryFocus:
    def test_known_types_return_strings(self):
        from app.services.classification import get_summary_focus
        for doc_type in ["resume", "contract", "invoice", "research paper",
                         "report", "letter", "cover letter", "article", "manual"]:
            focus = get_summary_focus(doc_type)
            assert isinstance(focus, str)
            assert len(focus) > 0

    def test_unknown_type_returns_default(self):
        from app.services.classification import get_summary_focus
        focus = get_summary_focus("something totally unknown")
        assert focus == "Main ideas & key points"


# ---------------------------------------------------------------------------
# ner.py tests
# ---------------------------------------------------------------------------

class TestExtractEntities:
    """
    These tests require spaCy en_core_web_sm to be installed.
    Skip gracefully if the model is not available.
    """

    @pytest.fixture(autouse=True)
    def require_spacy(self):
        pytest.importorskip("spacy")
        import spacy
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            pytest.skip("spaCy model 'en_core_web_sm' not installed.")

    def test_returns_expected_keys(self):
        from app.services.ner import extract_entities
        result = extract_entities("Hello world.")
        assert set(result.keys()) == {"persons", "organizations", "dates", "locations", "money"}

    def test_extracts_person(self):
        from app.services.ner import extract_entities
        result = extract_entities("Albert Einstein was born in Germany.")
        assert any("Einstein" in p or "Albert Einstein" in p for p in result["persons"])

    def test_extracts_organization(self):
        from app.services.ner import extract_entities
        result = extract_entities("She joined Google in 2022 and worked with Microsoft.")
        orgs = [o.lower() for o in result["organizations"]]
        assert "google" in orgs or "microsoft" in orgs

    def test_extracts_location(self):
        from app.services.ner import extract_entities
        result = extract_entities("The conference was held in Paris, France.")
        locations = [l.lower() for l in result["locations"]]
        assert "paris" in locations or "france" in locations

    def test_extracts_date(self):
        from app.services.ner import extract_entities
        result = extract_entities("The deadline is January 15, 2026.")
        assert len(result["dates"]) > 0

    def test_empty_text_returns_empty_lists(self):
        from app.services.ner import extract_entities
        result = extract_entities("")
        assert all(v == [] for v in result.values())

    def test_all_values_are_sorted_lists(self):
        from app.services.ner import extract_entities
        result = extract_entities(
            "Apple and Google are based in California. Tim Cook leads Apple."
        )
        for key, value in result.items():
            assert isinstance(value, list), f"{key} should be a list"
            assert value == sorted(value), f"{key} should be sorted"

    def test_deduplicates_entities(self):
        from app.services.ner import extract_entities
        # Repeat the same entity multiple times — should appear only once
        result = extract_entities("Google acquired the startup. Google is a big company. Google announced earnings.")
        google_count = result["organizations"].count("Google")
        assert google_count == 1
