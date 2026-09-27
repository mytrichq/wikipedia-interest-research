from __future__ import annotations

import calendar
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import pandas as pd
from matplotlib import get_data_path
from reportlab.graphics.shapes import Circle, Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from wir import __version__, charts, config, factcheck, languages, study
from wir.config import DATA_DIR

MAX_HEADLINE = 220
MAX_BULLET = 260
MAX_FINDINGS = 4
MAX_NEXT = 3
MAX_TABLE_ROWS = 8
SECTION_WORDS = {
    "headline": ("headline", "висновок", "заголовок", "головне"),
    "findings": ("finding", "спостереж", "знахідк", "результат"),
    "next": ("next", "далі", "кроки", "рекоменд"),
}
TEMPLATE = (
    "# Headline\n<one sentence answer>\n\n## Findings\n- <bullet>\n- <bullet>\n\n"
    "## Next steps\n- <bullet>"
)
TRUST_COLORS = {"High": "#0ca30c", "Medium": "#fab219", "Low": "#d03b3b"}
HEADER, WASH, ACCENT = charts.HEADER, charts.WASH, charts.RECENT
INK, INK2, MUTED = charts.INK, charts.INK_SECONDARY, charts.MUTED
RULE, ZEBRA, DECOR = "#d5e2e1", "#f4f9f8", "#2f8a8c"
PAGE_W, PAGE_H = A4
MARGIN = 15 * mm
HEADER_H = 96
FOOTER_H = 26
FRAME_PADDING = 6
CONTENT_W = PAGE_W - 2 * MARGIN - 2 * FRAME_PADDING
BODY_X = MARGIN + FRAME_PADDING
SCALES = (1.0, 0.94, 0.88, 0.82, 0.76, 0.7)
NARROW_NBSP = chr(0x202F)
CYRILLIC = range(0x0400, 0x0500)


class NarrativeError(ValueError):
    pass


class FactCheckError(NarrativeError):
    pass


@dataclass
class Narrative:
    headline: str = ""
    findings: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    automatic: bool = False

    def text(self) -> str:
        return "\n".join([self.headline, *self.findings, *self.next_steps])


@cache
def strings(lang: str) -> dict:
    table = json.loads((DATA_DIR / "report_i18n.json").read_text(encoding="utf-8"))
    return table.get(lang, table["en"])


def detect_language(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    cyrillic = sum(ord(c) in CYRILLIC for c in letters)
    return "uk" if letters and cyrillic / len(letters) > 0.3 else "en"


def parse_narrative(text: str) -> Narrative:
    narrative, section = Narrative(), None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            section = next(
                (k for k, words in SECTION_WORDS.items() if any(w in title.lower() for w in words)),
                None,
            )
            if section is None and not narrative.headline and len(title) > 20:
                narrative.headline = title
            continue
        item = re.sub(r"^([-*•]|\d+[.)])\s+", "", line)
        if section == "headline":
            narrative.headline = f"{narrative.headline} {item}".strip()
        elif section == "findings":
            narrative.findings.append(item)
        elif section == "next":
            narrative.next_steps.append(item)
    problems = []
    if not narrative.headline:
        problems.append("missing '# Headline' section with one sentence")
    if len(narrative.headline) > MAX_HEADLINE:
        problems.append(
            f"headline is {len(narrative.headline)} chars; keep it under {MAX_HEADLINE}"
        )
    if not 1 <= len(narrative.findings) <= MAX_FINDINGS:
        problems.append(f"'## Findings' needs 1-{MAX_FINDINGS} bullets")
    if len(narrative.next_steps) > MAX_NEXT:
        problems.append(f"'## Next steps' allows at most {MAX_NEXT} bullets")
    long = [b for b in narrative.findings + narrative.next_steps if len(b) > MAX_BULLET]
    if long:
        problems.append(f"{len(long)} bullet(s) longer than {MAX_BULLET} chars; shorten them")
    if problems:
        raise NarrativeError(
            "Narrative file problems: " + "; ".join(problems) + ". Expected format:\n" + TEMPLATE
        )
    return narrative


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value:+.0f}%".replace("-", "−")


