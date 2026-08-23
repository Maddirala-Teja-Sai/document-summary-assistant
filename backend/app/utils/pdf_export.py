"""
PDF export utility.

Generates a formatted PDF from a SummaryResponse payload using ReportLab.
The PDF is returned as raw bytes and streamed back to the client as a
download via the ``/api/export-pdf`` route.
"""

from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_BRAND_BLUE   = colors.HexColor("#3B82F6")   # Tailwind blue-500
_BRAND_DARK   = colors.HexColor("#1E293B")   # Tailwind slate-800
_BRAND_MUTED  = colors.HexColor("#64748B")   # Tailwind slate-500
_BRAND_LIGHT  = colors.HexColor("#F1F5F9")   # Tailwind slate-100
_WHITE        = colors.white


def _build_styles() -> dict:
    """Build and return a dict of named ParagraphStyles."""
    base = getSampleStyleSheet()

    return {
        "header": ParagraphStyle(
            "header",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=_BRAND_BLUE,
            spaceAfter=4,
        ),
        "meta_label": ParagraphStyle(
            "meta_label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=_BRAND_MUTED,
        ),
        "meta_value": ParagraphStyle(
            "meta_value",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=_BRAND_DARK,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=_BRAND_DARK,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=_BRAND_DARK,
            leftIndent=16,
            spaceAfter=6,
            leading=14,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=_BRAND_MUTED,
            alignment=1,   # centred
        ),
    }


def generate_summary_pdf(payload) -> bytes:
    """
    Generate a summary PDF from the given payload.

    Args:
        payload: A :class:`app.api.schemas.PDFExportRequest` instance.

    Returns:
        Raw PDF bytes suitable for streaming as a download response.
    """
    buf = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Summary — {payload.filename}",
        author="Document Summary Assistant",
    )

    story = []

    # ------------------------------------------------------------------ #
    # Header
    # ------------------------------------------------------------------ #
    story.append(Paragraph("Document Summary Assistant", styles["header"]))
    story.append(HRFlowable(width="100%", thickness=2, color=_BRAND_BLUE, spaceAfter=8))

    # ------------------------------------------------------------------ #
    # Metadata table
    # ------------------------------------------------------------------ #
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc_type_display = payload.document_type.title()

    meta_data = [
        [
            Paragraph("File:", styles["meta_label"]),
            Paragraph(payload.filename, styles["meta_value"]),
            Paragraph("Generated:", styles["meta_label"]),
            Paragraph(generated_at, styles["meta_value"]),
        ],
        [
            Paragraph("Document type:", styles["meta_label"]),
            Paragraph(doc_type_display, styles["meta_value"]),
            Paragraph("", styles["meta_label"]),
            Paragraph("", styles["meta_value"]),
        ],
    ]

    meta_table = Table(
        meta_data,
        colWidths=["18%", "32%", "18%", "32%"],
    )
    meta_table.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND",  (0, 0), (-1, -1), _BRAND_LIGHT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_BRAND_LIGHT, _WHITE]),
        ("BOX",         (0, 0), (-1, -1), 0.5, _BRAND_MUTED),
        ("INNERGRID",   (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
    ]))

    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------------------ #
    # Summary section
    # ------------------------------------------------------------------ #
    story.append(Paragraph("SUMMARY", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BRAND_MUTED, spaceAfter=6))

    if payload.key_sentences:
        for sentence in payload.key_sentences:
            safe = (
                sentence
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            story.append(Paragraph(f"• &nbsp; {safe}", styles["bullet"]))
    else:
        for line in payload.summary.splitlines():
            line = line.strip()
            if line:
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, styles["bullet"]))

    # ------------------------------------------------------------------ #
    # Improvement Suggestions section (if present)
    # ------------------------------------------------------------------ #
    if getattr(payload, "suggestions", None):
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("IMPROVEMENT SUGGESTIONS", styles["section_title"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=_BRAND_MUTED, spaceAfter=6))
        for suggestion in payload.suggestions:
            safe = (
                suggestion
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            story.append(Paragraph(f"• &nbsp; {safe}", styles["bullet"]))

    story.append(Spacer(1, 0.8 * cm))

    # ------------------------------------------------------------------ #
    # Footer
    # ------------------------------------------------------------------ #
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BRAND_MUTED, spaceAfter=4))
    story.append(Paragraph(
        "Generated by Document Summary Assistant",
        styles["footer"],
    ))

    # ------------------------------------------------------------------ #
    # Build
    # ------------------------------------------------------------------ #
    doc.build(story)
    buf.seek(0)
    return buf.read()
