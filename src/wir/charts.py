from __future__ import annotations

from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SURFACE = "#ffffff"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
POSITIVE = "#2a78d6"
NEGATIVE = "#e34948"
MAX_SERIES = len(PALETTE)
DIRECT_LABELS_UP_TO = 4
TREND_SIZE = (7.3, 3.1)


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)


def trend(
    series: dict[str, pd.Series],
    one_offs: dict[str, list[str]],
    path: Path,
    *,
    title: str,
    axis_label: str,
    one_off_label: str,
    index: bool,
) -> Path:
    """Lines per entity, colour fixed by entity order; indexed when scales differ."""
    fig = Figure(figsize=TREND_SIZE, dpi=200)
    ax = fig.subplots()
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    keys = list(series)[:MAX_SERIES]
    ends = []
    for slot, key in enumerate(keys):
        values = series[key].astype(float)
        if index:
            base = values.iloc[:12].mean() or 1.0
            values = values / base * 100
        color = PALETTE[slot]
        ax.plot(
            values.index,
            values.to_numpy(),
            color=color,
            linewidth=2,
            solid_capstyle="round",
            solid_joinstyle="round",
            label=key,
        )
        for month in one_offs.get(key, []):
            stamp = pd.Timestamp(f"{month}-01")
            if stamp in values.index:
                ax.scatter(
                    [stamp],
                    [values[stamp]],
                    s=40,
                    facecolor=SURFACE,
                    edgecolor=color,
                    linewidth=1.6,
                    zorder=3,
                )
                ax.annotate(
                    one_off_label,
                    (stamp, values[stamp]),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=7,
                    color=INK_SECONDARY,
                )
        ends.append((values.index[-1], float(values.iloc[-1]), key, color))
    if index:
        ax.axhline(100, color=AXIS, linewidth=0.8)
    if len(keys) <= DIRECT_LABELS_UP_TO:
        _direct_labels(ax, ends)
    if len(keys) >= 2:
        ax.legend(
            loc="lower left",
            bbox_to_anchor=(0, 1.0),
            ncol=min(len(keys), 8),
            frameon=False,
            fontsize=8,
            labelcolor=INK_SECONDARY,
            handlelength=1.5,
            borderaxespad=0,
        )
    ax.set_title(title, loc="left", fontsize=9, color=INK, pad=22 if len(keys) >= 2 else 6)
    ax.set_ylabel(axis_label, fontsize=8, color=MUTED)
    ax.set_ylim(bottom=0)
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    return path


def _direct_labels(ax, ends) -> None:
    low, high = ax.get_ylim()
    gap = (high - low) * 0.06
    placed: list[float] = []
    for x, y, key, _ in sorted(ends, key=lambda e: e[1]):
        while any(abs(y - p) < gap for p in placed):
            y += gap
        placed.append(y)
        ax.annotate(
            key,
            (x, y),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
            color=INK_SECONDARY,
        )
        ax.scatter([x], [y], s=0)
    ax.margins(x=0.06)


def growth(rows: list[tuple[str, float | None]], path: Path, *, title: str) -> Path:
    """Horizontal diverging bars of year-over-year change."""
    rows = [(k, v) for k, v in rows if v is not None]
    fig = Figure(figsize=(4.6, 0.4 + 0.32 * max(len(rows), 1)), dpi=200)
    ax = fig.subplots()
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    labels = [k for k, _ in rows][::-1]
    values = [v for _, v in rows][::-1]
    colors = [POSITIVE if v >= 0 else NEGATIVE for v in values]
    ax.barh(labels, values, color=colors, height=0.45)
    ax.axvline(0, color=AXIS, linewidth=1)
    span = max((abs(v) for v in values), default=1) or 1
    for position, value in enumerate(values):
        offset = span * 0.03 * (1 if value >= 0 else -1)
        ax.text(
            value + offset,
            position,
            f"{value:+.0f}%".replace("-", "−"),
            va="center",
            ha="left" if value >= 0 else "right",
            fontsize=8,
            color=INK,
        )
    ax.set_xlim(-span * 1.35, span * 1.35)
    ax.set_title(title, loc="left", fontsize=9, color=INK)
    ax.tick_params(axis="y", labelcolor=INK_SECONDARY)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    return path
