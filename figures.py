"""Draw the charts from the tables estimate.py wrote: the CAPM line, each model's fit, alphas by portfolio and over time."""
import textwrap

import matplotlib
matplotlib.use("Agg")
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import FIGURES, MAIN, MODELS, OUTPUT, PORTFOLIO_FILES
from estimate import COMMON_START, cross_section_fit, excess, time_series

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
COLOURS = dict(zip(MODELS, (BLUE, ORANGE, AQUA)))
DIVERGING = LinearSegmentedColormap.from_list("alpha", [BLUE, "#f4f3f0", ORANGE])
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
                     "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": MUTED,
                     "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True, "legend.frameon": False})
SOURCE = "Source: Kenneth French Data Library, file built from the 202609 CRSP database."
CORNERS = {"SMALL LoBM": ("Small growth", -9), "SMALL HiBM": ("Small value", -9)}  # points to the left, clear of the next panel


def save(fig, name, title, subtitle, caption):
    fig.text(0.015, 0.985, title, fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(0.015, 0.925, subtitle, color=MUTED, va="top")
    fig.text(0.015, 0.012, "\n".join(textwrap.wrap(caption, 138)), color=MUTED, fontsize=9, va="bottom")
    fig.savefig(FIGURES / name, dpi=200, facecolor="white")
    plt.close(fig)


def label_corners(ax, xs, ys, names):
    for x, y, name in zip(xs, ys, names):
        if name in CORNERS:
            text, offset = CORNERS[name]
            ax.annotate(text, (x, y), xytext=(offset, 0), textcoords="offset points", color=INK, fontsize=9, va="center", ha="right")


def capm_panel(ax, start, title):
    r, f, _ = excess(MAIN, "CAPM", start)
    means, betas = r.mean().to_numpy(), time_series(r.to_numpy(), f.to_numpy())[1]
    (intercept, slope), r2 = cross_section_fit(means, betas)
    line = np.array([0.8, 1.7])
    ax.plot(line, line * f["Mkt-RF"].mean(), color=MUTED, lw=1.2, ls="--", label="What the CAPM predicts")
    ax.plot(line, intercept + slope * line, color=ORANGE, lw=2, label="Fitted to the 25 portfolios")
    ax.scatter(betas[:, 0], means, s=45, color=BLUE, edgecolor="white", linewidth=1, zorder=3, label="Portfolio")
    label_corners(ax, betas[:, 0], means, r.columns)
    ax.set_title(f"{title}: R² {r2:.2f}, slope " + f"{slope:+.2f}".replace("-", "−"), loc="left", fontsize=11, color=INK)
    ax.set_xlabel("Market beta")


def capm_line():
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.6), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.975, top=0.8, bottom=0.26, wspace=0.08)
    capm_panel(axes[0], None, "1926-07 to 2026-09")
    capm_panel(axes[1], COMMON_START, "1963-07 to 2026-09")
    axes[0].set_ylabel("Mean excess return, % a month")
    axes[0].legend(loc="upper left", bbox_to_anchor=(0, -0.17), ncol=3, handlelength=1.6, columnspacing=1.4, labelcolor=MUTED, borderaxespad=0)
    save(fig, "capm_line.png", "Market beta says little about mean returns, and since 1963 the slope is negative",
         "Mean excess return of the 25 size and book-to-market portfolios against market beta.",
         "The dashed line runs through the origin with the market's own mean excess return as its slope. " + SOURCE)


def model_fit():
    table = pd.read_csv(OUTPUT / "fitted.csv")
    models = pd.read_csv(OUTPUT / "models.csv")
    models = models[models["sample"] == "Common sample"].set_index("model")
    fig, axes = plt.subplots(1, 3, figsize=(10, 5.2), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.975, top=0.76, bottom=0.2, wspace=0.08)
    ends = [table[["mean", "fitted"]].min().min() - 0.05, table[["mean", "fitted"]].max().max() + 0.05]
    for ax, model in zip(axes, MODELS):
        d = table[table.model == model]
        ax.plot(ends, ends, color=MUTED, lw=1.2, ls="--")
        ax.scatter(d.fitted, d["mean"], s=45, color=COLOURS[model], edgecolor="white", linewidth=1, zorder=3)
        label_corners(ax, d.fitted, d["mean"], d.portfolio)
        ax.set_title(f"{model}: R² {models.r2[model]:.2f}, adjusted {models.adj_r2[model]:.2f}", loc="left", fontsize=11, color=INK)
        ax.set_xlabel("Fitted mean, % a month")
    axes[0].set_ylabel("Actual mean, % a month")
    save(fig, "model_fit.png", "The factors line up mean returns on these portfolios",
         "25 size and book-to-market portfolios, 1963-07 to 2026-09. Intercept and prices of risk are free.",
         "A point on the dashed line is priced exactly. Small growth stays well below the line under every model. " + SOURCE)