def _views(value: float) -> str:
    return f"{round(value):,}".replace(",", NARROW_NBSP)


def _capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def period_text(label: str, lang: str) -> str:
    """'2024-09..2026-08' -> 'вер 2024 – сер 2026'."""
    months = strings(lang)["months"]
    start, end = (part.split("-") for part in label.split(".."))
    return f"{months[int(start[1]) - 1]} {start[0]} – {months[int(end[1]) - 1]} {end[0]}"


def topic_title(document: dict, lang: str) -> str:
    names = []
    for topic in document["spec"]["topics"]:
        labels = topic.get("labels") or {}
        name = labels.get(lang) or labels.get("en") or topic.get("label") or topic["input"]
        names.append(name.split(" + ")[0])
    return ", ".join(names)


def display_names(document: dict, lang: str) -> dict[str, str]:
    """Cell key -> label for people: 'pl' -> 'Польська', topic keys -> localized topic name."""
    topics = document["spec"]["topics"]
    by_label = {t.get("label") or t["input"]: t for t in topics}
    names = {}
    for cell in document["results"]["cells"]:
        language = _capital(languages.display_name(cell["lang"], lang))
        topic = by_label.get(cell["topic"], {})
        topic_name = (topic.get("labels") or {}).get(lang) or cell["topic"]
        if len(topics) == 1:
            names[cell["key"]] = language
        elif len(document["spec"]["langs"]) == 1:
            names[cell["key"]] = _capital(topic_name)
        else:
            names[cell["key"]] = f"{_capital(topic_name)} · {language}"
    return names


def auto_narrative(document: dict, summary: dict, lang: str) -> Narrative:
    s, names = strings(lang), display_names(document, lang)
    verdicts = [r["verdict"] for r in summary["results"] if r.get("status") != "missing"]
    counts = {v: verdicts.count(v) for v in dict.fromkeys(verdicts)}
    total = len(verdicts)
    summary_text = ", ".join(
        s["summary_word"][v].format(n=n, total=total) for v, n in counts.items()
    )
    findings = []
    for row in summary["results"]:
        name = names[row["key"]]
        if row.get("status") == "missing":
            findings.append(s["auto_missing"].format(key=name))
            continue
        findings.append(
            s["auto_cell"].format(
                key=name,
                verdict=s["verdicts"][row["verdict"]],
                yoy=_pct(row["yoy_pct"]),
                up=row["months_up_of_12"],
                trust=s["trust_levels"][row["trust"].split(" ")[0]],
            )
        )
    ranking = summary["ranking"]
    trusted = [r for r in ranking if not _row(summary, r["key"])["trust"].startswith("Low")]
    if trusted and len(ranking) > 1:
        best = trusted[0]
        next_steps = [s["auto_next"].format(key=names[best["key"]], score=best["score"])]
    else:
        next_steps = [s["auto_next_none"]]
    return Narrative(
        headline=s["auto_headline"].format(topic=topic_title(document, lang), summary=summary_text),
        findings=findings[:MAX_FINDINGS],
        next_steps=next_steps,
        automatic=True,
    )


def _row(summary: dict, key: str) -> dict:
    return next(r for r in summary["results"] if r["key"] == key)


