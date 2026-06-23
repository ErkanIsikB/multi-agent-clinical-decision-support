from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "clinicalbridge_project_report.pdf"

NAVY = colors.HexColor("#173F5F")
BLUE = colors.HexColor("#20639B")
TEAL = colors.HexColor("#2A9D8F")
PALE = colors.HexColor("#EAF4F7")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#5D6B78")


def register_fonts() -> None:
    base = "/System/Library/Fonts/Supplemental"
    pdfmetrics.registerFont(TTFont("Arial", f"{base}/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", f"{base}/Arial Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Italic", f"{base}/Arial Italic.ttf"))
    pdfmetrics.registerFontFamily(
        "Arial",
        normal="Arial",
        bold="Arial-Bold",
        italic="Arial-Italic",
    )


class ArchitectureDiagram(Flowable):
    def __init__(self, width: float = 6.6 * inch, height: float = 2.35 * inch):
        super().__init__()
        self.width = width
        self.height = height

    def draw_box(self, canvas, x, y, width, height, label, fill=PALE):
        canvas.setFillColor(fill)
        canvas.setStrokeColor(BLUE)
        canvas.roundRect(x, y, width, height, 5, stroke=1, fill=1)
        canvas.setFillColor(INK)
        canvas.setFont("Arial-Bold", 7.5)
        lines = label.split("\n")
        for index, line in enumerate(lines):
            canvas.drawCentredString(x + width / 2, y + height / 2 + 3 - index * 9, line)

    def arrow(self, canvas, x1, y1, x2, y2):
        canvas.setStrokeColor(MUTED)
        canvas.setFillColor(MUTED)
        canvas.line(x1, y1, x2, y2)
        angle = 4
        if x2 >= x1:
            canvas.line(x2, y2, x2 - angle, y2 + angle / 2)
            canvas.line(x2, y2, x2 - angle, y2 - angle / 2)
        else:
            canvas.line(x2, y2, x2 + angle, y2 + angle / 2)
            canvas.line(x2, y2, x2 + angle, y2 - angle / 2)

    def draw(self):
        c = self.canv
        bw, bh = 0.92 * inch, 0.48 * inch
        y_mid = 1.08 * inch
        self.draw_box(c, 0.0, y_mid, bw, bh, "RPM\nAlert")
        self.draw_box(c, 1.15 * inch, y_mid, bw, bh, "Triage\nAgent")
        self.draw_box(c, 2.35 * inch, 1.55 * inch, bw, bh, "EHR\nAgent")
        self.draw_box(c, 2.35 * inch, 0.62 * inch, bw, bh, "Anamnesis\nAgent")
        self.draw_box(c, 3.62 * inch, y_mid, bw, bh, "Synthesis\nAgent")
        self.draw_box(c, 4.82 * inch, y_mid, bw, bh, "Quality\nGate")
        self.draw_box(c, 5.95 * inch, y_mid, 0.68 * inch, bh, "Context\nBrief", TEAL)
        self.draw_box(
            c, 2.35 * inch, 0.0, bw, bh, "Immediate\nEscalation", colors.HexColor("#FDECEC")
        )

        self.arrow(c, bw, y_mid + bh / 2, 1.15 * inch, y_mid + bh / 2)
        self.arrow(c, 2.07 * inch, y_mid + bh / 2, 2.35 * inch, 1.55 * inch + bh / 2)
        self.arrow(c, 2.07 * inch, y_mid + bh / 2, 2.35 * inch, 0.62 * inch + bh / 2)
        self.arrow(c, 3.27 * inch, 1.55 * inch + bh / 2, 3.62 * inch, y_mid + bh / 2)
        self.arrow(c, 3.27 * inch, 0.62 * inch + bh / 2, 3.62 * inch, y_mid + bh / 2)
        self.arrow(c, 4.54 * inch, y_mid + bh / 2, 4.82 * inch, y_mid + bh / 2)
        self.arrow(c, 5.74 * inch, y_mid + bh / 2, 5.95 * inch, y_mid + bh / 2)
        self.arrow(c, 1.61 * inch, y_mid, 2.35 * inch, bh / 2)
        self.arrow(c, 3.27 * inch, bh / 2, 4.82 * inch, y_mid)

        c.setFont("Arial-Italic", 6.8)
        c.setFillColor(MUTED)
        c.drawString(2.37 * inch, 2.15 * inch, "Parallel context retrieval")
        c.drawString(1.82 * inch, 0.17 * inch, "Critical")


