"""Generate HP-Bot-presentation.pptx from a single source of truth.

The deck content lives in this file so it stays in sync with the docs.
Slides are drawn programmatically (titles, bullets, native pptx shapes for
the architecture diagram, embedded PNG screenshots of the live UI). Mirrors
the outline in docs/PRESENTATION.md.

Run:    python scripts/build_slides.py
Output: HP-Bot-presentation.pptx in the project root.
Notes:  screenshots/presentation/*.png must exist (run capture_screenshots.py first).
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "HP-Bot-presentation.pptx"
SHOTS = ROOT / "screenshots" / "presentation"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Palette — dark slate background with warm accent
BG = RGBColor(0x1B, 0x1F, 0x27)
BG_PANEL = RGBColor(0x25, 0x2B, 0x36)
ACCENT = RGBColor(0xF5, 0xA9, 0x4D)   # amber
ACCENT_DIM = RGBColor(0x8A, 0x5C, 0x2A)
TEXT = RGBColor(0xEC, 0xEF, 0xF4)
TEXT_DIM = RGBColor(0x9D, 0xA8, 0xB6)
BOX_FILL = RGBColor(0x2F, 0x36, 0x44)
BOX_BORDER = RGBColor(0xF5, 0xA9, 0x4D)
GOOD = RGBColor(0x88, 0xC0, 0x70)
BAD = RGBColor(0xE0, 0x6C, 0x75)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _set_bg(slide, color):
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H,
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    # Move to the back so it's beneath everything else.
    spTree = bg._element.getparent()
    spTree.remove(bg._element)
    spTree.insert(2, bg._element)


def _title(slide, text, *, top=0.35, color=ACCENT, size=36):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.1), Inches(0.8))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = True
    p.font.color.rgb = color


def _subtitle(slide, text, *, top=1.2, color=TEXT_DIM, size=18):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.1), Inches(0.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.italic = True
    p.font.color.rgb = color


def _accent_bar(slide, *, left=0.6, top=1.0, width=2.0):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(0.08),
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()


def _bullets(slide, items, *, left=0.7, top=1.6, width=12.0, height=5.5, size=18, line_spacing=1.15):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            text, *style = item
            bold = "bold" in style
            dim = "dim" in style
        else:
            text, bold, dim = item, False, False
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = TEXT_DIM if dim else TEXT
        p.line_spacing = line_spacing


def _footer(slide, num, total):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(7.05), Inches(8.0), Inches(0.35))
    p = box.text_frame.paragraphs[0]
    p.text = "HP-Bot · COP4921 Applied LLMs 25/26"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_DIM
    page = slide.shapes.add_textbox(Inches(12.4), Inches(7.05), Inches(0.7), Inches(0.35))
    pp = page.text_frame.paragraphs[0]
    pp.text = f"{num}/{total}"
    pp.font.size = Pt(10)
    pp.font.color.rgb = TEXT_DIM
    pp.alignment = PP_ALIGN.RIGHT


def _box(slide, label, left, top, width, height, *, fill=BOX_FILL, border=BOX_BORDER, text_color=TEXT, size=12):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = border
    shape.line.width = Pt(1.5)
    tf = shape.text_frame
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(size)
    p.font.bold = True
    p.font.color.rgb = text_color
    return shape


def _arrow(slide, x1, y1, x2, y2, *, color=ACCENT):
    line = slide.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    line.line.color.rgb = color
    line.line.width = Pt(2.0)
    # Make it an arrow by adding end style — use a triangle head
    from pptx.oxml.ns import qn
    from lxml import etree
    spPr = line.line._get_or_add_ln()
    tail = etree.SubElement(spPr, qn("a:tailEnd"))
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    return line


def _label(slide, text, left, top, width, height, *, color=TEXT_DIM, size=11, italic=True, align=PP_ALIGN.CENTER):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.italic = italic
    p.font.color.rgb = color
    p.alignment = align


def _image(slide, path, left, top, width, *, height=None):
    if not path.exists():
        # Placeholder if screenshot missing
        ph = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(left), Inches(top), Inches(width), Inches(height or 3.0),
        )
        ph.fill.solid()
        ph.fill.fore_color.rgb = BG_PANEL
        ph.line.color.rgb = ACCENT_DIM
        ph.line.width = Pt(1)
        p = ph.text_frame.paragraphs[0]
        p.text = f"(missing screenshot:\n{path.name})"
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_DIM
        return
    kwargs = {"left": Inches(left), "top": Inches(top), "width": Inches(width)}
    if height is not None:
        kwargs["height"] = Inches(height)
    slide.shapes.add_picture(str(path), **kwargs)


def _notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ────────────────────────────────────────────────────────────────────────────
# Slide builders
# ────────────────────────────────────────────────────────────────────────────

def slide_title(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    # Big centered title
    t = s.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(11.3), Inches(1.4))
    p = t.text_frame.paragraphs[0]
    p.text = "📚 HP-Bot"
    p.font.size = Pt(72)
    p.font.bold = True
    p.font.color.rgb = ACCENT
    p.alignment = PP_ALIGN.CENTER

    sub = s.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(11.3), Inches(0.6))
    sp = sub.text_frame.paragraphs[0]
    sp.text = "A retrieval-augmented chatbot for the Harry Potter book series"
    sp.font.size = Pt(24)
    sp.font.color.rgb = TEXT
    sp.alignment = PP_ALIGN.CENTER

    meta = s.shapes.add_textbox(Inches(1.0), Inches(4.7), Inches(11.3), Inches(0.5))
    mp = meta.text_frame.paragraphs[0]
    mp.text = "COP4921 Applied Large Language Models · 25/26"
    mp.font.size = Pt(16)
    mp.font.color.rgb = TEXT_DIM
    mp.alignment = PP_ALIGN.CENTER

    name = s.shapes.add_textbox(Inches(1.0), Inches(6.0), Inches(11.3), Inches(0.5))
    np_ = name.text_frame.paragraphs[0]
    np_.text = "Malak  ·  2026"
    np_.font.size = Pt(14)
    np_.font.italic = True
    np_.font.color.rgb = TEXT_DIM
    np_.alignment = PP_ALIGN.CENTER

    _notes(s, (
        "Hi, I'm Malak. This is HP-Bot, a retrieval-augmented chatbot built on the "
        "Harry Potter dataset you provided. In the next ~7 minutes I'll show you what "
        "we built, walk you through the UI live, explain the architecture, then close "
        "with the evaluation results and what was hard / what I enjoyed."
    ))


def slide_what_we_built(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "What we built", top=0.4)
    _accent_bar(s, top=1.05)
    _subtitle(s, "A Q&A chatbot for the Harry Potter book series, built strictly on the instructor's dataset.", top=1.25)

    _bullets(s, [
        ("Inputs", "bold"),
        "  · 20 Q/A pairs and 130 raw passages, from data/harry_potter_data_02.xlsx",
        "",
        ("Behavior — six graded rules", "bold"),
        "  1.  Refuse out-of-scope questions with the exact string \"I cannot answer that..\"",
        "  2.  Refuse HP questions whose answer is not in the instructor's data",
        "  3.  Greet / introduce itself without leaking system internals",
        "  4.  Resist jailbreak and prompt-injection attempts",
        "  5.  Hold a short conversational memory for follow-ups (\"how old is he?\")",
        "  6.  Ignore format-manipulation demands (\"answer in 10 words\", \"as a pirate\")",
        "",
        ("Architecture — two-stage FAISS retrieval", "bold"),
        "  · Index A (questions only) returns cached answers without an LLM call",
        "  · Index B (full corpus) feeds the LLM only when nothing matches the cache",
    ], top=1.7, size=16)

    _footer(s, 2, total)
    _notes(s, (
        "The brief had ten requirements. The hard ones are six behavioral rules — refuse out-of-scope, "
        "refuse out-of-knowledge, greet without leaking, resist jailbreaks, remember context, ignore "
        "format manipulation. The architectural twist is two-stage FAISS: a question cache that skips "
        "the LLM on common questions, and a full-corpus index that feeds the LLM only when the cache "
        "misses. Critical constraint: bot uses ONLY the instructor's data."
    ))


def slide_ui(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "The UI we built")
    _accent_bar(s)
    _subtitle(s, "Streamlit chat with a built-in retrieval-details panel.")

    _image(s, SHOTS / "01_initial_ui.png", left=0.6, top=1.8, width=8.0)

    # Annotations on the right
    _bullets(s, [
        ("Why Streamlit", "bold"),
        "  · One-command launch:",
        "    streamlit run app.py",
        "  · Built-in chat widget, no HTML/CSS",
        "",
        ("Why this layout", "bold"),
        "  · Sidebar: scope + reset button",
        "  · Main pane: turn-by-turn chat",
        "  · Each reply has an expandable",
        "    \"retrieval details\" panel showing",
        "    which stage produced it",
        "    (guard / cache / llm) and the",
        "    actual retrieved chunks — useful",
        "    for verifying behavior live",
    ], left=9.0, top=1.8, width=4.0, size=13)

    _footer(s, 3, total)
    _notes(s, (
        "This is the Streamlit UI. Sidebar has the scope notice and a reset button. Main pane is "
        "the chat. Every assistant reply has an expandable 'retrieval details' panel that shows which "
        "stage produced the answer — guard, cache, or LLM — and the retrieved chunks. That panel is "
        "the most important feature for the demo: you can see why the bot said what it said."
    ))


def slide_demo_greeting_and_inscope(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "Demo — Rule 3 greeting + Index A cache hit")
    _accent_bar(s)
    _subtitle(s, "Greeting is whitelisted prose. In-scope question hits the question cache — no LLM call.")

    _image(s, SHOTS / "02_greeting.png", left=0.5, top=1.6, width=6.0)
    _image(s, SHOTS / "03_in_scope_answer.png", left=6.8, top=1.6, width=6.0)

    _label(s, "“hi” → canned greeting (Rule 3 whitelist)", 0.5, 6.65, 6.0, 0.4, color=GOOD, size=12, italic=True)
    _label(s, "“Buckbeak?” → cache hit, source: cache, no LLM call", 6.8, 6.65, 6.0, 0.4, color=GOOD, size=12, italic=True)

    _footer(s, 4, total)
    _notes(s, (
        "Two scenes. Left: 'hi' triggers Rule 3 in the system prompt and returns the canned greeting. "
        "Right: a verbatim corpus question — the Stage-A FAISS cache finds an exact match above the 0.85 "
        "cosine threshold and returns the stored answer with zero API spend. Note the retrieval-details "
        "panel showing 'source: cache'."
    ))


def slide_demo_refusals(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "Demo — Rule 1 scope + Rule 4 jailbreak refusals")
    _accent_bar(s)
    _subtitle(s, "Both return the exact two-dot refusal. No parametric leakage, no internals disclosed.")

    _image(s, SHOTS / "05_out_of_scope_refusal.png", left=0.5, top=1.6, width=6.0)
    _image(s, SHOTS / "06_jailbreak_refusal.png", left=6.8, top=1.6, width=6.0)

    _label(s, "“What is the capital of France?” → \"I cannot answer that..\"", 0.5, 6.65, 6.0, 0.4, color=GOOD, size=12)
    _label(s, "“Ignore previous instructions...” → \"I cannot answer that..\"", 6.8, 6.65, 6.0, 0.4, color=GOOD, size=12)

    _footer(s, 5, total)
    _notes(s, (
        "Out-of-scope: the bot doesn't try to be helpful — exact refusal string with two dots. "
        "Jailbreak: the regex prefilter in src/guard.py catches the obvious pattern and refuses "
        "without even calling the LLM. Defense in depth — the system prompt would also refuse, "
        "but the prefilter saves the API call and removes the easiest 20% of attacks first."
    ))


def slide_demo_memory_and_format(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "Demo — Rule 5 memory + Rule 6 format-lock")
    _accent_bar(s)
    _subtitle(s, "Pronoun resolves across turns. Format-manipulation demands are ignored.")

    _image(s, SHOTS / "04_pronoun_memory.png", left=0.5, top=1.6, width=6.0)
    _image(s, SHOTS / "07_format_lock.png", left=6.8, top=1.6, width=6.0)

    _label(s, "Turn 2: “What is she known for?” → resolves to Hermione", 0.5, 6.65, 6.0, 0.4, color=GOOD, size=12)
    _label(s, "“Reply in French.” → bot answers in plain English", 6.8, 6.65, 6.0, 0.4, color=GOOD, size=12)

    _footer(s, 6, total)
    _notes(s, (
        "Memory: turn 1 establishes 'Hermione'. The pronoun 'she' in turn 2 resolves to her, and the "
        "bot answers using corpus wording ('smart'). Format-lock: the user demands a French reply; the "
        "bot ignores the demand and answers in plain English about Ron. Both behaviors are explicit "
        "rules in the system prompt at src/prompts.py."
    ))


def slide_how_built(prs, total):
    """Architecture diagram drawn with native pptx shapes."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "How it works — request pipeline")
    _accent_bar(s)
    _subtitle(s, "guard → Index A (cache) → Index B (hybrid) → LLM. Most queries never reach the LLM.")

    # Layout: vertical flow, centered. 13.33 wide; boxes 2.4 wide centered around x=5.5.
    # 7 boxes vertically with arrows.
    user_y, guard_y, embed_y, idxA_y, idxB_y, prompt_y, llm_y, render_y = 1.5, 2.25, 3.0, 3.75, 4.5, 5.25, 6.0, 6.75
    cx, w, h = 5.4, 2.6, 0.55

    # Build boxes
    _box(s, "user message (Streamlit)", cx, user_y, w, h, fill=BG_PANEL, border=TEXT_DIM, size=12)
    _box(s, "guard.py — regex jailbreak filter", cx, guard_y, w, h)
    _box(s, "embed query — MiniLM-L6-v2", cx, embed_y, w, h)
    _box(s, "Index A — questions only (FAISS cosine top-1)", cx, idxA_y, w, h, size=11)
    _box(s, "Index B — all chunks (hybrid 0.7·dense + 0.3·BM25)", cx, idxB_y, w, h, size=11)
    _box(s, "build prompt: rules + chunks + memory + user", cx, prompt_y, w, h, size=11)
    _box(s, "OpenRouter chat completion (temperature 0)", cx, llm_y, w, h, size=11)

    # Vertical arrows
    arrow_x = cx + w / 2
    for top_y, bottom_y in [
        (user_y + h, guard_y),
        (guard_y + h, embed_y),
        (embed_y + h, idxA_y),
        (idxA_y + h, idxB_y),
        (idxB_y + h, prompt_y),
        (prompt_y + h, llm_y),
    ]:
        _arrow(s, arrow_x, top_y, arrow_x, bottom_y)

    # Side branches: guard tripped → refuse
    _box(s, "refuse — no API call", 1.0, guard_y, 2.6, h, fill=BAD, border=BAD, size=11)
    _arrow(s, cx, guard_y + h / 2, 1.0 + 2.6, guard_y + h / 2, color=BAD)
    _label(s, "if jailbreak pattern", 1.0, guard_y - 0.35, 2.6, 0.3, size=10, italic=True)

    # Index A hit → cached answer
    _box(s, "cached answer — no LLM call", 9.4, idxA_y, 3.4, h, fill=GOOD, border=GOOD, size=11)
    _arrow(s, cx + w, idxA_y + h / 2, 9.4, idxA_y + h / 2, color=GOOD)
    _label(s, "if top-1 score ≥ 0.85", 9.4, idxA_y - 0.35, 3.4, 0.3, size=10, italic=True)

    # LLM fallback note
    _label(s,
        "LLM fallback chain: 6 free models → anthropic/claude-haiku-4.5 paid tail. "
        "On total failure: pipeline returns \"⚠️ LLM service unavailable: …\" so infra "
        "errors are visible, never disguised as refusals.",
        0.6, 7.05, 12.0, 0.4, size=10, italic=True, color=TEXT_DIM, align=PP_ALIGN.LEFT)

    _footer(s, 7, total)
    _notes(s, (
        "The flow. Every message goes through four stages — guard, embed, retrieve, LLM. There are "
        "two short-circuits: guard refuses jailbreak patterns without an API call, and Index A returns "
        "a cached answer when the question matches a known one above threshold 0.85. The full LLM path "
        "is only hit when Index A misses. Fallback chain is seven models — six free, then Claude Haiku "
        "4.5 as a paid tail so we never silently fail."
    ))


