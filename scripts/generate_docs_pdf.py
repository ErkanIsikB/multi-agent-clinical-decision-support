"""Render the capstone markdown deliverables to styled PDFs.

Converts the data dictionary, prompt-engineering portfolio, and evaluation
report markdown files into PDFs that reuse the ClinicalBridge report styling
(Arial family, navy/blue/teal palette) and, unlike the project-report
generator, render Markdown tables and fenced code blocks.
"""

from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf"

NAVY = colors.HexColor("#173F5F")
BLUE = colors.HexColor("#20639B")
TEAL = colors.HexColor("#2A9D8F")
PALE = colors.HexColor("#EAF4F7")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#5D6B78")
GRID = colors.HexColor("#AAB8C2")

DOCS = [
    (
        "data_dictionary.md",
        "clinicalbridge_data_dictionary.pdf",
        "Simulated Dataset and Data Dictionary",
    ),
    (
        "prompt_engineering_portfolio.md",
        "clinicalbridge_prompt_engineering_portfolio.pdf",
        "Prompt Engineering Portfolio",
    ),
    (
        "evaluation_report.md",
        "clinicalbridge_evaluation_report.pdf",
        "Evaluation Report",
    ),
]


def register_fonts() -> None:
    base = "/System/Library/Fonts/Supplemental"
    pdfmetrics.registerFont(TTFont("Arial", f"{base}/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", f"{base}/Arial Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Italic", f"{base}/Arial Italic.ttf"))
    pdfmetrics.registerFontFamily(
        "Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic"
    )


def clean_text(text: str) -> str:
    return (
        text.replace("—", " - ")
        .replace("–", "-")
        .replace("‑", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("≥", ">=")
        .replace("≤", "<=")
    )


def inline_markdown(text: str) -> str:
    escaped = html.escape(clean_text(text))
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font name='Arial-Bold'>\1</font>", escaped)
    return escaped


def build_styles() -> dict:
    sample = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title", parent=sample["Title"], fontName="Arial-Bold", fontSize=26,
            leading=30, textColor=NAVY, alignment=TA_LEFT, spaceAfter=10,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle", parent=sample["Normal"], fontName="Arial", fontSize=13,
            leading=18, textColor=BLUE, alignment=TA_LEFT,
        ),
        "Heading1": ParagraphStyle(
            "Heading1", parent=sample["Heading1"], fontName="Arial-Bold", fontSize=15,
            leading=19, textColor=NAVY, spaceBefore=10, spaceAfter=4, keepWithNext=True,
        ),
        "Heading2": ParagraphStyle(
            "Heading2", parent=sample["Heading2"], fontName="Arial-Bold", fontSize=11.5,
            leading=15, textColor=BLUE, spaceBefore=7, spaceAfter=3, keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body", parent=sample["BodyText"], fontName="Arial", fontSize=9.6,
            leading=13.6, textColor=INK, alignment=TA_LEFT, spaceAfter=3,
        ),
        "Bullet": ParagraphStyle(
            "Bullet", parent=sample["BodyText"], fontName="Arial", fontSize=9.5,
            leading=13.2, textColor=INK, leftIndent=15, firstLineIndent=-9,
            bulletIndent=4, spaceAfter=2,
        ),
        "OrderedBullet": ParagraphStyle(
            "OrderedBullet", parent=sample["BodyText"], fontName="Arial", fontSize=9.5,
            leading=13.2, textColor=INK, leftIndent=17, firstLineIndent=-11,
            bulletIndent=4, spaceAfter=2,
        ),
        "Cell": ParagraphStyle(
            "Cell", parent=sample["BodyText"], fontName="Arial", fontSize=8.4,
            leading=10.6, textColor=INK,
        ),
        "CellRight": ParagraphStyle(
            "CellRight", parent=sample["BodyText"], fontName="Arial", fontSize=8.4,
            leading=10.6, textColor=INK, alignment=2,
        ),
        "CellHead": ParagraphStyle(
            "CellHead", parent=sample["BodyText"], fontName="Arial-Bold", fontSize=8.4,
            leading=10.6, textColor=colors.white,
        ),
        "Small": ParagraphStyle(
            "Small", parent=sample["BodyText"], fontName="Arial", fontSize=8.5,
            leading=11, textColor=MUTED, alignment=TA_CENTER,
        ),
        "Code": ParagraphStyle(
            "Code", parent=sample["BodyText"], fontName="Courier", fontSize=8.2,
            leading=10.6, textColor=INK, backColor=PALE, leftIndent=6, spaceAfter=3,
        ),
    }


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(line: str) -> bool:
    return bool(re.match(r"^\|?[\s:|-]+\|?$", line)) and "-" in line


def _numeric_cell(val: str) -> bool:
    core = re.sub(r"[*%s()<>=\s-]", "", val)
    core = core.replace(".", "").replace(",", "")
    return bool(core) and core.isdigit()