def limitations(document: dict, summary: dict, lang: str) -> list[str]:
    s = strings(lang)
    results = document["results"]

    def language(code: str) -> str:
        return _capital(languages.display_name(code, lang))

    items = list(s["lim_fixed"][:2])
    readers, hidden = [], []
    for code, ctx in results["editions"].items():
        codes = languages.hidden_country_codes(code)
        if codes:
            countries = ", ".join(languages.country_name(c, lang) for c in codes)
            hidden.append(s["lim_hidden"].format(lang=language(code), countries=countries))
        else:
            shares = ", ".join(
                f"{languages.country_name(c['country'], lang)} {c['share']:.0%}"
                for c in ctx["top_reader_countries"]
            )
            readers.append(f"{language(code)}: {shares}")
    if readers:
        items[1] += " " + s["lim_readers"].format(items="; ".join(readers))
    items += hidden
    editions = {
        cell["lang"]: cell["metrics"]["relative"]["edition_views_yoy_pct"]
        for cell in results["cells"]
        if cell["status"] == "ok"
    }
    changes = [f"{language(c)} {_pct(v)}" for c, v in editions.items() if v is not None]
    if changes:
        items.append(s["lim_edition"].format(items=", ".join(changes)))
    for proxy in document["spec"].get("proxies", []):
        items.append(s["lim_proxy"].format(lang=language(proxy["lang"]), title=proxy["title"]))
    for cell in results["cells"]:
        if cell["status"] == "missing":
            items.append(s["lim_missing"].format(lang=language(cell["lang"])))
    items.append(s["lim_fixed"][2])
    return items


@cache
def _register_fonts() -> None:
    fonts = DATA_DIR / "fonts"
    for name, file in (
        ("Inter", "Inter-Regular"),
        ("Inter-SemiBold", "Inter-SemiBold"),
        ("Inter-Bold", "Inter-Bold"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(fonts / f"{file}.ttf")))
    dejavu = Path(get_data_path()) / "fonts" / "ttf"
    pdfmetrics.registerFont(TTFont("Fallback", str(dejavu / "DejaVuSans.ttf")))


def _covered(text: str, font: str = "Inter") -> bool:
    glyphs = pdfmetrics.getFont(font).face.charToGlyph
    return all(ord(c) in glyphs or c.isspace() for c in text)


def _t(text: str) -> str:
    """Paragraph-safe text: **bold** is kept, scripts Inter lacks use the fallback font."""
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    return escaped if _covered(plain) else f'<font name="Fallback">{escaped}</font>'


def _styles(scale: float) -> dict[str, ParagraphStyle]:
    _register_fonts()

    def style(name, size, font="Inter", color=INK, leading=1.3, **kw):
        return ParagraphStyle(
            name,
            fontName=font,
            fontSize=size * scale,
            leading=size * scale * leading,
            textColor=colors.HexColor(color),
            **kw,
        )

    return {
        "title": style("title", 19, "Inter-Bold", "#ffffff", 1.18),
        "subtitle": style("subtitle", 8.5, color="#d6ebea"),
        "meta": style("meta", 7.5, color="#ffffff", alignment=2, leading=1.5),
        "label": style("label", 7, "Inter-SemiBold", ACCENT, spaceAfter=1),
        "question": style("question", 8.5, color=INK2),
        "headline": style("headline", 12.5, "Inter-Bold", INK, 1.28),
        "h2": style("h2", 10, "Inter-Bold", HEADER, spaceAfter=3),
        "note": style("note", 7, color=MUTED),
        "tile_value": style("tile_value", 16, "Inter-Bold", HEADER, 1.1),
        "tile_value_small": style("tile_value_small", 12, "Inter-Bold", HEADER, 1.15),
        "tile_caption": style("tile_caption", 7, color=INK2),
        "body": style("body", 8.2),
        "cell": style("cell", 7.4),
        "cell_bold": style("cell_bold", 7.4, "Inter-SemiBold"),
        "cell_head": style("cell_head", 7, "Inter-SemiBold", "#ffffff"),
        "link": style("link", 7.4, color=ACCENT),
        "step_head": style("step_head", 7.5, "Inter-Bold", "#ffffff", alignment=1),
        "step_body": style("step_body", 7.8, color=INK),
        "small": style("small", 7.6, color=INK2, leading=1.35),
        "footer": style("footer", 6.3, color=MUTED),
    }