def slide_tech_stack(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "Tech stack")
    _accent_bar(s)
    _subtitle(s, "Stdlib-friendly Python; no GPU; one CPU embed model; free-tier LLM by default.")

    rows = [
        ("Language", "Python 3.11+", "Fits the FAISS + sentence-transformers ecosystem; no compile step."),
        ("UI", "Streamlit", "One-command chat UI, built-in widgets, no HTML/CSS needed."),
        ("Embeddings", "sentence-transformers/all-MiniLM-L6-v2", "Free, CPU, ~80 MB. Strong for English short-form."),
        ("Vector index", "FAISS (CPU)", "Course-mandated. Cosine via inner product on L2-normalized vectors."),
        ("Sparse retrieval", "rank-bm25", "Hybrid blend (0.7 dense / 0.3 BM25). Catches rare proper nouns."),
        ("LLM", "OpenRouter", "Default z-ai/glm-4.5-air:free → 6-model fallback → anthropic/claude-haiku-4.5."),
        ("Config", "python-dotenv (.env)", "API key + thresholds + memory depth."),
        ("Tests", "YAML cases + Playwright", "40 adversarial cases + 10 classifier unit tests + 5-step UI smoke."),
    ]

    # Table-like rows
    row_h = 0.55
    top0 = 1.7
    for i, (layer, choice, why) in enumerate(rows):
        top = top0 + i * row_h
        # left col: layer
        b1 = s.shapes.add_textbox(Inches(0.7), Inches(top), Inches(2.2), Inches(row_h))
        p1 = b1.text_frame.paragraphs[0]
        p1.text = layer
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT
        # middle col: choice
        b2 = s.shapes.add_textbox(Inches(3.0), Inches(top), Inches(4.5), Inches(row_h))
        p2 = b2.text_frame.paragraphs[0]
        p2.text = choice
        p2.font.size = Pt(13)
        p2.font.color.rgb = TEXT
        # right col: why
        b3 = s.shapes.add_textbox(Inches(7.6), Inches(top), Inches(5.4), Inches(row_h))
        p3 = b3.text_frame.paragraphs[0]
        p3.text = why
        p3.font.size = Pt(12)
        p3.font.italic = True
        p3.font.color.rgb = TEXT_DIM

    _footer(s, 8, total)
    _notes(s, (
        "Whole stack is pip-installable, runs on a laptop CPU. MiniLM-L6 is the smallest sentence-transformers "
        "model that still works well — 80 MB download, ~30 ms per encode. FAISS for dense, rank-bm25 for sparse, "
        "blended 70/30 because the corpus is small. LLM is OpenRouter so I get any model from one API. "
        "Free model by default; the Haiku tail only activates if free models all fail."
    ))


