from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import pandas as pd
from matplotlib import get_data_path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from wir import __version__, charts, config, factcheck, study
from wir.config import DATA_DIR

MAX_HEADLINE = 220
MAX_BULLET = 260
MAX_FINDINGS = 4
MAX_AUTO_FINDINGS = 6
MAX_NEXT = 3
MAX_TABLE_ROWS = 8
TRUST_COLORS = {"High": "#0ca30c", "Medium": "#fab219", "Low": "#d03b3b"}
INK, INK2, MUTED, RULE, WASH = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#f4f3ef"
SECTION_WORDS = {
    "headline": ("headline", "висновок", "заголовок", "головне"),
    "findings": ("finding", "спостереж", "знахідк", "результат"),
    "next": ("next", "далі", "кроки", "рекоменд"),
}
MARGIN = 14 * mm
FRAME_PADDING = 12
SCALES = (1.2, 1.1, 1.0, 0.92, 0.84, 0.76)


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
    cyrillic = sum("Ѐ" <= c <= "ӿ" for c in letters)
    return "uk" if letters and cyrillic / len(letters) > 0.3 else "en"


def parse_narrative(text: str) -> Narrative:
    narrative, section = Narrative(), None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            title = line.lstrip("#").strip().lower()
            section = next(
                (k for k, words in SECTION_WORDS.items() if any(w in title for w in words)), None
            )
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
            "Narrative file problems: "
            + "; ".join(problems)
            + ". Follow assets/narrative_template.md."
        )
    return narrative


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value:+.0f}%".replace("-", "−")