def make_charts(document: dict, folder: Path, lang: str) -> dict[str, Path]:
    s, names = strings(lang), display_names(document, lang)
    frame = pd.read_csv(folder / "data" / "monthly.csv")
    series, one_offs, changes = {}, {}, []
    ranks = {r["key"]: r["rank"] for r in document["results"]["ranking"]}
    cells = sorted(
        (c for c in document["results"]["cells"] if c["status"] == "ok"),
        key=lambda c: ranks.get(c["key"], 99),
    )
    for cell in cells:
        name = names[cell["key"]]
        rows = frame[(frame["topic"] == cell["topic"]) & (frame["lang"] == cell["lang"])]
        series[name] = pd.Series(
            rows["views"].to_numpy(), index=pd.to_datetime(rows["month"] + "-01")
        )
        clean = cell["metrics"]["growth_without_one_offs"]
        one_offs[name] = [o["month"] for o in clean["one_off_months"]]
        if clean["robust_yoy_pct"] is not None:
            changes.append((name, clean["robust_yoy_pct"]))
    out = folder / "charts"
    out.mkdir(exist_ok=True)
    paths: dict[str, Path] = {}
    if not series:
        return paths
    single = len(series) == 1
    width = CONTENT_W / 72 * (1.0 if single else 0.58)
    height = 2.15 if single or len(series) <= 3 else 2.9
    paths["dynamics"] = charts.dynamics(
        series,
        one_offs,
        out / "dynamics.png",
        months=s["months"],
        one_off_label=s["one_off"],
        width=width,
        height=height,
    )
    if not single and changes:
        paths["change"] = charts.change_bars(
            changes,
            out / "change.png",
            width=CONTENT_W / 72 * 0.36,
            height=min(height, 0.42 * len(changes) + 0.35),
        )
    return paths


def _decorations(canvas, lang: str, document: dict, st: dict) -> None:
    s = strings(lang)
    canvas.saveState()
    canvas.setFillColor(colors.HexColor(HEADER))
    canvas.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor(DECOR))
    for x, y, size in (
        (PAGE_W - 58, PAGE_H, 58),
        (PAGE_W - 104, PAGE_H, 34),
        (PAGE_W, PAGE_H - 62, 30),
    ):
        path = canvas.beginPath()
        path.moveTo(x, y)
        path.lineTo(x + size, y)
        path.lineTo(x + size, y - size)
        path.close()
        canvas.drawPath(path, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor(ACCENT))
    canvas.rect(0, PAGE_H - HEADER_H - 3, PAGE_W, 3, stroke=0, fill=1)

    title = Paragraph(_t(s["title"].format(topic=topic_title(document, lang))), st["title"])
    _, height = title.wrap(CONTENT_W * 0.7, HEADER_H)
    subtitle = Paragraph(_t(s["subtitle"]), st["subtitle"])
    _, sub_height = subtitle.wrap(CONTENT_W * 0.7, HEADER_H)
    top = PAGE_H - (HEADER_H - height - sub_height - 4) / 2
    title.drawOn(canvas, BODY_X, top - height)
    subtitle.drawOn(canvas, BODY_X, top - height - sub_height - 4)

    meta = Paragraph(
        f"{_t(s['report_date'])}: <b>{config.today():%d.%m.%Y}</b><br/>"
        f"{_t(s['period_label'])}: <b>{_t(period_text(document['results']['period'], lang))}</b>",
        st["meta"],
    )
    _, meta_height = meta.wrap(CONTENT_W * 0.28, HEADER_H)
    meta.drawOn(
        canvas, PAGE_W - BODY_X - CONTENT_W * 0.28, PAGE_H - HEADER_H / 2 - meta_height / 2 - 6
    )

    canvas.setStrokeColor(colors.HexColor(RULE))
    canvas.setLineWidth(0.6)
    canvas.line(BODY_X, FOOTER_H, PAGE_W - BODY_X, FOOTER_H)
    qids = ", ".join("+".join(t["qids"]) for t in document["spec"]["topics"])
    footer = s["source"].format(version=__version__, study=document["id"]) + f" · Wikidata {qids}"
    note = Paragraph(_t(footer), st["footer"])
    note.wrap(CONTENT_W, FOOTER_H)
    note.drawOn(canvas, BODY_X, FOOTER_H - 12)
    canvas.restoreState()


