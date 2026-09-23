from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from matplotlib import font_manager, rcParams
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from wir.config import DATA_DIR

HEADER = "#0e5f63"
WASH = "#e3f0ef"
POSITIVE = "#008f86"
NEGATIVE = "#e0603f"
EARLIER = "#6db8b1"
RECENT = "#0b6e6a"
INK = "#10201f"
INK_SECONDARY = "#4a5a59"
MUTED = "#7d8b8a"
GRID = "#dfe8e7"
AXIS = "#b9c9c8"
SURFACE = "#ffffff"
FONT = "Inter"
MAX_PANELS = 8
BLOCK_MONTHS = 3

for _weight in ("Regular", "SemiBold", "Bold"):
    font_manager.fontManager.addfont(str(DATA_DIR / "fonts" / f"Inter-{_weight}.ttf"))
rcParams["font.family"] = [FONT, "DejaVu Sans"]


def _figure(width: float, height: float) -> Figure:
    fig = Figure(figsize=(width, height), dpi=220)
    fig.patch.set_facecolor(SURFACE)
    return fig


def _style(ax, grid_axis: str = "y") -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=7, length=0)


def _fmt_pct(value: float) -> str:
    return f"{value:+.0f}%".replace("-", "−")


def _fmt_views(value: float) -> str:
    if value >= 10_000:
        return f"{value / 1000:.0f}k"
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return f"{value:.0f}"


def change_bars(rows: list[tuple[str, float]], path: Path, *, width: float, height: float) -> Path:
    """Year-over-year change per entity: teal up, coral down, the value at the bar end."""
    fig = _figure(width, height)
    ax = fig.subplots()
    _style(ax, grid_axis="x")
    ax.spines["bottom"].set_visible(False)
    labels = [label for label, _ in rows][::-1]
    values = [value for _, value in rows][::-1]
    span = max((abs(v) for v in values), default=10) or 10
    ax.barh(labels, values, color=[POSITIVE if v >= 0 else NEGATIVE for v in values], height=0.55)
    ax.axvline(0, color=AXIS, linewidth=1)
    pad = span * 0.04
    for position, value in enumerate(values):
        ax.text(
            value + (pad if value >= 0 else -pad),
            position,
            _fmt_pct(value),
            va="center",
            ha="left" if value >= 0 else "right",
            fontsize=8,
            fontweight="bold",
            color=INK,
        )
    limit = span * 1.45
    ax.set_xlim(
        -limit if min(values, default=0) < 0 else -span * 0.2,
        limit if max(values, default=0) > 0 else span * 0.2,
    )
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=8, labelcolor=INK_SECONDARY)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, facecolor=SURFACE)
    return path


def _blocks(monthly: pd.Series) -> pd.Series:
    """Three-month blocks aligned to the last month, so the latest block is always complete."""
    usable = len(monthly) - len(monthly) % BLOCK_MONTHS
    tail = monthly.iloc[-usable:]
    groups = [tail.iloc[i : i + BLOCK_MONTHS] for i in range(0, usable, BLOCK_MONTHS)]
    return pd.Series([g.sum() for g in groups], index=[g.index[-1] for g in groups])


def _block_label(end: pd.Timestamp, months: list[str]) -> str:
    start = end - pd.DateOffset(months=BLOCK_MONTHS - 1)
    return f"{months[start.month - 1]}–{months[end.month - 1]}\n{end:%Y}"


def _monthly_columns(ax, monthly: pd.Series, one_offs: list[str], months, one_off_label) -> None:
    colors = [RECENT if i >= len(monthly) - 12 else EARLIER for i in range(len(monthly))]
    ax.bar(range(len(monthly)), monthly.to_numpy(), color=colors, width=0.72)
    ticks = [i for i in range(len(monthly)) if (len(monthly) - 1 - i) % 3 == 0]
    ax.set_xticks(
        ticks, [f"{months[monthly.index[i].month - 1]}\n{monthly.index[i]:%Y}" for i in ticks]
    )
    stamps = list(monthly.index)
    for month in one_offs:
        stamp = pd.Timestamp(f"{month}-01")
        if stamp in stamps:
            i = stamps.index(stamp)
            ax.annotate(
                one_off_label,
                (i, monthly.iloc[i]),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                fontsize=6.5,
                color=INK_SECONDARY,
            )
    ax.yaxis.set_major_formatter(lambda v, _: _fmt_views(v))


def dynamics(
    series: dict[str, pd.Series],
    one_offs: dict[str, list[str]],
    path: Path,
    *,
    months: list[str],
    one_off_label: str,
    width: float,
    height: float,
) -> Path:
    """One entity: monthly columns. Several: small multiples of 3-month blocks, each on its own
    scale. The last 12 months are dark and earlier months light, so the year-over-year
    comparison is visible without a second colour scale or a second axis.
    """
    keys = list(series)[:MAX_PANELS]
    fig = _figure(width, height)
    if len(keys) == 1:
        ax = fig.subplots()
        _style(ax)
        monthly = series[keys[0]].astype(float)
        _monthly_columns(ax, monthly, one_offs.get(keys[0], []), months, one_off_label)
    else:
        columns = min(len(keys), 3 if len(keys) <= 6 else 4)
        axes = fig.subplots(math.ceil(len(keys) / columns), columns, squeeze=False)
        recent = 12 // BLOCK_MONTHS
        for slot, ax in enumerate(axes.flat):
            if slot >= len(keys):
                ax.set_visible(False)
                continue
            blocks = _blocks(series[keys[slot]].astype(float))
            colors = [RECENT if i >= len(blocks) - recent else EARLIER for i in range(len(blocks))]
            ax.bar(range(len(blocks)), blocks.to_numpy(), color=colors, width=0.7)
            _style(ax)
            ax.set_title(keys[slot], loc="left", fontsize=8, color=INK, fontweight="bold", pad=3)
            ticks = [0, len(blocks) - 1]
            ax.set_xticks(ticks, [_block_label(blocks.index[i], months) for i in ticks])
            ax.yaxis.set_major_locator(MaxNLocator(3))
            ax.yaxis.set_major_formatter(lambda v, _: _fmt_views(v))
            ax.tick_params(labelsize=6.5)
    fig.tight_layout(pad=0.4, h_pad=0.8, w_pad=0.8)
    fig.savefig(path, facecolor=SURFACE)
    return path
