"""Performance trend chart for the Slack message: each timed action in this
run against the same action on recent runs of the same environment.

One small panel per action (they take very different times, so each has its
own scale):
- grey line + dots: the action's time on recent runs (worst attempt per run);
- larger dot: this run, coloured by the same rule as the performance check --
  green normal, amber "slower than usual" (1.5x), red regression (2x) or over
  its budget;
- dashed line: the "usual" time (median of the last 10 runs, the baseline the
  check uses) and a red dashed line at 2x usual, where a regression starts.

History comes from perf_history.jsonl (the metrics branch's runs.jsonl).
Never raises: any problem just means no chart, and the Slack step posts the
summary chart alone.
"""

import json
from datetime import datetime
from pathlib import Path

from common_utilities import perf
from common_utilities.path_settings import PathSettings

# Status palette (reserved for state, never for identity) + chart ink.
GOOD, WARNING, CRITICAL = "#0ca30c", "#fab219", "#d03b3b"
INK, INK_2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

MAX_HISTORY_RUNS = 10


def _history(env: str) -> list[tuple[str, dict]]:
    """[(timestamp, {key: worst elapsed_s})] for this env, oldest first."""
    path = Path(PathSettings.ROOT) / perf.PERF_HISTORY_FILE
    if not path.exists():
        return []
    runs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            run = json.loads(line)
        except ValueError:
            continue
        if run.get("env") != env or not run.get("perf"):
            continue
        worst = {}
        for e in run["perf"]:
            if e.get("key") and e.get("elapsed_s") is not None:
                worst[e["key"]] = max(worst.get(e["key"], 0), float(e["elapsed_s"]))
        if worst:
            runs.append((run.get("timestamp_utc", ""), worst))
    runs.sort(key=lambda r: r[0])
    return runs[-MAX_HISTORY_RUNS:]


def _this_run(env: str) -> dict[str, dict]:
    """{key: {"elapsed", "status", "ratio"}} for this run (worst attempt)."""
    by_key: dict[str, list[dict]] = {}
    for e in perf.read_perf_results(env):
        by_key.setdefault(e.get("key"), []).append(e)
    out = {}
    for key, entries in by_key.items():
        noisy = key in perf.NOISY_KEYS
        if any(e.get("trend_regression") or (not e.get("passed") and not noisy) for e in entries):
            status = CRITICAL
        elif any(e.get("trend_warning") or not e.get("passed") for e in entries):
            status = WARNING
        else:
            status = GOOD
        ratios = [e["trend_ratio"] for e in entries if e.get("trend_ratio") is not None]
        out[key] = {"elapsed": max(e["elapsed_s"] for e in entries), "status": status,
                    "ratio": max(ratios) if ratios else None}
    return out


def _short_date(ts: str) -> str:
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return f"{d.strftime('%b')} {d.day}"
    except ValueError:
        return ""