def _badge(number: int, size: float) -> Drawing:
    drawing = Drawing(size, size)
    drawing.add(
        Circle(size / 2, size / 2, size / 2, fillColor=colors.HexColor(HEADER), strokeColor=None)
    )
    drawing.add(
        String(
            size / 2,
            size / 2 - size * 0.18,
            str(number),
            fontName="Inter-Bold",
            fontSize=size * 0.5,
            fillColor=colors.white,
            textAnchor="middle",
        )
    )
    return drawing


def _tiles(document: dict, summary: dict, names: dict, s: dict, st: dict, width: float) -> Table:
    cells = {c["key"]: c for c in document["results"]["cells"]}
    ok = [r for r in summary["results"] if r.get("status") != "missing"]
    tiles: list[tuple[str, str]] = []
    if len(summary["results"]) == 1 and ok:
        row = ok[0]
        level = row["trust"].split(" ")[0]
        tiles = [
            (_pct(row["yoy_pct"]), s["tile_change"]),
            (_views(row["avg_monthly_views"]), s["tile_views"]),
            (s["trust_levels"][level], s["tile_trust"]),
        ]
        season = cells[row["key"]]["metrics"].get("seasonality") or {}
        if season.get("strong"):
            month = s["month_names"][list(calendar.month_name).index(season["peak_month"]) - 1]
            tiles.append((f"{month} ×{season['peak_factor']:.1f}", s["tile_season"]))
        else:
            tiles.append((_pct(row["relative_yoy_pct"]), s["tile_relative"]))
    elif ok:
        ranks = {r["key"]: r["rank"] for r in summary["ranking"]}
        best = min(ok, key=lambda r: ranks.get(r["key"], 99))
        growing = sum(r["verdict"] == "growing" for r in ok)
        tiles = [
            (names[best["key"]], s["tile_best"]),
            (_pct(best["yoy_pct"]), s["tile_best_change"]),
            (s["tile_of"].format(n=growing, total=len(ok)), s["tile_growing"]),
            (_views(sum(r["avg_monthly_views"] for r in ok)), s["tile_total_views"]),
        ]
    cells = []
    for value, caption in tiles:
        value_style = st["tile_value"] if len(value) <= 9 else st["tile_value_small"]
        cells.append(
            [Paragraph(_t(value), value_style), Paragraph(_t(caption), st["tile_caption"])]
        )
    gap = 6
    tile_w = (width - gap * (len(cells) - 1)) / max(len(cells), 1)
    row, widths = [], []
    for i, content in enumerate(cells):
        inner = Table([[content[0]], [content[1]]], colWidths=[tile_w])
        inner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(WASH)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
                    ("TOPPADDING", (0, 1), (-1, 1), 1),
                    ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(ACCENT)),
                ]
            )
        )
        row.append(inner)
        widths.append(tile_w)
        if i < len(cells) - 1:
            row.append("")
            widths.append(gap)
    table = Table([row], colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _legend(s: dict, st: dict) -> Paragraph:
    return Paragraph(
        f'<font color="{charts.EARLIER}">■</font> {_t(s["legend_earlier"])}&nbsp;&nbsp;&nbsp;'
        f'<font color="{charts.RECENT}">■</font> {_t(s["legend_recent"])}',
        st["note"],
    )


def _chart_block(chart_paths, s, st, scale) -> list:
    if "dynamics" not in chart_paths:
        return []

    def image(path: Path, width: float) -> Image:
        img = Image(str(path))
        ratio = img.imageHeight / img.imageWidth
        return Image(str(path), width=width * scale, height=width * ratio * scale)

    def heading(title: str, note: str) -> Paragraph:
        return Paragraph(
            f"{_t(title)} <font size='{7 * scale}' color='{MUTED}'>· {_t(note)}</font>", st["h2"]
        )

    if "change" not in chart_paths:
        return [
            heading(s["dynamics_title"], s["dynamics_note_single"]),
            image(chart_paths["dynamics"], CONTENT_W),
            _legend(s, st),
        ]
    left = [
        heading(s["change_title"], s["change_note"]),
        image(chart_paths["change"], CONTENT_W * 0.36),
    ]
    right = [
        heading(s["dynamics_title"], s["dynamics_note"]),
        image(chart_paths["dynamics"], CONTENT_W * 0.58),
        _legend(s, st),
    ]
    table = Table([[left, right]], colWidths=[CONTENT_W * 0.4, CONTENT_W * 0.6])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 14),
            ]
        )
    )
    return [table]


