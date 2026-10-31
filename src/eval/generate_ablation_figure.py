"""Draw the reentrancy ablation as a bar chart of false positives per configuration.

Every value is read from results/ablation/ablation_summary.json. Writes
paper/rewrite/figures/fig_ablation.png.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUMMARY = os.path.join(REPO, "results/ablation/ablation_summary.json")
OUT = os.path.join(REPO, "paper/rewrite/figures/fig_ablation.png")
LABELS = {
    "full": "Final engine",
    "no_stipend_exclusion": "No stipend exclusion",
    "constant_gas_only": "Constant-gas rule only",
    "no_slot_mutex": "No slot-mutex rule",
    "no_mutex": "No mutex rules",
    "mutex_by_reachability": "Reachability, not dominance",
    "no_push0_decode": "No PUSH0 decoding",
    "no_cbor_strip": "No CBOR stripping",
    "pre_fix_v2": "Pre-fix engine (v2)",
}


def main() -> None:
    with open(SUMMARY, encoding="utf-8") as handle:
        summary = json.load(handle)
    names = list(LABELS)
    fp = [summary[name]["reentrancy"]["fp"] for name in names]
    tp = [summary[name]["reentrancy"]["tp"] for name in names]
    fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=300)
    colors = ["#1E3A8A" if name == "full" else "#9CA3AF" for name in names]
    bars = ax.barh(range(len(names)), fp, color=colors, edgecolor="#111827", linewidth=0.5)
    for index, bar in enumerate(bars):
        ax.text(bar.get_width() + 0.4, index, f"{fp[index]} FP (TP {tp[index]})", va="center", fontsize=7)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([LABELS[name] for name in names], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel("False positives on SmartBugs-curated reentrancy (143 files)", fontsize=8)
    ax.set_xlim(0, max(fp) + 12)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