def render_perf_trend_chart(env: str, env_display: str, out_path) -> Path | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from matplotlib.ticker import FuncFormatter, MaxNLocator
    except ImportError:
        return None
    try:
        history = _history(env)
        current = _this_run(env)
        if not current:
            return None
        baseline = perf.load_baseline(env)
        keys = [k for k in perf.STEP_LABELS if k in current or any(k in h for _, h in history)]

        cols = 3
        rows = (len(keys) + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(13, 3.3 * rows + 1.4), dpi=130, squeeze=False)
        fig.patch.set_facecolor(SURFACE)
        fmt = FuncFormatter(lambda v, _: perf.fmt_duration(v) if v > 0 else "0")

        for ax, key in zip(axes.flat, keys):
            ax.set_facecolor(SURFACE)
            hist_vals = [h.get(key) for _, h in history]
            hist_x = [i for i, v in enumerate(hist_vals) if v is not None]
            hist_y = [v for v in hist_vals if v is not None]
            this = current.get(key)
            x_now = len(history)
            median = baseline.get(key)

            line_x, line_y = list(hist_x), list(hist_y)
            if this:
                line_x.append(x_now)
                line_y.append(this["elapsed"])
            if line_x:
                ax.plot(line_x, line_y, color=MUTED, linewidth=2, zorder=1)
            ax.scatter(hist_x, hist_y, s=36, color=MUTED, edgecolors=SURFACE, linewidths=1.5, zorder=2)
            if this:
                ax.scatter([x_now], [this["elapsed"]], s=150, color=this["status"],
                           edgecolors=SURFACE, linewidths=2, zorder=3)

            top = max(line_y) if line_y else 1
            if median:
                ax.axhline(median, color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)), zorder=0)
                ax.axhline(2 * median, color=CRITICAL, linewidth=1.2, linestyle=(0, (4, 3)), alpha=0.8, zorder=0)
                # Labels sit just outside the plot's right edge so they never
                # collide with the data line.
                edge = ax.get_yaxis_transform()
                ax.text(1.01, median, f"usual\n{perf.fmt_duration(median)}", transform=edge,
                        va="center", ha="left", fontsize=8, color=INK_2, linespacing=1.1)
                ax.text(1.01, 2 * median, f"2x\n{perf.fmt_duration(2 * median)}", transform=edge,
                        va="center", ha="left", fontsize=8, color=INK_2, linespacing=1.1)
                top = max(top, 2 * median)
            ax.set_ylim(0, top * 1.18)
            ax.set_xlim(-0.6, x_now + 0.6)

            # Title: the action; headline value in ink (never the status colour).
            ax.set_title(perf.STEP_LABELS.get(key, key), loc="left", fontsize=11.5,
                         fontweight="bold", color=INK, pad=20)
            if this:
                parts = [f"this run {perf.fmt_duration(this['elapsed'])}"]
                if this.get("ratio"):
                    parts.append(f"{this['ratio']:.1f}x usual")
                tag = {CRITICAL: "  ▲ REGRESSION" if (this.get("ratio") or 0) >= perf.TREND_FAIL_FACTOR
                       else "  ▲ OVER LIMIT", WARNING: "  ● slower than usual", GOOD: ""}[this["status"]]
                sub = " · ".join(parts) + tag
            else:
                sub = "not measured this run"
            if not median:
                n = sum(1 for v in hist_vals if v is not None)
                sub += f"   (building history: {n} earlier run{'s' if n != 1 else ''})"
            ax.text(0, 1.04, sub, transform=ax.transAxes, fontsize=9, color=INK_2, va="bottom")

            ticks = [0] if history else []
            labels = [_short_date(history[0][0])] if history else []
            ticks.append(x_now)
            labels.append("this run")
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, fontsize=8.5, color=MUTED)
            ax.yaxis.set_major_formatter(fmt)
            ax.yaxis.set_major_locator(MaxNLocator(4))
            ax.tick_params(axis="y", labelsize=8.5, colors=MUTED, length=0)
            ax.tick_params(axis="x", length=0)
            ax.grid(axis="y", color=GRID, linewidth=0.8)
            ax.set_axisbelow(True)
            for side in ("top", "right", "left"):
                ax.spines[side].set_visible(False)
            ax.spines["bottom"].set_color(GRID)

        for ax in list(axes.flat)[len(keys):]:
            ax.axis("off")

        fig.suptitle(f"Performance trend — {env_display}: this run vs recent runs",
                     x=0.01, ha="left", fontsize=14, fontweight="bold", color=INK)
        handles = [
            Line2D([0], [0], color=MUTED, linewidth=2, marker="o", markersize=6, label="recent runs"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=GOOD, markersize=10, label="this run: normal"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=WARNING, markersize=10,
                   label="slower than usual (1.5x)"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=CRITICAL, markersize=10,
                   label="regression (2x) / over limit"),
            Line2D([0], [0], color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)), label="usual (median of last 10)"),
            Line2D([0], [0], color=CRITICAL, linewidth=1.2, linestyle=(0, (4, 3)), label="2x usual = regression"),
        ]
        fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, fontsize=9,
                   labelcolor=INK_2, bbox_to_anchor=(0.5, 0.0))
        fig.tight_layout(rect=(0, 0.06, 1, 0.95), h_pad=2.2, w_pad=2.0)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, facecolor=SURFACE)
        plt.close(fig)
        return out_path
    except Exception as e:  # never break the run over a chart
        print(f"[perf-trend] chart not rendered: {e}")
        return None
