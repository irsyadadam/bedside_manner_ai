"""Render publication-style SVG figures from the data sidecars produced
by scripts/eval_ablations.py and scripts/sensitivity_sweep.py.

Outputs (manuscript/figures/*.svg):
  fig7_ablation.svg         Tables 4 + 5 — radar + bar panels
  fig9_threshold_sweep.svg  Panel A of Fig 12 (standalone)
  fig11_latency.svg         Per-module wall-clock (renders stub if mock-only)
  fig12_sensitivity.svg     3-panel: threshold + top_k + chunk_size

Style: seaborn 'ticks' base + serif Helvetica-ish + tight layout +
deterministic colorblind-safe palette. SVG (vector) output.
"""
from __future__ import annotations

import argparse
import json
import logging
from math import pi
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

log = logging.getLogger("clinicomm.render_figures")


# --------------------------------------------------------------------------
# Style
# --------------------------------------------------------------------------


def apply_publication_style() -> None:
    sns.set_theme(
        context="paper",
        style="ticks",
        font_scale=1.05,
        rc={
            "figure.dpi": 110,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.transparent": False,
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",  # ships with matplotlib on every box
            "axes.titleweight": "bold",
            "axes.titlesize": 11,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "legend.title_fontsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": ":",
            "lines.linewidth": 1.8,
            "patch.linewidth": 0.4,
            "patch.edgecolor": "white",
        },
    )


# Colorblind-safe; consistent across all figures.
CONDITION_COLORS = {
    "(a) naive":           "#7f7f7f",
    "(b) framework_only":  "#1f77b4",
    "(c) retrieval_only":  "#ff7f0e",
    "(d) full_pipeline":   "#2ca02c",
}


# --------------------------------------------------------------------------
# Fig 7 — Ablation (Tables 4 + 5)
# --------------------------------------------------------------------------


def fig7_ablation(data_path: Path, out_path: Path) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    rows = data.get("per_condition_mean", [])
    if not rows:
        log.warning("fig7: no per_condition_mean rows in %s", data_path)
        return

    fig = plt.figure(figsize=(11.5, 5.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.4], wspace=0.32)

    # ---- Left panel: radar of normalized framework/quality dims ----
    ax_radar = fig.add_subplot(gs[0, 0], projection="polar")
    dims = [
        ("nurse_n",            "NURSE\nelements"),
        ("four_habits_n",      "Four Habits\nelements"),
        ("citations",          "PMIDs\ncited"),
        ("provenance_ratio",   "Provenance\nratio"),
        ("teach_back_present", "Teach-back"),
        ("follow_up_timeframe","Follow-up\ntimeframe"),
    ]
    # Normalize each dimension across the 4 conditions to [0, 1] so the
    # shape comparison is meaningful.
    max_per_dim = {}
    for col, _ in dims:
        vals = []
        for r in rows:
            v = r.get(col, 0)
            if isinstance(v, str) and "/" in v:
                k, n = v.split("/")
                vals.append(int(k) / max(1, int(n)))
            else:
                vals.append(float(v))
        max_per_dim[col] = max(vals) or 1.0

    angles = np.linspace(0, 2 * pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    ax_radar.set_theta_offset(pi / 2)
    ax_radar.set_theta_direction(-1)
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels([label for _, label in dims], fontsize=8.5)
    ax_radar.set_ylim(0, 1.05)
    ax_radar.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax_radar.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], fontsize=7, color="#666")
    ax_radar.grid(alpha=0.35)

    for r in rows:
        cond = r["condition"]
        vals = []
        for col, _ in dims:
            v = r.get(col, 0)
            if isinstance(v, str) and "/" in v:
                k, n = v.split("/")
                v = int(k) / max(1, int(n))
            else:
                v = float(v) / max_per_dim[col]
            vals.append(v)
        vals += vals[:1]
        color = CONDITION_COLORS.get(cond, "#666")
        ax_radar.plot(angles, vals, color=color, linewidth=2.0, label=cond)
        ax_radar.fill(angles, vals, color=color, alpha=0.14)

    ax_radar.set_title("Framework + provenance coverage", pad=14)
    ax_radar.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10),
                     ncols=2, frameon=False)

    # ---- Right panel: grouped bars on quantitative dims ----
    ax_bars = fig.add_subplot(gs[0, 1])
    bar_metrics = [
        ("citations",        "PMIDs cited"),
        ("nurse_n",          "NURSE elements"),
        ("four_habits_n",    "Four Habits"),
        ("provenance_ratio", "Provenance ratio"),
        ("word_count",       "Word count / 100"),
        ("fk_grade",         "Flesch–Kincaid"),
    ]

    def _norm(col, v):
        if col == "word_count":
            return float(v) / 100.0  # rescale to fit common y-axis
        if isinstance(v, str) and "/" in v:
            k, n = v.split("/")
            return int(k) / max(1, int(n))
        return float(v)

    conditions = [r["condition"] for r in rows]
    x = np.arange(len(bar_metrics))
    width = 0.20
    for i, cond in enumerate(conditions):
        r = rows[i]
        vals = [_norm(col, r.get(col, 0)) for col, _ in bar_metrics]
        ax_bars.bar(
            x + (i - 1.5) * width,
            vals,
            width=width,
            label=cond,
            color=CONDITION_COLORS.get(cond, "#666"),
            edgecolor="white",
            linewidth=0.6,
        )

    ax_bars.set_xticks(x)
    ax_bars.set_xticklabels([m[1] for m in bar_metrics],
                             rotation=20, ha="right", fontsize=8.5)
    ax_bars.set_ylabel("Mean across transcripts")
    ax_bars.set_title("Quantitative metrics by condition", pad=10)
    ax_bars.legend(loc="upper left", frameon=False, ncols=1)

    fig.suptitle("Figure 7 — Module-level ablation: naive → framework-only "
                 "→ retrieval-only → full pipeline", fontsize=12, y=1.00)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    log.info("wrote %s", out_path)