def _table(document, summary, names, s, st) -> Table:
    ranks = {r["key"]: r["rank"] for r in summary["ranking"]}
    cells = {c["key"]: c for c in document["results"]["cells"]}
    rows = sorted(summary["results"], key=lambda r: ranks.get(r["key"], 99))[:MAX_TABLE_ROWS]
    data = [[Paragraph(_t(h), st["cell_head"]) for h in s["table"]]]
    for row in rows:
        cell = cells[row["key"]]
        name = Paragraph(_t(names[row["key"]]), st["cell_bold"])
        if row.get("status") == "missing":
            data.append(["—", name, Paragraph(_t(s["missing"]), st["cell"])] + [""] * 6)
            continue
        edition = languages.get(cell["lang"])
        links = []
        for article in cell["articles"]:
            label = _t(article["title"]) + (f" ({_t(s['proxy'])})" if article["proxy"] else "")
            links.append(f'<link href="{edition.article_url(article["title"])}">{label}</link>')
        level, score = row["trust"].split(" ", 1)
        trust = (
            f'<font color="{TRUST_COLORS[level]}">●</font> {_t(s["trust_levels"][level])} {score}'
        )
        color = charts.POSITIVE if (row["yoy_pct"] or 0) >= 0 else charts.NEGATIVE
        data.append(
            [
                Paragraph(str(ranks.get(row["key"], "")), st["cell"]),
                name,
                Paragraph("<br/>".join(links), st["link"]),
                Paragraph(_views(row["avg_monthly_views"]), st["cell"]),
                Paragraph(
                    f'<font color="{color}"><b>{_pct(row["yoy_pct"])}</b></font>', st["cell"]
                ),
                Paragraph(_pct(row["relative_yoy_pct"]), st["cell"]),
                Paragraph(_pct(row["edition_yoy_pct"]), st["cell"]),
                Paragraph(_t(s["verdicts"][row["verdict"]]), st["cell"]),
                Paragraph(trust, st["cell"]),
            ]
        )
    fractions = [0.035, 0.12, 0.185, 0.1, 0.09, 0.11, 0.09, 0.11, 0.16]
    table = Table(data, colWidths=[CONTENT_W * f for f in fractions], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(HEADER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor(RULE)),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    style += [
        ("BACKGROUND", (0, i), (-1, i), colors.HexColor(ZEBRA)) for i in range(2, len(data), 2)
    ]
    table.setStyle(TableStyle(style))
    return table


def _findings(narrative, s, st, scale) -> list:
    size = 15 * scale
    cards = []
    for number, text in enumerate(narrative.findings, start=1):
        card = Table(
            [[_badge(number, size), Paragraph(_t(text), st["body"])]],
            colWidths=[size + 8, CONTENT_W / 2 - size - 20],
        )
        card.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        cards.append(card)
    grid = [cards[i : i + 2] + [""] * (2 - len(cards[i : i + 2])) for i in range(0, len(cards), 2)]
    table = Table(grid, colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * scale),
            ]
        )
    )
    return [Paragraph(_t(s["findings"]), st["h2"]), table]


