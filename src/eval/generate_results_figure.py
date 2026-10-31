"""Draw the SmartBugs-curated results figure from the score artifacts.

Panel A: file-level recall with exact 95% Clopper-Pearson intervals for reentrancy, denial of
service and access control, for EVM-Guard v1 (pre-registered), EVM-Guard v3 (final, post hoc),
Slither and Mythril.
Panel B: run outcomes (completed, error, timeout) for each tool on the 143 files.

Writes paper/figures/fig_smartbugs_empirical.png. Every value is read from results/.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS = os.path.join(REPO, "results")
OUT = os.path.join(REPO, "paper/rewrite/figures/fig_smartbugs_empirical.png")
CATEGORIES = [("reentrancy", "Reentrancy (31 files)"), ("denial_of_service", "Denial of service (6 files)"),
              ("access_control", "Access control (18 files)")]
SERIES = [
    ("EVM-Guard v1 (pre-registered)", "external_v1_preregistered/evm_guard_scores.json", "#9DB4D6", ""),
    ("EVM-Guard v3 (final, post hoc)", "external/evm_guard_scores.json", "#1E3A8A", ""),
    ("Slither 0.11.6", "external/slither_scores.json", "#6B7280", ""),
    ("Mythril 0.24.8", "external/mythril_scores.json", "#E5E7EB", "//"),
]
OUTCOME_ROWS = [("EVM-Guard v3", "external/evm_guard_contracts.csv", None),
                ("Slither 0.11.6", "external/slither_scores.json", None),
                ("Mythril 0.24.8", "external/mythril_scores.json", None)]


def load(relative: str) -> dict:
    with open(os.path.join(RESULTS, relative), encoding="utf-8") as handle:
        return json.load(handle)


def panel_recall(ax) -> None:
    width = 0.2
    x = np.arange(len(CATEGORIES))
    for offset, (label, relative, color, hatch) in enumerate(SERIES):
        scores = load(relative)["flagged_any"]
        values, low, high = [], [], []
        for key, _ in CATEGORIES:
            s = scores[key]
            recall = 100 * s["recall"]
            values.append(recall)
            low.append(recall - 100 * s["recall_ci95"][0])
            high.append(100 * s["recall_ci95"][1] - recall)
        positions = x + (offset - 1.5) * width
        ax.bar(positions, values, width, color=color, edgecolor="#111827", linewidth=0.6, hatch=hatch,
               label=label, yerr=[low, high], capsize=2, error_kw={"linewidth": 0.7})
    ax.set_xticks(x)
    ax.set_xticklabels([name for _, name in CATEGORIES], fontsize=8)
    ax.set_ylabel("Recall (%)")
    ax.set_ylim(0, 115)
    ax.set_title("(a) File-level recall with 95% intervals", fontsize=9, loc="left")
    ax.legend(fontsize=7, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.2))
    ax.spines[["top", "right"]].set_visible(False)


def outcome_counts() -> list:
    evm = load("external/evm_guard_scores.json")
    rows = []
    for label, relative, _ in OUTCOME_ROWS:
        if relative.endswith(".csv"):
            completed = evm["files"]
            rows.append((label, completed, 0, 0))
            continue
        status = load(relative)["status"]
        rows.append((label, status.get("ok", 0), status.get("error", 0), status.get("timeout", 0)))
    return rows


def panel_outcomes(ax) -> None:
    rows = outcome_counts()
    names = [row[0] for row in rows]
    y = np.arange(len(rows))[::-1]
    completed = np.array([row[1] for row in rows])
    errors = np.array([row[2] for row in rows])
    timeouts = np.array([row[3] for row in rows])
    ax.barh(y, completed, color="#1E3A8A", label="completed")
    ax.barh(y, errors, left=completed, color="#9CA3AF", label="error")
    ax.barh(y, timeouts, left=completed + errors, color="#FFFFFF", edgecolor="#111827", hatch="//",
            linewidth=0.6, label="timeout")
    for index, row in enumerate(rows):
        ax.text(row[1] + row[2] + row[3] + 2, y[index], f"{row[1]} / {row[2]} / {row[3]}", va="center", fontsize=7)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("Files (of 143)")
    ax.set_xlim(0, 175)
    ax.set_title("(b) Run outcomes on the same 143 files", fontsize=9, loc="left")
    ax.legend(fontsize=7, frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.27))
    ax.spines[["top", "right"]].set_visible(False)


def main() -> None:
    matplotlib.rcParams["font.family"] = "DejaVu Sans"
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.5, 4.2), dpi=300, gridspec_kw={"width_ratios": [1.55, 1]})
    panel_recall(ax_a)
    panel_outcomes(ax_b)
    fig.tight_layout()
    fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
