import base64
import binascii
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FONT_NAME = "STSong-Light"


def build_resume_pdf(resume):
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=safe_text(resume.get("name")) or "resume",
    )

    styles = create_styles()
    story = []

    header_left = [
        Paragraph(safe_text(resume.get("name")) or "姓名", styles["Name"]),
        Paragraph(safe_text(resume.get("title")) or "求职方向", styles["Title"]),
        Paragraph(build_contact_line(resume), styles["Contact"]),
    ]
    avatar = build_avatar(resume.get("avatar"))
    header_table = Table([[header_left, avatar]], colWidths=[128 * mm, 34 * mm])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 1.6, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    sections = [
        ("个人优势", resume.get("summary")),
        ("核心技能", resume.get("skills")),
        ("工作 / 实习经历", format_entries(resume.get("experience"), "organization")),
        ("项目经历", format_entries(resume.get("projects"), "name")),
        ("教育经历", resume.get("education")),
        ("自我评价", resume.get("selfEvaluation")),
    ]
    for title, content in sections:
        story.append(build_section(title, content, styles))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def create_styles():
    styles = getSampleStyleSheet()
    return {
        "Name": ParagraphStyle(
            "ResumeName",
            parent=styles["Normal"],
            fontName=FONT_NAME,
            fontSize=24,
            leading=30,
            textColor=colors.black,
            spaceAfter=3,
        ),
        "Title": ParagraphStyle(
            "ResumeTitle",
            parent=styles["Normal"],
            fontName=FONT_NAME,
            fontSize=12,
            leading=18,
            textColor=colors.HexColor("#333333"),
            spaceAfter=4,
        ),
        "Contact": ParagraphStyle(
            "ResumeContact",
            parent=styles["Normal"],
            fontName=FONT_NAME,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#555555"),
        ),
        "SectionTitle": ParagraphStyle(
            "ResumeSectionTitle",
            parent=styles["Normal"],
            fontName=FONT_NAME,
            fontSize=12,
            leading=16,
            textColor=colors.black,
            spaceAfter=5,
        ),
        "Body": ParagraphStyle(
            "ResumeBody",
            parent=styles["Normal"],
            fontName=FONT_NAME,
            fontSize=10,
            leading=17,
            textColor=colors.HexColor("#222222"),
            wordWrap="CJK",
        ),
    }


def build_section(title, content, styles):
    title_table = Table(
        [[Paragraph(escape(title), styles["SectionTitle"])]],
        colWidths=[162 * mm],
    )
    title_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.7, colors.HexColor("#D0D0D0")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    body = Paragraph(to_paragraph_text(content), styles["Body"])
    return KeepTogether([title_table, Spacer(1, 2 * mm), body, Spacer(1, 6 * mm)])


def build_contact_line(resume):
    values = [
        safe_text(resume.get("phone")),
        safe_text(resume.get("email")),
        safe_text(resume.get("location")),
    ]
    return "  |  ".join(value for value in values if value) or "电话 | 邮箱 | 城市"


def build_avatar(data_url):
    image_bytes = decode_data_url(data_url)
    if image_bytes:
        image = Image(BytesIO(image_bytes), width=26 * mm, height=32 * mm)
        image.hAlign = "RIGHT"
        return image

    placeholder = Table([["照片"]], colWidths=[26 * mm], rowHeights=[32 * mm])
    placeholder.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#777777")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return placeholder


def decode_data_url(data_url):
    if not isinstance(data_url, str) or "," not in data_url:
        return b""
    header, encoded = data_url.split(",", 1)
    if "base64" not in header:
        return b""
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        return b""


def to_paragraph_text(value):
    text = safe_text(value) or "暂无"
    return "<br/>".join(escape(line) for line in text.splitlines())


def format_entries(entries, title_key):
    if isinstance(entries, str):
        return entries
    if not isinstance(entries, list):
        return ""

    blocks = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        title = safe_text(entry.get(title_key)) or ("项目名称" if title_key == "name" else "公司 / 组织")
        time = safe_text(entry.get("time"))
        role = safe_text(entry.get("role"))
        description = safe_text(entry.get("description"))

        first_line = title
        if time:
            first_line = f"{first_line} | {time}"
        lines = [first_line]
        if role:
            lines.append(role)
        if description:
            lines.append(description)
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def safe_text(value):
    return str(value or "").strip()