def make_table(header: list[str], rows: list[list[str]], styles: dict, width: float):
    rows = [(row + [""] * len(header))[: len(header)] for row in rows]

    # A column is right-aligned if every non-empty body cell looks numeric.
    right_cols = set()
    for c in range(len(header)):
        vals = [rows[r][c] for r in range(len(rows)) if rows[r][c].strip()]
        if vals and all(_numeric_cell(v) for v in vals):
            right_cols.add(c)

    def cell(text: str, head: bool, col: int):
        if head:
            style = styles["CellHead"]
        else:
            style = styles["CellRight"] if col in right_cols else styles["Cell"]
        return Paragraph(inline_markdown(text), style)

    data = [[cell(h, True, i) for i, h in enumerate(header)]]
    for row in rows:
        data.append([cell(val, False, i) for i, val in enumerate(row)])

    ncols = len(header)
    first = width * (0.30 if ncols <= 3 else 0.24)
    rest = (width - first) / (ncols - 1) if ncols > 1 else width
    col_widths = [first] + [rest] * (ncols - 1)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    table.setStyle(TableStyle(style))
    return table


def parse_markdown(path: Path, styles: dict, width: float) -> list:
    lines = clean_text(path.read_text(encoding="utf-8")).splitlines()
    story: list = []
    paragraph: list[str] = []
    i = 0

    def flush() -> None:
        if paragraph:
            story.append(Paragraph(inline_markdown(" ".join(paragraph)), styles["Body"]))
            paragraph.clear()

    in_code = False
    code_lines: list[str] = []
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        if stripped.startswith("```"):
            if in_code:
                flush()
                for cl in code_lines:
                    story.append(Paragraph(html.escape(cl) or "&nbsp;", styles["Code"]))
                code_lines = []
                in_code = False
            else:
                flush()
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(raw)
            i += 1
            continue

        # Markdown table block
        if stripped.startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            flush()
            header = split_row(stripped)
            j = i + 2
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(split_row(lines[j].strip()))
                j += 1
            table = make_table(header, rows, styles, width)
            story.append(Spacer(1, 0.04 * inch))
            story.append(table)
            story.append(Spacer(1, 0.09 * inch))
            i = j
            continue

        if not stripped:
            flush()
            i += 1
            continue
        if stripped.startswith("# "):
            flush()
            story.append(Paragraph(inline_markdown(stripped[2:]), styles["Heading1"]))
            i += 1
            continue
        if stripped.startswith("## "):
            flush()
            story.append(Spacer(1, 0.05 * inch))
            story.append(Paragraph(inline_markdown(stripped[3:]), styles["Heading1"]))
            i += 1
            continue
        if stripped.startswith("### "):
            flush()
            story.append(Paragraph(inline_markdown(stripped[4:]), styles["Heading2"]))
            i += 1
            continue
        if stripped.startswith("- "):
            flush()
            story.append(
                Paragraph(f"<bullet>&bull;</bullet>{inline_markdown(stripped[2:])}", styles["Bullet"])
            )
            i += 1
            continue
        ordered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if ordered:
            flush()
            story.append(
                Paragraph(
                    f"<bullet>{ordered.group(1)}.</bullet>{inline_markdown(ordered.group(2))}",
                    styles["OrderedBullet"],
                )
            )
            i += 1
            continue
        paragraph.append(stripped)
        i += 1
    flush()
    return story


def page_header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 10.55 * inch, letter[0] - doc.rightMargin, 10.55 * inch)
    canvas.setFont("Arial-Italic", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10.62 * inch, "ClinicalBridge")
    canvas.drawRightString(
        letter[0] - doc.rightMargin, 10.62 * inch, "COP-3442 Prompt Engineering"
    )
    canvas.setFont("Arial", 8)
    canvas.drawString(doc.leftMargin, 0.45 * inch, "Educational prototype - simulated data only")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def cover(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 10.3 * inch, letter[0], 0.7 * inch, stroke=0, fill=1)
    canvas.setFillColor(TEAL)
    canvas.circle(0.8 * inch, 10.65 * inch, 0.13 * inch, stroke=0, fill=1)
    page_header_footer(canvas, doc)
    canvas.restoreState()


def build_one(md_name: str, pdf_name: str, subtitle: str, styles: dict) -> Path:
    out = OUT_DIR / pdf_name
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out), pagesize=letter,
        rightMargin=0.78 * inch, leftMargin=0.78 * inch,
        topMargin=0.95 * inch, bottomMargin=0.7 * inch,
        title=f"ClinicalBridge - {subtitle}",
        author="Erkan Isik Bacak, Raymond Lasses, Ata Uzun, Kutlay Basar Aklan",
    )
    width = letter[0] - 1.56 * inch
    story = [
        Spacer(1, 0.1 * inch),
        Paragraph("ClinicalBridge", styles["Title"]),
        Paragraph(subtitle, styles["Subtitle"]),
        Spacer(1, 0.05 * inch),
        Paragraph(f"COP-3442 Prompt Engineering - generated {date.today().isoformat()}", styles["Small"]),
        Spacer(1, 0.12 * inch),
    ]
    story.extend(parse_markdown(ROOT / md_name, styles, width))
    doc.build(story, onFirstPage=cover, onLaterPages=page_header_footer)
    return out


def main() -> None:
    register_fonts()
    styles = build_styles()
    for md_name, pdf_name, subtitle in DOCS:
        path = build_one(md_name, pdf_name, subtitle, styles)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