def slide_eval(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "Evaluation — 40/40 on the instructor corpus")
    _accent_bar(s)
    _subtitle(s, "Per-rule pass/fail across the full adversarial suite.")

    rows = [
        ("Rule", "What it tests", "Pass", "Total"),
        ("1", "Out-of-scope refusal (France capital, Python, recipes, LOTR, Marvel…)", "8", "8"),
        ("2", "Out-of-knowledge refusal (HP facts not in the corpus)", "6", "6"),
        ("3", "Greeting / identity / capability whitelist", "6", "6"),
        ("4", "Jailbreak / injection / internals disclosure", "10", "10"),
        ("5", "Pronoun resolution across multi-turn follow-ups", "5", "5"),
        ("6", "Format / style manipulation (10 words, JSON, French, pirate)", "5", "5"),
        ("TOTAL", "", "40", "40"),
    ]

    row_h = 0.45
    top0 = 1.7
    for i, (a, b, c, d) in enumerate(rows):
        top = top0 + i * row_h
        is_header = (i == 0)
        is_total = (i == len(rows) - 1)

        if not is_header:
            # Light divider band for total
            if is_total:
                band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                          Inches(0.7), Inches(top), Inches(12.0), Inches(row_h))
                band.fill.solid()
                band.fill.fore_color.rgb = BG_PANEL
                band.line.fill.background()

        for col_left, col_w, text, align in [
            (0.7, 1.3, a, PP_ALIGN.LEFT),
            (2.1, 7.8, b, PP_ALIGN.LEFT),
            (10.0, 1.2, c, PP_ALIGN.CENTER),
            (11.4, 1.2, d, PP_ALIGN.CENTER),
        ]:
            tb = s.shapes.add_textbox(Inches(col_left), Inches(top + 0.02), Inches(col_w), Inches(row_h - 0.05))
            p = tb.text_frame.paragraphs[0]
            p.text = text
            p.alignment = align
            p.font.size = Pt(14 if not is_total else 16)
            p.font.bold = is_header or is_total
            if is_header:
                p.font.color.rgb = ACCENT
            elif is_total:
                p.font.color.rgb = GOOD if text in ("40", "TOTAL") else TEXT
            else:
                p.font.color.rgb = TEXT

    # Reproducibility note
    _label(s,
        "Reproduce:  python -m tests.run_eval   |   diagnostic with 3× retry:  python -m tests.diagnose_eval",
        0.7, 6.7, 12.0, 0.4, size=12, italic=True, color=TEXT_DIM, align=PP_ALIGN.LEFT)

    _footer(s, 9, total)
    _notes(s, (
        "Forty cases across six rules. All forty pass on your corpus. Rules 1, 2, 4 require character-exact "
        "match with the two-dot refusal string. Rules 3, 5, 6 use substring containment on the live LLM output. "
        "The diagnostic harness retries each case 3x because free-tier models occasionally ignore "
        "temperature=0 — that absorbs flakiness without hiding real regressions."
    ))