def _views(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def topic_title(document: dict, lang: str) -> str:
    names = []
    for topic in document["spec"]["topics"]:
        labels = topic.get("labels") or {}
        name = labels.get(lang) or labels.get("en") or topic.get("label") or topic["input"]
        parts = name.split(" + ")
        names.append(parts[0] + (" + …" if len(parts) > 1 else ""))
    return ", ".join(names)


def auto_narrative(document: dict, summary: dict, lang: str) -> Narrative:
    s = strings(lang)
    verdicts = [r["verdict"] for r in summary["results"] if r.get("status") != "missing"]
    counts = {v: verdicts.count(v) for v in dict.fromkeys(verdicts)}
    total = len(verdicts)
    summary_text = ", ".join(
        s["summary_word"][v].format(n=n, total=total) for v, n in counts.items()
    )
    findings = []
    for row in summary["results"]:
        if row.get("status") == "missing":
            findings.append(s["auto_missing"].format(key=row["key"]))
            continue
        findings.append(
            s["auto_cell"].format(
                key=row["key"],
                verdict=s["verdicts"][row["verdict"]],
                yoy=_pct(row["yoy_pct"]),
                up=row["months_up_of_12"],
                trust=s["trust_levels"][row["trust"].split(" ")[0]],
            )
        )
    ranking = summary["ranking"]
    trusted = [r for r in ranking if not _row(summary, r["key"])["trust"].startswith("Low")]
    if trusted and len(ranking) > 1:
        next_steps = [s["auto_next"].format(key=trusted[0]["key"], score=trusted[0]["score"])]
    else:
        next_steps = [s["auto_next_none"]]
    return Narrative(
        headline=s["auto_headline"].format(topic=topic_title(document, lang), summary=summary_text),
        findings=findings[:MAX_AUTO_FINDINGS],
        next_steps=next_steps,
        automatic=True,
    )


def _row(summary: dict, key: str) -> dict:
    return next(r for r in summary["results"] if r["key"] == key)


def limitations(document: dict, summary: dict, lang: str) -> list[str]:
    s = strings(lang)
    results = document["results"]
    items = list(s["lim_fixed"][:2])
    readers, hidden = [], []
    for code, ctx in results["editions"].items():
        if ctx.get("hidden_countries"):
            hidden.append(
                s["lim_hidden"].format(lang=code, countries=", ".join(ctx["hidden_countries"]))
            )
        else:
            shares = ", ".join(
                f"{c['country']} {c['share']:.0%}" for c in ctx["top_reader_countries"]
            )
            readers.append(f"{code}: {shares}")
    if readers:
        items[1] += " " + s["lim_readers"].format(items="; ".join(readers))
    items += hidden
    editions = {
        cell["lang"]: cell["metrics"]["relative"]["edition_views_yoy_pct"]
        for cell in results["cells"]
        if cell["status"] == "ok"
    }
    changes = [f"{code} {_pct(value)}" for code, value in editions.items() if value is not None]
    if changes:
        items.append(s["lim_edition"].format(items=", ".join(changes)))
    for proxy in document["spec"].get("proxies", []):
        items.append(s["lim_proxy"].format(lang=proxy["lang"], title=proxy["title"]))
    for row in summary["results"]:
        if row.get("status") == "missing":
            items.append(s["lim_missing"].format(lang=row["key"]))
    items.append(s["lim_fixed"][2])
    return items


def _fonts() -> tuple[str, str]:
    if "WirSans" not in pdfmetrics.getRegisteredFontNames():
        folder = Path(get_data_path()) / "fonts" / "ttf"
        pdfmetrics.registerFont(TTFont("WirSans", str(folder / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("WirSans-Bold", str(folder / "DejaVuSans-Bold.ttf")))
    return "WirSans", "WirSans-Bold"


def _renderable(text: str) -> bool:
    glyphs = pdfmetrics.getFont("WirSans").face.charToGlyph
    return all(ord(c) in glyphs or c.isspace() for c in text)


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_charts(document: dict, folder: Path, lang: str) -> dict[str, Path]:
    s = strings(lang)
    frame = pd.read_csv(folder / "data" / "monthly.csv")
    series, one_offs = {}, {}
    for cell in document["results"]["cells"]:
        if cell["status"] != "ok":
            continue
        rows = frame[(frame["topic"] == cell["topic"]) & (frame["lang"] == cell["lang"])]
        series[cell["key"]] = pd.Series(
            rows["views"].to_numpy(), index=pd.to_datetime(rows["month"] + "-01")
        )
        one_offs[cell["key"]] = [
            o["month"] for o in cell["metrics"]["growth_without_one_offs"]["one_off_months"]
        ]
    out = folder / "charts"
    out.mkdir(exist_ok=True)
    paths = {}
    if series:
        single = len(series) == 1
        paths["trend"] = charts.trend(
            series,
            one_offs,
            out / "trend.png",
            title=s["trend_title_single"] if single else s["trend_title"],
            axis_label=s["views_axis"] if single else s["index_axis"],
            one_off_label=s["one_off"],
            index=not single,
        )
        summary = study.summarize(document)
        paths["growth"] = charts.growth(
            [
                (r["key"], r.get("yoy_pct"))
                for r in summary["results"]
                if r.get("status") != "missing"
            ],
            out / "growth.png",
            title=s["table"][4],
        )
    return paths


def _styles(scale: float) -> dict[str, ParagraphStyle]:
    regular, bold = _fonts()

    def style(name, size, font=regular, color=INK, leading=1.25, **kw):
        return ParagraphStyle(
            name,
            fontName=font,
            fontSize=size * scale,
            leading=size * scale * leading,
            textColor=colors.HexColor(color),
            alignment=TA_LEFT,
            **kw,
        )

    return {
        "title": style("title", 15, bold),
        "meta": style("meta", 8, color=MUTED),
        "question": style("question", 9, color=INK2),
        "headline": style("headline", 11.5, bold, leading=1.3),
        "h2": style("h2", 9, bold, spaceBefore=4 * scale, spaceAfter=2 * scale),
        "body": style("body", 8.2),
        "cell": style("cell", 7.4),
        "cell_bold": style("cell_bold", 7.4, bold),
        "small": style("small", 6.9, color=INK2),
        "footer": style("footer", 6.5, color=MUTED),
    }


def _story(document, summary, narrative, lang, chart_paths, scale):
    s, st = strings(lang), _styles(scale)
    width = A4[0] - 2 * MARGIN - FRAME_PADDING
    results = document["results"]
    story = [
        Paragraph(_esc(s["title"].format(topic=topic_title(document, lang))), st["title"]),
        Paragraph(
            _esc(
                s["meta"].format(
                    langs=", ".join(document["spec"]["langs"]),
                    period=results["period"],
                    today=config.today().isoformat(),
                )
            ),
            st["meta"],
        ),
    ]
    if document["spec"].get("question"):
        story.append(Paragraph(_esc(f"«{document['spec']['question']}»"), st["question"]))
    story.append(Spacer(1, 4 * scale))
    headline = Table([[Paragraph(_esc(narrative.headline), st["headline"])]], colWidths=[width])
    headline.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(WASH)),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(charts.PALETTE[0])),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story += [headline, Spacer(1, 5 * scale)]
    if "trend" in chart_paths:
        chart_width = width * min(1.0, scale)
        chart_height = chart_width * charts.TREND_SIZE[1] / charts.TREND_SIZE[0]
        story += [
            Image(str(chart_paths["trend"]), width=chart_width, height=chart_height),
            Spacer(1, 4 * scale),
        ]
    story.append(_table(summary, s, st, width))
    columns = [
        [Paragraph(_esc(s["findings"]), st["h2"])]
        + [Paragraph("• " + _esc(f), st["body"]) for f in narrative.findings],
        [Paragraph(_esc(s["next_steps"]), st["h2"])]
        + [Paragraph("→ " + _esc(n), st["body"]) for n in narrative.next_steps],
    ]
    two = Table([columns], colWidths=[width * 0.56, width * 0.44])
    two.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 10),
            ]
        )
    )
    story += [Spacer(1, 3 * scale), two]
    story.append(Paragraph(_esc(s["limitations"]), st["h2"]))
    for item in limitations(document, summary, lang):
        story.append(Paragraph("– " + _esc(item), st["small"]))
    footer = s["source"].format(version=__version__, study=document["id"])
    qids = ", ".join("+".join(t["qids"]) for t in document["spec"]["topics"])
    footer += f" · Wikidata {qids}"
    if narrative.automatic:
        footer += " · " + s["auto_note"]
    story += [Spacer(1, 4 * scale), Paragraph(_esc(footer), st["footer"])]
    return story