def clean_text(text: str) -> str:
    return (
        text.replace("\u2014", " - ")
        .replace("\u2013", "-")
        .replace("\u2011", "-")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


def inline_markdown(text: str) -> str:
    placeholders: list[tuple[str, str]] = []

    def link_replacement(match: re.Match) -> str:
        placeholder = f"@@LINK{len(placeholders)}@@"
        label = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        placeholders.append((placeholder, f"<link href='{url}' color='#20639B'>{label}</link>"))
        return placeholder

    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link_replacement, text)
    escaped = html.escape(clean_text(text))
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<i>\1</i>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font name='Arial-Bold'>\1</font>", escaped)
    for placeholder, markup in placeholders:
        escaped = escaped.replace(placeholder, markup)
    return escaped


def parse_markdown(path: Path, styles: dict, insert_diagram: bool = False) -> list:
    lines = clean_text(path.read_text(encoding="utf-8")).splitlines()
    if path.name == "project_report.md":
        start = next(index for index, line in enumerate(lines) if line.startswith("## Abstract"))
        lines = lines[start:]
        stop = next(
            (index for index, line in enumerate(lines) if line.strip() == "## References"),
            len(lines),
        )
        lines = lines[:stop]
    story = []
    paragraph: list[str] = []
    is_references = path.name == "references.md"
    heading1_style = styles["ReferenceHeading1"] if is_references else styles["Heading1"]
    heading2_style = styles["ReferenceHeading2"] if is_references else styles["Heading2"]
    body_style = styles["ReferenceBody"] if is_references else styles["Body"]
    bullet_style = styles["ReferenceBullet"] if is_references else styles["Bullet"]

    def flush() -> None:
        if paragraph:
            story.append(Paragraph(inline_markdown(" ".join(paragraph)), body_style))
            story.append(Spacer(1, 0.08 * inch))
            paragraph.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("## "):
            flush()
            title = stripped[3:]
            story.append(Spacer(1, 0.08 * inch))
            story.append(Paragraph(inline_markdown(title), heading1_style))
            story.append(Spacer(1, 0.06 * inch))
            if insert_diagram and title.startswith("4. System architecture"):
                story.append(ArchitectureDiagram())
                story.append(Spacer(1, 0.12 * inch))
            continue
        if stripped.startswith("# "):
            flush()
            if stripped[2:] != "References":
                story.append(Paragraph(inline_markdown(stripped[2:]), heading1_style))
            continue
        if stripped.startswith("### "):
            flush()
            story.append(Paragraph(inline_markdown(stripped[4:]), heading2_style))
            continue
        if stripped.startswith("- "):
            flush()
            story.append(
                Paragraph(
                    f"<bullet>&bull;</bullet>{inline_markdown(stripped[2:])}",
                    bullet_style,
                )
            )
            continue
        paragraph.append(stripped)
    flush()
    return story


def page_header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B7C5CF"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 10.1 * inch, letter[0] - doc.rightMargin, 10.1 * inch)
    canvas.setFont("Arial-Italic", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10.22 * inch, "ClinicalBridge Project Report")
    canvas.drawRightString(letter[0] - doc.rightMargin, 10.22 * inch, "COP-3442 Prompt Engineering")
    canvas.setFont("Arial", 8)
    canvas.drawString(doc.leftMargin, 0.48 * inch, "Bahçeşehir University")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.48 * inch, f"Page {doc.page}")
    canvas.restoreState()


def first_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 9.85 * inch, letter[0], 1.15 * inch, stroke=0, fill=1)
    canvas.setFillColor(TEAL)
    canvas.circle(0.85 * inch, 9.3 * inch, 0.17 * inch, stroke=0, fill=1)
    canvas.setFillColor(MUTED)
    canvas.setFont("Arial-Italic", 8)
    canvas.drawCentredString(
        letter[0] / 2, 0.48 * inch, "Educational prototype - simulated data only"
    )
    canvas.restoreState()