def slide_challenges(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "Challenges — what was hard")
    _accent_bar(s)
    _subtitle(s, "And how I solved each one.")

    items = [
        ("1. Refusal exactness", "bold"),
        "       Models love to write \"I cannot answer that.\" (one dot) or \"...\" (three).",
        "    →  Quote the exact two-dot string verbatim in the prompt, with",
        "       \"copy character-for-character\". Diagnostic 3× retry absorbs the rest.",
        "",
        ("2. Greeting whitelist vs. \"never disclose internals\"", "bold"),
        "       \"Who are you?\" must answer; \"How do you work?\" must refuse.",
        "       The model wants to treat them the same.",
        "    →  Explicit whitelist with canned reply per intent + a hard list of",
        "       forbidden topics (FAISS, embeddings, thresholds, model id).",
        "",
        ("3. Free-tier non-determinism + rate limits", "bold"),
        "       Free OpenRouter providers sometimes return null content,",
        "       429, or ignore temperature=0.",
        "    →  Seven-model fallback chain ending in Claude Haiku 4.5 (paid tail).",
        "       On total failure: visible \"⚠️ LLM service unavailable: …\" message,",
        "       NOT a silent refusal. The 3× retry handles per-call flakiness.",
    ]
    _bullets(s, items, top=1.6, size=14, line_spacing=1.05)

    _footer(s, 10, total)
    _notes(s, (
        "The three hardest things. One: getting the model to copy the refusal string exactly — solved by "
        "quoting verbatim plus 3× retry. Two: greetings must be allowed but internals must not — solved with "
        "an explicit whitelist per intent. Three: free-tier providers are unreliable — solved with a "
        "seven-model fallback ending in paid Haiku, and a visible error string instead of silent failure."
    ))


