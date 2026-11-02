"""PPT 생성 스크립트들이 공유하는 도구 모음 (python-pptx)."""
import math
from io import BytesIO
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
FONT = "Malgun Gothic"

BG = RGBColor(0x0F, 0x16, 0x23)
PANEL = RGBColor(0x1A, 0x24, 0x36)
PANEL2 = RGBColor(0x22, 0x2F, 0x45)
ACCENT = RGBColor(0x4F, 0xC3, 0xF7)
TEXT = RGBColor(0xE8, 0xEE, 0xF7)
MUTED = RGBColor(0xB4, 0xC2, 0xD8)
WARN = RGBColor(0xFF, 0x8A, 0x65)
RED = RGBColor(0xFF, 0x5A, 0x5A)
GREEN = RGBColor(0x7C, 0xE3, 0xA1)
SLATE = RGBColor(0x4A, 0x5A, 0x75)
MID = RGBColor(0x3A, 0x7C, 0xA5)


def new_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, line=None, line_w=1.5):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_w)
    s.shadow.inherit = False
    return s


def text(slide, x, y, w, h, lines, size=18, color=TEXT, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.15):
    """lines: 문자열 또는 (문자열, {size,color,bold}) 목록"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    if isinstance(lines, str):
        lines = [lines]
    for i, ln in enumerate(lines):
        opt = {}
        if isinstance(ln, tuple):
            ln, opt = ln
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run()
        r.text = ln
        r.font.name = FONT
        r.font.size = Pt(opt.get("size", size))
        r.font.bold = opt.get("bold", bold)
        r.font.color.rgb = opt.get("color", color)
    return tb


def new_slide(prs, title, footer, n, total, notes="", title_size=30, tag=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    rect(s, 0, 0, 0.18, 7.5, ACCENT)
    text(s, 0.6, 0.35, 10.6, 0.8, title, size=title_size, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    if tag:
        text(s, 10.3, 0.45, 2.7, 0.6, tag, size=14, color=ACCENT, bold=True,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, 0.65, 1.2, 1.4, 0.06, ACCENT)
    text(s, 0.6, 7.05, 9, 0.35, footer, size=12, color=MUTED)
    text(s, 11.7, 7.05, 1.2, 0.35, f"{n} / {total}", size=12, color=MUTED, align=PP_ALIGN.RIGHT)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def est_lines(s, size, width_in):
    cpl = max(8, int((width_in - 0.1) * 72 / (size * 0.92)))
    return sum(max(1, math.ceil(len(p) / cpl)) for p in s.split("\n"))


def blocks(slide, items, x=0.6, y=1.5, w=5.9, head_size=22, body_size=17, gap=0.14, head_color=ACCENT):
    """(제목, 설명) 목록을 위에서 아래로 쌓는다. 끝 y를 돌려준다."""
    for head, body in items:
        lines = est_lines(body, body_size, w)
        h = head_size * 1.45 / 72 + lines * body_size * 1.5 / 72 + 0.08
        text(slide, x, y, w, h, [(head, {"size": head_size, "bold": True, "color": head_color}),
                                 (body, {"size": body_size, "color": TEXT})], spacing=1.12)
        y += h + gap
    return y


def picture_slot(slide, path, x, y, w, h):
    """16:9 이미지를 테두리 안에 채운다. 파일이 없으면 자리 표시를 남긴다."""
    path = Path(path)
    rect(slide, x, y, w, h, PANEL, MSO_SHAPE.RECTANGLE, line=ACCENT, line_w=1.5)
    if path.is_file():
        slide.shapes.add_picture(str(path), Inches(x + 0.04), Inches(y + 0.04), width=Inches(w - 0.08), height=Inches(h - 0.08))
    else:
        text(slide, x, y + h / 2 - 0.3, w, 0.6, "예시 화면 자리", size=22, bold=True, align=PP_ALIGN.CENTER)


def caption_box(slide, x, y, w, h, label, lines, size=17):
    rect(slide, x, y, w, h, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.08
    rect(slide, x, y + 0.15, 0.08, h - 0.3, ACCENT)
    text(slide, x + 0.25, y + 0.1, w - 0.4, h - 0.2,
         [(label, {"size": size, "bold": True, "color": ACCENT})] + [(ln, {"size": size}) for ln in lines], spacing=1.15)


def sprite_pic(slide, name, x, y, w, h):
    """게임 스프라이트를 정수 배율로 확대해 비율을 유지하며 넣는다."""
    path = ROOT / "assets" / "sprites" / "unified" / f"{name}_idle.png"
    with Image.open(path) as im:
        scale = min(w / im.width, h / im.height)
        iw, ih = im.width * scale, im.height * scale
        big = im.convert("RGBA").resize((im.width * 12, im.height * 12), Image.Resampling.NEAREST)
        data = BytesIO()
        big.save(data, format="PNG")
        data.seek(0)
    slide.shapes.add_picture(data, Inches(x + (w - iw) / 2), Inches(y + (h - ih) / 2), width=Inches(iw), height=Inches(ih))


def table(slide, x, y, widths, rows, size=16, row_h=0.55, head_fill=ACCENT, colors=None):
    """rows[0]은 머리글. 칸은 문자열 또는 (문자열, 색)."""
    cy = y
    for ri, row in enumerate(rows):
        cx = x
        for ci, cell in enumerate(row):
            col = None
            if isinstance(cell, tuple):
                cell, col = cell
            if ri == 0:
                fill, fcol, bold = head_fill, BG, True
            else:
                fill, fcol, bold = (PANEL if ri % 2 else PANEL2), (col or TEXT), False
            rect(slide, cx, cy, widths[ci] - 0.03, row_h - 0.03, fill)
            text(slide, cx + 0.06, cy, widths[ci] - 0.15, row_h - 0.03, cell, size=size,
                 color=fcol, bold=bold, anchor=MSO_ANCHOR.MIDDLE)
            cx += widths[ci]
        cy += row_h
    return cy