def _steps(narrative, s, st) -> list:
    if not narrative.next_steps:
        return []
    count = len(narrative.next_steps)
    gap = 8
    width = (CONTENT_W - gap * (count - 1)) / count
    row, widths = [], []
    for number, text in enumerate(narrative.next_steps, start=1):
        box = Table(
            [
                [Paragraph(_t(s["step"].format(n=number)), st["step_head"])],
                [Paragraph(_t(text), st["step_body"])],
            ],
            colWidths=[width],
        )
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(HEADER)),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor(WASH)),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        row.append(box)
        widths.append(width)
        if number < count:
            row.append("")
            widths.append(gap)
    table = Table([row], colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [Paragraph(_t(s["next_steps"]), st["h2"]), table]


def _story(document, summary, narrative, lang, chart_paths, scale) -> list:
    s, st, names = strings(lang), _styles(scale), display_names(document, lang)
    gap = 7 * scale
    story: list = []
    if document["spec"].get("question"):
        question = Table(
            [
                [
                    Paragraph(
                        f"<font name='Inter-SemiBold' color='{ACCENT}'>"
                        f"{_t(s['question_label'])}:</font> {_t(document['spec']['question'])}",
                        st["question"],
                    )
                ]
            ],
            colWidths=[CONTENT_W],
        )
        question.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(WASH)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story += [question, Spacer(1, gap)]
    story += [
        Paragraph(_t(s["headline_label"].upper()), st["label"]),
        Paragraph(_t(narrative.headline), st["headline"]),
        Spacer(1, gap),
        _tiles(document, summary, names, s, st, CONTENT_W),
        Spacer(1, gap * 1.2),
    ]
    story += _chart_block(chart_paths, s, st, scale)
    story += [
        Spacer(1, gap),
        Paragraph(_t(s["table_title"]), st["h2"]),
        _table(document, summary, names, s, st),
        Spacer(1, gap * 1.2),
    ]
    story += _findings(narrative, s, st, scale)
    story += [Spacer(1, gap * 0.6)] + _steps(narrative, s, st)
    story += [Spacer(1, gap), Paragraph(_t(s["limitations"]), st["h2"])]
    story += [
        Paragraph("– " + _t(item), st["small"]) for item in limitations(document, summary, lang)
    ]
    if narrative.automatic:
        story.append(Paragraph(_t(s["auto_note"]), st["note"]))
    return story


def _page_count(doc: SimpleDocTemplate, story: list, furniture) -> int:
    pages: list[int] = []

    def first(canvas, d):
        pages.append(1)
        furniture(canvas)

    doc.build(story, onFirstPage=first, onLaterPages=lambda canvas, d: pages.append(1))
    return len(pages)


def build_pdf(document, summary, narrative, lang, chart_paths, path: Path) -> int:
    """Shrinks text and charts step by step until everything fits on one A4 page."""
    pages = 0
    header_styles = _styles(1.0)

    def furniture(canvas) -> None:
        _decorations(canvas, lang, document, header_styles)

    for scale in SCALES:
        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=HEADER_H + 14,
            bottomMargin=FOOTER_H + 8,
            title=strings(lang)["title"].format(topic=topic_title(document, lang)),
            author="wikipedia-interest-research",
            subject=document["id"],
        )
        story = _story(document, summary, narrative, lang, chart_paths, scale)
        pages = _page_count(doc, story, furniture)
        if pages == 1:
            break
    return pages


def _markdown_url(url: str) -> str:
    return url.replace("(", "%28").replace(")", "%29")