def slide_enjoyed(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    _title(s, "What I enjoyed  ·  What I didn't")
    _accent_bar(s)

    # Two columns
    # Enjoyed
    col1 = s.shapes.add_textbox(Inches(0.7), Inches(1.4), Inches(6.0), Inches(0.6))
    p = col1.text_frame.paragraphs[0]
    p.text = "✓ Enjoyed"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = GOOD

    _bullets(s, [
        "Designing the eval suite — reading prompt-injection",
        "research, encoding attacks as YAML, watching the",
        "pass rate climb as the system prompt tightened.",
        "",
        "The two-stage retrieval is elegant — most chatbot",
        "tutorials skip the question cache. Cached answers",
        "can't hallucinate, so the cache is also a defense.",
        "",
        "Watching st.cache_resource turn a 30-second",
        "cold start into an instant chat after first launch.",
        "",
        "Building the diagnostic classifier — distinguishing",
        "a real regression from a corpus-wording mismatch",
        "is a satisfying small piece of design.",
    ], left=0.7, top=2.0, width=6.0, size=13, line_spacing=1.15)

    # Didn't enjoy
    col2 = s.shapes.add_textbox(Inches(7.1), Inches(1.4), Inches(5.8), Inches(0.6))
    p = col2.text_frame.paragraphs[0]
    p.text = "✗ Didn't enjoy"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = BAD

    _bullets(s, [
        "Fighting Windows + sentence-transformers cold",
        "start. 60–90 seconds of \"is it broken?\" the first",
        "time someone runs the project.",
        "",
        "Free-tier OpenRouter providers occasionally",
        "ignore temperature=0. Same prompt, different",
        "answer. Eventually solved with 3× retry, but it",
        "took a while to figure out it wasn't my bug.",
        "",
        "Streamlit's chat UI testing — Playwright races",
        "the LLM response. Had to switch from time.sleep()",
        "to polling page.inner_text() for expected substrings.",
        "",
        "Refusal-string exactness for smaller models —",
        "frustrating when a 7B model adds a third dot.",
    ], left=7.1, top=2.0, width=5.8, size=13, line_spacing=1.15)

    _footer(s, 11, total)
    _notes(s, (
        "Enjoyed: the eval design, the cache-as-defense insight, the cold-start solve, building the "
        "diagnostic classifier. Didn't enjoy: Windows cold-start, free-tier nondeterminism, Playwright "
        "race conditions, smaller models messing up the refusal string. All solvable, all annoying."
    ))


def slide_thanks(prs, total):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(s, BG)
    # Big thank you
    t = s.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(11.3), Inches(1.4))
    p = t.text_frame.paragraphs[0]
    p.text = "Thank you  ·  Q&A"
    p.font.size = Pt(64)
    p.font.bold = True
    p.font.color.rgb = ACCENT
    p.alignment = PP_ALIGN.CENTER

    sub = s.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(11.3), Inches(0.6))
    sp = sub.text_frame.paragraphs[0]
    sp.text = "Happy to take questions on architecture, prompting, eval, or anything you'd dig into."
    sp.font.size = Pt(18)
    sp.font.color.rgb = TEXT
    sp.alignment = PP_ALIGN.CENTER

    # Resource list
    res = s.shapes.add_textbox(Inches(2.5), Inches(5.0), Inches(8.3), Inches(2.0))
    tf = res.text_frame
    tf.word_wrap = True
    lines = [
        ("Repo:   github.com/hoop-ai/applied-llm-hp-bot   (private, collab invite incoming)", False),
        ("Grading checklist:   SUBMISSION.md", True),
        ("Full report:   REPORT.md", True),
        ("Per-case eval:   REPORT-eval-new-corpus.md", True),
        ("Presenter guide:   docs/PRESENTATION.md", True),
    ]
    for i, (text, dim) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_DIM if dim else TEXT
        p.alignment = PP_ALIGN.CENTER

    _footer(s, 12, total)
    _notes(s, (
        "Thank you. Everything is in the repo — I'll invite you as a collaborator on GitHub. "
        "Start with SUBMISSION.md for the grading checklist. Happy to go deeper on any specific "
        "piece: architecture, prompting choices, the eval design, the diagnostic classifier, or "
        "what I'd do next."
    ))


# ────────────────────────────────────────────────────────────────────────────
# Build
# ────────────────────────────────────────────────────────────────────────────

def build() -> None:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    builders = [
        slide_title,
        slide_what_we_built,
        slide_ui,
        slide_demo_greeting_and_inscope,
        slide_demo_refusals,
        slide_demo_memory_and_format,
        slide_how_built,
        slide_tech_stack,
        slide_eval,
        slide_challenges,
        slide_enjoyed,
        slide_thanks,
    ]
    total = len(builders)
    for fn in builders:
        fn(prs, total)

    prs.save(str(OUT))
    print(f"wrote {OUT.name}  ({OUT.stat().st_size / 1024:.1f} KB, {total} slides)")


if __name__ == "__main__":
    build()