# --------------------------------------------------------------------------
# Fig 9 — cluster threshold (Panel A of Fig 12, standalone)
# --------------------------------------------------------------------------


def fig9_threshold(data_path: Path, out_path: Path) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    rows = data.get("panel_a", [])
    if not rows:
        log.warning("fig9: no panel_a in %s", data_path)
        return
    thr = [r["threshold"] for r in rows]
    n_c = [r["n_clusters"] for r in rows]
    n_conv = [r["n_convergent"] for r in rows]
    n_div = [r["n_divergent"] for r in rows]

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(thr, n_c, "o-", color="#222", label="total clusters")
    ax.plot(thr, n_conv, "s-", color="#2ca02c", label="convergent")
    ax.plot(thr, n_div, "^-", color="#d62728", label="divergent (LLM-resolved)")

    ax.axvline(0.75, color="#888", ls=":", lw=1)
    ax.annotate("current\n(0.75)", xy=(0.75, max(n_c)),
                 xytext=(0.755, max(n_c)), fontsize=8, color="#666",
                 ha="left", va="top")
    ax.set_xlabel("Cluster similarity threshold (cosine, BGE assertion text)")
    ax.set_ylabel("Count")
    ax.set_title("Figure 9 — Sensitivity of Module III clustering to "
                  "similarity threshold")
    ax.legend(frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    log.info("wrote %s", out_path)


# --------------------------------------------------------------------------
# Fig 11 — latency
# --------------------------------------------------------------------------


def fig11_latency(traces_dir: Path, out_path: Path) -> None:
    files = sorted(traces_dir.glob("trace_*.json"))
    if not files:
        log.warning("fig11: no trace JSONs in %s", traces_dir)
        return

    rows: list[tuple[str, str, float]] = []
    mode = "?"
    for f in files:
        td = json.loads(f.read_text(encoding="utf-8"))
        mode = td.get("mode", "?")
        tid = td.get("transcript_id", f.stem)
        timings = td.get("module_timings_ms") or {}
        for mod in ("module_1_intake", "module_2_retrieval",
                    "module_3_reasoning", "module_4_response"):
            rows.append((tid, mod.replace("_", " "), float(timings.get(mod, 0.0))))

    if not rows or all(t < 5 for _, _, t in rows):
        # Mock pipeline timings are sub-ms — render a stub.
        fig, ax = plt.subplots(figsize=(7.5, 4.0))
        ax.text(0.5, 0.5,
                 "Figure 11 — per-module wall-clock latency\n\n"
                 "All measurements ≤ 5 ms (mock-LLM pipeline).\n"
                 "This figure populates when the real-LLM pipeline is run\n"
                 "(scripts/run_demo.py --all  with the vLLM server up).",
                 ha="center", va="center", fontsize=10, color="#444",
                 transform=ax.transAxes)
        ax.set_axis_off()
        ax.set_title("Figure 11 — Per-module wall-clock latency  (stub)")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, format="svg")
        plt.close(fig)
        log.info("wrote %s (stub: mock-only)", out_path)
        return

    import pandas as pd
    df = pd.DataFrame(rows, columns=["transcript", "module", "ms"])
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    sns.barplot(
        data=df, x="module", y="ms", hue="transcript",
        palette="deep", ax=ax, edgecolor="white", linewidth=0.6,
    )
    ax.set_ylabel("Wall-clock latency (ms)")
    ax.set_xlabel("")
    ax.set_title(f"Figure 11 — Per-module wall-clock latency  ({mode} LLM)")
    for tick in ax.get_xticklabels():
        tick.set_rotation(15)
        tick.set_ha("right")
    ax.legend(title="transcript", frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    log.info("wrote %s (%s mode)", out_path, mode)


# --------------------------------------------------------------------------
# Fig 12 — 3-panel sensitivity
# --------------------------------------------------------------------------


def fig12_sensitivity(
    threshold_path: Path, topk_path: Path, chunksize_path: Path | None,
    out_path: Path,
) -> None:
    t = json.loads(threshold_path.read_text(encoding="utf-8")) if threshold_path.exists() else {"panel_a": []}
    k = json.loads(topk_path.read_text(encoding="utf-8")) if topk_path.exists() else {"panel_b": []}
    c = (
        json.loads(chunksize_path.read_text(encoding="utf-8"))
        if chunksize_path and chunksize_path.exists()
        else {"panel_c": []}
    )

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    fig.suptitle("Figure 12 — Hyperparameter sensitivity", fontsize=12, y=1.02)

    # ---- Panel A: cluster threshold ----
    rows_a = t.get("panel_a", [])
    if rows_a:
        thr = [r["threshold"] for r in rows_a]
        axes[0].plot(thr, [r["n_clusters"] for r in rows_a],     "o-",
                      color="#222",    label="total")
        axes[0].plot(thr, [r["n_convergent"] for r in rows_a],   "s-",
                      color="#2ca02c", label="convergent")
        axes[0].plot(thr, [r["n_divergent"] for r in rows_a],    "^-",
                      color="#d62728", label="divergent")
        axes[0].axvline(0.75, color="#888", ls=":", lw=1)
        axes[0].set_xlabel("Cluster similarity threshold")
        axes[0].set_ylabel("Count")
        axes[0].set_title("A. Module III clustering")
        axes[0].legend(frameon=False, fontsize=8)
    else:
        axes[0].text(0.5, 0.5, "(no data)", ha="center", va="center",
                      transform=axes[0].transAxes)
        axes[0].set_axis_off()

    # ---- Panel B: top_k ----
    rows_b = k.get("panel_b", [])
    if rows_b:
        tks = [r["top_k"] for r in rows_b]
        axes[1].plot(tks, [r["n_candidate_chunks"]   for r in rows_b], "o-",
                      color="#222", label="candidate chunks")
        axes[1].plot(tks, [r["n_candidate_documents"] for r in rows_b], "s-",
                      color="#1f77b4", label="candidate docs (post-dedup)")
        axes[1].plot(tks, [r["n_returned_documents"] for r in rows_b], "^-",
                      color="#2ca02c", label="returned (post-rerank cap)")
        axes[1].axvline(20, color="#888", ls=":", lw=1)
        axes[1].set_xlabel("top_k chunks per sub-query")
        axes[1].set_ylabel("Count")
        axes[1].set_title("B. Module II retrieval")
        axes[1].legend(frameon=False, fontsize=8)
    else:
        axes[1].text(0.5, 0.5, "(no data)", ha="center", va="center",
                      transform=axes[1].transAxes)
        axes[1].set_axis_off()

    # ---- Panel C: chunk size ----
    rows_c = c.get("panel_c", [])
    if rows_c and any("status" not in r for r in rows_c):
        cs = [r["chunk_size"] for r in rows_c]
        # if rows have other metric fields render them; fallback otherwise
        axes[2].plot(cs, [r.get("retrieval_overlap_pct", 0) for r in rows_c], "o-")
        axes[2].set_xlabel("chunk size (tokens)")
        axes[2].set_ylabel("Retrieval overlap %")
        axes[2].set_title("C. Module II chunk size")
    else:
        axes[2].text(0.5, 0.55,
                      "Panel C — chunk size sweep\n\n"
                      "Requires re-running Phases 4 + 5 per value\n(deferred — opt-in).\n\n"
                      "Run:\n"
                      "  scripts/sensitivity_sweep.py --include-chunk-size",
                      ha="center", va="center", fontsize=9, color="#444",
                      transform=axes[2].transAxes)
        axes[2].set_axis_off()
        axes[2].set_title("C. Module II chunk size  (deferred)")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    log.info("wrote %s", out_path)


# --------------------------------------------------------------------------
# Fig 8 — conflict-resolution rule distribution
# --------------------------------------------------------------------------


def fig8_conflict_resolution(traces_dir: Path, out_path: Path) -> None:
    """Across all saved traces, tally which resolution_rule (recency /
    authority / evidence_strength / coverage / confidence) fired for
    each divergent cluster. Renders a clean horizontal bar chart with
    one bar per rule plus an overflow 'fallback' bucket for clusters
    where the LLM did not name a rule.
    """
    import pandas as pd

    files = sorted(traces_dir.glob("trace_*.json"))
    if not files:
        log.warning("fig8: no trace_*.json in %s", traces_dir)
        return

    counts: dict[str, int] = {
        "recency": 0,
        "authority": 0,
        "evidence_strength": 0,
        "coverage": 0,
        "confidence": 0,
        "fallback / unspecified": 0,
    }
    n_divergent_total = 0
    n_convergent_total = 0
    per_trace: list[tuple[str, str, int]] = []

    for f in files:
        td = json.loads(f.read_text(encoding="utf-8"))
        tid = td.get("transcript_id", f.stem)
        local: dict[str, int] = {k: 0 for k in counts}
        for c in td["structured_context"]["clusters"]:
            if not c.get("convergent", True):
                n_divergent_total += 1
                rule = (c.get("resolution_rule") or "").strip().lower()
                if rule in counts:
                    counts[rule] += 1
                    local[rule] += 1
                else:
                    counts["fallback / unspecified"] += 1
                    local["fallback / unspecified"] += 1
            else:
                n_convergent_total += 1
        for k, v in local.items():
            if v > 0:
                per_trace.append((tid, k, v))

    if n_divergent_total == 0:
        # Nothing to plot — render an informative stub.
        fig, ax = plt.subplots(figsize=(7.5, 4.0))
        ax.text(0.5, 0.5,
                 "Figure 8 — Conflict-resolution rule distribution\n\n"
                 f"No divergent clusters across {len(files)} traces.\n"
                 f"All {n_convergent_total} clusters converged.\n\n"
                 "Populates once real-LLM extraction produces clusters\n"
                 "with disagreeing assertions.",
                 ha="center", va="center", fontsize=10, color="#444",
                 transform=ax.transAxes)
        ax.set_axis_off()
        ax.set_title("Figure 8 — Conflict-resolution rule distribution  (stub)")
        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, format="svg")
        plt.close(fig)
        log.info("wrote %s (stub: no divergent clusters)", out_path)
        return

    # Build the horizontal bar chart.
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    rule_order = [
        "recency", "authority", "evidence_strength",
        "coverage", "confidence", "fallback / unspecified",
    ]
    y = np.arange(len(rule_order))
    vals = [counts[r] for r in rule_order]
    pcts = [(v / n_divergent_total * 100) if n_divergent_total else 0 for v in vals]
    bars = ax.barh(
        y, vals,
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#7f7f7f"],
        edgecolor="white", linewidth=0.6,
    )
    ax.set_yticks(y)
    ax.set_yticklabels([r.replace("_", " ") for r in rule_order])
    ax.invert_yaxis()
    ax.set_xlabel(f"# divergent clusters (n = {n_divergent_total} total)")
    ax.set_title(
        f"Figure 8 — Conflict-resolution rule distribution  "
        f"({len(files)} traces · {n_divergent_total} divergent clusters)"
    )
    # value labels at the end of each bar
    for bar, v, p in zip(bars, vals, pcts):
        if v == 0:
            continue
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                 f"{v}  ({p:.0f}%)", va="center", fontsize=9)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    log.info("wrote %s (%d divergent clusters)", out_path, n_divergent_total)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(prog="scripts/render_figures.py")
    p.add_argument("--data-dir", type=Path, default=Path("manuscript/data"))
    p.add_argument("--traces-dir", type=Path, default=Path("manuscript/traces"))
    p.add_argument("--out-dir", type=Path, default=Path("manuscript/figures"))
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    apply_publication_style()

    fig7_ablation(args.data_dir / "ablation_metrics.json",
                   args.out_dir / "fig7_ablation.svg")
    fig8_conflict_resolution(args.traces_dir,
                              args.out_dir / "fig8_conflict_resolution.svg")
    fig9_threshold(args.data_dir / "sensitivity_threshold.json",
                    args.out_dir / "fig9_threshold_sweep.svg")
    fig11_latency(args.traces_dir, args.out_dir / "fig11_latency.svg")
    fig12_sensitivity(
        args.data_dir / "sensitivity_threshold.json",
        args.data_dir / "sensitivity_topk.json",
        args.data_dir / "sensitivity_chunksize.json",
        args.out_dir / "fig12_sensitivity.svg",
    )


if __name__ == "__main__":
    main()