def summary_markdown(document, summary, narrative, lang) -> str:
    s, names = strings(lang), display_names(document, lang)
    ranks = {r["key"]: r["rank"] for r in summary["ranking"]}
    cells = {c["key"]: c for c in document["results"]["cells"]}
    lines = [f"# {s['title'].format(topic=topic_title(document, lang))}", ""]
    if document["spec"].get("question"):
        lines += [f"> {document['spec']['question']}", ""]
    lines += [f"**{narrative.headline}**", ""]
    lines += ["| " + " | ".join(s["table"]) + " |", "|" + "---|" * len(s["table"])]
    for row in sorted(summary["results"], key=lambda r: ranks.get(r["key"], 99)):
        cell = cells[row["key"]]
        if row.get("status") == "missing":
            lines.append(f"| — | {names[row['key']]} | {s['missing']} |" + " |" * 6)
            continue
        edition = languages.get(cell["lang"])
        links = ", ".join(
            f"[{a['title']}]({_markdown_url(edition.article_url(a['title']))})"
            + (f" ({s['proxy']})" if a["proxy"] else "")
            for a in cell["articles"]
        )
        level, score = row["trust"].split(" ", 1)
        lines.append(
            "| "
            + " | ".join(
                [
                    str(ranks.get(row["key"], "")),
                    names[row["key"]],
                    links,
                    _views(row["avg_monthly_views"]),
                    _pct(row["yoy_pct"]),
                    _pct(row["relative_yoy_pct"]),
                    _pct(row["edition_yoy_pct"]),
                    s["verdicts"][row["verdict"]],
                    f"{s['trust_levels'][level]} {score}",
                ]
            )
            + " |"
        )
    lines += [
        "",
        f"## {s['findings']}",
        *[f"{i}. {f}" for i, f in enumerate(narrative.findings, 1)],
    ]
    lines += ["", f"## {s['next_steps']}", *[f"- {n}" for n in narrative.next_steps]]
    lines += [
        "",
        f"## {s['limitations']}",
        *[f"- {i}" for i in limitations(document, summary, lang)],
    ]
    charts_md = [
        f"![{name}](charts/{name}.png)"
        for name in ("change", "dynamics")
        if (study.study_dir(document["id"]) / "charts" / f"{name}.png").exists()
    ]
    lines += [
        "",
        *charts_md,
        "",
        "_" + s["source"].format(version=__version__, study=document["id"]) + "_",
    ]
    return "\n".join(lines) + "\n"


def build(study_id: str, narrative_path: Path | None, lang: str | None) -> dict:
    document = study.load(study_id)
    summary = study.summarize(document)
    folder = study.study_dir(study_id)
    if narrative_path:
        text = Path(narrative_path).read_text(encoding="utf-8")
        narrative = parse_narrative(text)
        check = factcheck.check(narrative.text(), document)
        if not check["ok"]:
            raise FactCheckError(factcheck.explain(check))
        lang = lang or detect_language(text)
    else:
        lang = lang or "en"
        narrative = auto_narrative(document, summary, lang)
        check = {"ok": True, "numbers_checked": 0, "unmatched": []}
    for stale in (folder / "charts").glob("*.png"):
        stale.unlink()
    chart_paths = make_charts(document, folder, lang)
    pdf = folder / "report.pdf"
    pages = build_pdf(document, summary, narrative, lang, chart_paths, pdf)
    (folder / "summary.md").write_text(
        summary_markdown(document, summary, narrative, lang), encoding="utf-8"
    )
    return {
        "status": "ok",
        "study": study_id,
        "report_language": lang,
        "pdf": str(pdf.resolve()),
        "pages": pages,
        "summary_md": str((folder / "summary.md").resolve()),
        "charts": {k: str(v.resolve()) for k, v in chart_paths.items()},
        "data_csv": str((folder / "data" / "monthly.csv").resolve()),
        "narrative": "automatic (no --narrative given)" if narrative.automatic else "from file",
        "factcheck": {"ok": check["ok"], "numbers_checked": check["numbers_checked"]},
        "limitations_for_chat": limitations(document, summary, lang),
        "reminder": "Keep a short Limitations line in your chat reply (see limitations_for_chat).",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
    }