def _table(summary, s, st, width):
    ranks = {r["key"]: r["rank"] for r in summary["ranking"]}
    rows = sorted(summary["results"], key=lambda r: ranks.get(r["key"], 99))[:MAX_TABLE_ROWS]
    header = [Paragraph(_esc(h), st["cell_bold"]) for h in s["table"]]
    data = [header]
    for row in rows:
        articles = [a for a in row.get("articles", []) if _renderable(a)] or ["—"]
        article_text = ", ".join(articles).replace("(PROXY)", f"({s['proxy']})")
        if row.get("status") == "missing":
            data.append(
                [
                    "—",
                    Paragraph(_esc(row["key"]), st["cell_bold"]),
                    Paragraph(_esc(s["missing"]), st["cell"]),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            continue
        level = row["trust"].split(" ")[0]
        score = row["trust"].split(" ", 1)[1]
        label = f"{s['trust_levels'][level]} {score}"
        dot = f'<font color="{TRUST_COLORS[level]}">●</font> {_esc(label)}'
        data.append(
            [
                str(ranks.get(row["key"], "")),
                Paragraph(_esc(row["key"]), st["cell_bold"]),
                Paragraph(_esc(article_text), st["cell"]),
                Paragraph(_views(row["avg_monthly_views"]), st["cell"]),
                Paragraph(_pct(row["yoy_pct"]), st["cell_bold"]),
                Paragraph(_pct(row["relative_yoy_pct"]), st["cell"]),
                Paragraph(_pct(row["edition_yoy_pct"]), st["cell"]),
                Paragraph(_esc(s["verdicts"][row["verdict"]]), st["cell"]),
                Paragraph(dot, st["cell"]),
            ]
        )
    fractions = [0.04, 0.08, 0.17, 0.1, 0.09, 0.13, 0.1, 0.12, 0.17]
    table = Table(data, colWidths=[width * f for f in fractions], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "WirSans"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.4),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(INK2)),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor(RULE)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ]
        )
    )
    return table


def _page_count(doc: SimpleDocTemplate, story: list) -> int:
    pages: list[int] = []
    doc.build(
        story,
        onFirstPage=lambda canvas, d: pages.append(1),
        onLaterPages=lambda canvas, d: pages.append(1),
    )
    return len(pages)


def build_pdf(document, summary, narrative, lang, chart_paths, path: Path) -> int:
    """Shrinks fonts and the chart step by step until everything fits on one page."""
    pages = 0
    for scale in SCALES:
        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=MARGIN,
            title=strings(lang)["title"].format(topic=topic_title(document, lang)),
            author="wikipedia-interest-research",
            subject=document["id"],
        )
        pages = _page_count(doc, _story(document, summary, narrative, lang, chart_paths, scale))
        if pages == 1:
            break
    return pages


def summary_markdown(document, summary, narrative, lang) -> str:
    s = strings(lang)
    ranks = {r["key"]: r["rank"] for r in summary["ranking"]}
    lines = [f"# {s['title'].format(topic=topic_title(document, lang))}", ""]
    lines += [f"**{narrative.headline}**", ""]
    lines += ["| " + " | ".join(s["table"]) + " |", "|" + "---|" * len(s["table"])]
    for row in sorted(summary["results"], key=lambda r: ranks.get(r["key"], 99)):
        if row.get("status") == "missing":
            lines.append(f"| — | {row['key']} | {s['missing']} |" + " |" * 6)
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(ranks.get(row["key"], "")),
                    row["key"],
                    ", ".join(row["articles"]),
                    _views(row["avg_monthly_views"]),
                    _pct(row["yoy_pct"]),
                    _pct(row["relative_yoy_pct"]),
                    _pct(row["edition_yoy_pct"]),
                    s["verdicts"][row["verdict"]],
                    row["trust"],
                ]
            )
            + " |"
        )
    lines += ["", f"## {s['findings']}", *[f"- {f}" for f in narrative.findings]]
    lines += ["", f"## {s['next_steps']}", *[f"- {n}" for n in narrative.next_steps]]
    lines += [
        "",
        f"## {s['limitations']}",
        *[f"- {i}" for i in limitations(document, summary, lang)],
    ]
    lines += [
        "",
        "![trend](charts/trend.png)",
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
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
    }