def build_styles() -> dict:
    sample = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=sample["Title"],
            fontName="Arial-Bold",
            fontSize=28,
            leading=32,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=sample["Normal"],
            fontName="Arial",
            fontSize=14,
            leading=19,
            textColor=BLUE,
            alignment=TA_LEFT,
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            parent=sample["Heading1"],
            fontName="Arial-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=sample["Heading2"],
            fontName="Arial-Bold",
            fontSize=12,
            leading=15,
            textColor=BLUE,
            spaceBefore=6,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="Arial",
            fontSize=9.6,
            leading=13.4,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=3,
            allowWidows=0,
            allowOrphans=0,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=sample["BodyText"],
            fontName="Arial",
            fontSize=9.4,
            leading=13,
            textColor=INK,
            leftIndent=15,
            firstLineIndent=-9,
            bulletIndent=4,
            spaceAfter=3,
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=sample["BodyText"],
            fontName="Arial",
            fontSize=8.5,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "TOC": ParagraphStyle(
            "TOC",
            parent=sample["BodyText"],
            fontName="Arial",
            fontSize=10,
            leading=15,
            textColor=INK,
        ),
        "ReferenceHeading1": ParagraphStyle(
            "ReferenceHeading1",
            parent=sample["Heading1"],
            fontName="Arial-Bold",
            fontSize=12.5,
            leading=15,
            textColor=NAVY,
            spaceBefore=5,
            spaceAfter=2,
            keepWithNext=True,
        ),
        "ReferenceHeading2": ParagraphStyle(
            "ReferenceHeading2",
            parent=sample["Heading2"],
            fontName="Arial-Bold",
            fontSize=10.5,
            leading=12,
            textColor=BLUE,
            spaceBefore=4,
            spaceAfter=2,
            keepWithNext=True,
        ),
        "ReferenceBody": ParagraphStyle(
            "ReferenceBody",
            parent=sample["BodyText"],
            fontName="Arial",
            fontSize=8.2,
            leading=10.3,
            textColor=INK,
        ),
        "ReferenceBullet": ParagraphStyle(
            "ReferenceBullet",
            parent=sample["BodyText"],
            fontName="Arial",
            fontSize=8.2,
            leading=10.3,
            textColor=INK,
            leftIndent=14,
            firstLineIndent=-8,
            bulletIndent=4,
            spaceAfter=2,
        ),
    }


def main() -> None:
    register_fonts()
    styles = build_styles()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.78 * inch,
        leftMargin=0.78 * inch,
        topMargin=0.92 * inch,
        bottomMargin=0.72 * inch,
        title="ClinicalBridge Project Report",
        author="Erkan Işık Bacak, Raymond Lasses, Ata Uzun, Kutlay Başar Aklan",
    )

    team_data = [
        ["Student", "Student number"],
        ["Erkan Işık Bacak", "2200914"],
        ["Raymond Lasses", "2200274"],
        ["Ata Uzun", "2103247"],
        ["Kutlay Başar Aklan", "2202139"],
    ]
    team_table = Table(team_data, colWidths=[3.65 * inch, 1.55 * inch])
    team_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Arial"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AAB8C2")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story = [
        Spacer(1, 1.05 * inch),
        Paragraph("ClinicalBridge", styles["Title"]),
        Paragraph(
            "Bridging the Clinical Context Gap with an LLM-Powered Multi-Agent System",
            styles["Subtitle"],
        ),
        Spacer(1, 0.28 * inch),
        Paragraph("COP-3442 Prompt Engineering - Spring 2026", styles["Heading2"]),
        Spacer(1, 0.18 * inch),
        team_table,
        Spacer(1, 0.28 * inch),
        Table(
            [
                [
                    Paragraph(
                        "<b>Safety notice.</b> This report describes an educational prototype "
                        "using entirely simulated data. ClinicalBridge is not a diagnostic tool "
                        "and must not be used for real clinical decisions.",
                        styles["Body"],
                    )
                ]
            ],
            colWidths=[5.75 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4E5")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E6A23C")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 0.3 * inch),
        Paragraph(f"Final report generated {date.today().isoformat()}", styles["Small"]),
        PageBreak(),
        Paragraph("Contents", styles["Heading1"]),
        Spacer(1, 0.08 * inch),
    ]
    contents = [
        "Abstract",
        "1. Problem and motivation",
        "2. Objective and scope",
        "3. Requirements interpretation",
        "4. System architecture",
        "5. OpenAI and LangChain implementation",
        "6. Retrieval-augmented generation",
        "7. Memory and tools",
        "8. Simulated dataset",
        "9. Prompt engineering",
        "10. Safety design",
        "11. Evaluation",
        "12. Interfaces and demonstration",
        "13. Limitations",
        "14. Reflection",
        "15. Conclusion",
        "References",
    ]
    for index, item in enumerate(contents):
        prefix = "" if index == 0 else f"{index}. " if item == "References" else ""
        story.append(Paragraph(f"{prefix}{inline_markdown(item)}", styles["TOC"]))
    story.append(PageBreak())
    story.extend(parse_markdown(ROOT / "docs" / "project_report.md", styles, True))
    story.append(PageBreak())
    story.append(Paragraph("References", styles["Heading1"]))
    story.extend(parse_markdown(ROOT / "docs" / "references.md", styles))

    document.build(story, onFirstPage=first_page, onLaterPages=page_header_footer)
    print(OUT)


if __name__ == "__main__":
    main()