def alphas():
    table = pd.read_csv(OUTPUT / "alphas.csv")
    top = table[list(MODELS)].abs().max().max()
    fig, axes = plt.subplots(1, 3, figsize=(10, 5.0))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.74, bottom=0.2, wspace=0.08)
    for ax, model in zip(axes, MODELS):
        grid = table[model].to_numpy().reshape(5, 5)
        ax.imshow(grid, cmap=DIVERGING, vmin=-top, vmax=top)
        ax.grid(False)
        for (row, col), value in np.ndenumerate(grid):
            ax.text(col, row, f"{value:+.2f}".replace("-", "−"), ha="center", va="center", fontsize=9, color=INK)
        ax.set_xticks(range(5), ["Low", "2", "3", "4", "High"])
        ax.set_yticks(range(5), ["Small", "2", "3", "4", "Big"] if model == "CAPM" else [""] * 5)
        ax.tick_params(length=0)
        ax.set_xlabel("Book-to-market")
        ax.set_title(f"{model}: mean |α| {table[model].abs().mean():.3f}", loc="left", fontsize=11, color=INK)
        for spine in ax.spines.values():
            spine.set_visible(False)
    save(fig, "alphas.png", "Value is explained by the factors, and small growth only partly",
         "Alpha of each portfolio, per cent a month, 1963-07 to 2026-09. Blue is below what the model predicts, orange above.",
         "The three-factor model takes out most of the value pattern. The five-factor model shrinks the small growth alpha further but raises some others. " + SOURCE)


def rolling():
    table = pd.read_csv(OUTPUT / "rolling_r2.csv")
    when = pd.PeriodIndex(table.window_end, freq="M").to_timestamp()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.075, right=0.975, top=0.82, bottom=0.2)
    for model in MODELS:
        ax.plot(when, table[model], color=COLOURS[model], lw=1.8, label=model)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Cross-sectional R²")
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.06), ncol=3, handlelength=1.4, columnspacing=1.6, labelcolor=MUTED, borderaxespad=0)
    save(fig, "rolling_r2.png", "The fit comes and goes",
         "R² of mean returns on betas over each ten-year window, by the month it ends. 25 size and book-to-market portfolios.",
         "Betas and means are both re-estimated in each window, so neighbouring points share nine years of data. " + SOURCE)


def by_assets():
    table = pd.read_csv(OUTPUT / "other_assets.csv")
    names = list(PORTFOLIO_FILES)
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.2, right=0.975, top=0.82, bottom=0.2)
    height = 0.24
    for i, model in enumerate(MODELS):
        values = table[table.model == model].set_index("portfolios").mean_abs_alpha[names]
        y = np.arange(len(names)) + (i - 1) * (height + 0.02)
        ax.barh(y, values, height=height, color=COLOURS[model], label=model)
        for v, h in zip(values, y):
            ax.text(v + 0.003, h, f"{v:.3f}", va="center", fontsize=9, color=INK)
    ax.set_yticks(range(len(names)), names)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.07), ncol=3, handlelength=1.4, columnspacing=1.6, labelcolor=MUTED, borderaxespad=0)
    save(fig, "alpha_by_assets.png", "On industries, adding factors makes the alphas larger",
         "Mean absolute alpha, per cent a month, by model and set of test portfolios, 1963-07 to 2026-09.",
         "The first three sets are sorted on the characteristics behind the factors. Industries are not. " + SOURCE)


def main():
    FIGURES.mkdir(exist_ok=True)
    capm_line()
    model_fit()
    alphas()
    rolling()
    by_assets()


if __name__ == "__main__":
    main()
