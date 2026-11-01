"""Draw Figure 2: SmartBugs-curated recall with 95% Clopper-Pearson intervals, and run completion.

Values are those of Table 4 (engine v5; v5 has the same recall as v1-v3 on these categories).
Drawn at its printed size. Writes paper/figures/fig_smartbugs_empirical.png.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "paper", "figures", "fig_smartbugs_empirical.png")
CATEGORIES = ["Reentrancy\n(31)", "Denial of\nservice (6)", "Access\ncontrol (18)"]
# tool: (recall %, lower CI, upper CI, colour, hatch)
RECALL = {
    "EVM-Guard v5": ([93.5, 83.3, 11.1], [78.6, 35.9, 1.4], [99.2, 99.6, 34.7], "#1E3A8A", ""),
    "Slither 0.11.6": ([93.5, 33.3, 44.4], [78.6, 4.3, 21.5], [99.2, 77.7, 69.2], "#475569", "//"),
    "Mythril 0.24.8": ([22.6, 16.7, 72.2], [9.6, 0.4, 46.5], [41.1, 64.1, 90.3], "#94A3B8", ".."),
}
# tool: (completed, errors, timeouts)
COMPLETION = {"EVM-Guard v5": (143, 0, 0), "Slither 0.11.6": (141, 2, 0), "Mythril 0.24.8": (86, 20, 37)}
TOTAL_FILES = 143
BAR_WIDTH = 0.26


def recall_panel(ax) -> None:
    x = np.arange(len(CATEGORIES))
    for index, (tool, (values, low, high, colour, hatch)) in enumerate(RECALL.items()):
        errors = [np.subtract(values, low), np.subtract(high, values)]
        ax.bar(x + (index - 1) * BAR_WIDTH, values, BAR_WIDTH, yerr=errors, capsize=2.5, label=tool, color=colour,
               edgecolor="#0F172A", linewidth=0.6, hatch=hatch, error_kw={"linewidth": 0.8})
    ax.set_ylabel("Recall (%)")
    ax.set_title("(a) Recall with 95% Clopper–Pearson intervals", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORIES)
    ax.set_ylim(0, 105)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False, fontsize=6.5)


def completion_panel(ax) -> None:
    tools = list(COMPLETION)
    y = np.arange(len(tools))[::-1]
    done, errs, outs = (np.array([COMPLETION[t][i] for t in tools]) for i in range(3))
    ax.barh(y, done, 0.5, label="Completed", color="#1E3A8A", edgecolor="#0F172A", linewidth=0.6)
    ax.barh(y, errs, 0.5, left=done, label="Error", color="#64748B", edgecolor="#0F172A", linewidth=0.6, hatch="\\\\")
    ax.barh(y, outs, 0.5, left=done + errs, label="Timeout (60 s)", color="#CBD5E1", edgecolor="#0F172A",
            linewidth=0.6, hatch="xx")
    ax.set_yticks(y)
    ax.set_yticklabels(tools)
    ax.set_xlim(0, TOTAL_FILES)
    ax.set_xlabel(f"Files ({TOTAL_FILES})")
    ax.set_title("(b) Run completion", fontsize=8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3, frameon=False, fontsize=6.5)


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.0, 2.7), dpi=300, gridspec_kw={"width_ratios": [1.15, 1]})
    recall_panel(left)
    completion_panel(right)
    fig.tight_layout()
    fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
