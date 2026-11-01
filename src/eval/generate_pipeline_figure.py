"""Draw Figure 1, the EVM-Guard pipeline, at its printed size (text width of the journal page).

Each stage lists what the code does. Items marked "v6" exist only in engine v6; everything else
is shared by v5 and v6. Writes paper/figures/fig_pipeline_architecture.png.
"""
import os

import matplotlib.patches as patches
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "paper", "figures", "fig_pipeline_architecture.png")
WIDTH_IN, HEIGHT_IN = 7.2, 2.25
BOX_W, BOX_H, BOX_Y, HEADER_H, GAP = 1.30, 2.05, 0.10, 0.46, 0.135
TITLE_PT, BODY_PT, TAG_PT = 7.0, 6.1, 5.6
LINE_STEP = 0.145
HEADER_BG, BODY_BG, BORDER, V6_COLOR = "#1E293B", "#F8FAFC", "#475569", "#9A3412"

STAGES = [
    ("Disassembly", ["Strip CBOR trailer", "Disassemble", "Recover selectors"], []),
    ("CFG and abstract\nstack dataflow", ["Basic blocks", "Stack fixpoint;", "  constant jumps", "Gas bounds,", "  provenance"],
     ["Per-context return", "  sites (depth 4)"]),
    ("Reentrancy check", ["CALL, then SSTORE", "  in same function", "Mutex rules", "Skip gas <= 2300"],
     ["Z3 path feasibility;", "  only UNSAT rejects", "Attacker model"]),
    ("Z3 parameters", ["Fixed template;", "  SAT gives witness", "  parameters"],
     ["Witness calldata,", "  value, storage"]),
    ("Sandbox replay", ["py-evm sandbox", "Post-state check,", "  not exit status", "Label confirmed", "  or unconfirmed"],
     ["Re-entering vs", "  passive attacker"]),
]


def draw_line(ax, x: float, y: float, line: str, color: str) -> None:
    """A bullet item, or its indented continuation when the text starts with two spaces."""
    is_continuation = line.startswith("  ")
    text = line.strip() if is_continuation else "\u2022 " + line.strip()
    ax.text(x + (0.15 if is_continuation else 0.07), y, text, ha="left", va="top", fontsize=BODY_PT, color=color,
            zorder=4)


def draw_stage(ax, x: float, title: str, shared: list, v6_only: list) -> None:
    ax.add_patch(patches.FancyBboxPatch((x, BOX_Y), BOX_W, BOX_H, boxstyle="round,pad=0.02,rounding_size=0.06",
                                        linewidth=0.9, edgecolor=BORDER, facecolor=BODY_BG, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((x, BOX_Y + BOX_H - HEADER_H), BOX_W, HEADER_H,
                                        boxstyle="round,pad=0.02,rounding_size=0.06",
                                        linewidth=0.9, edgecolor=BORDER, facecolor=HEADER_BG, zorder=3))
    ax.text(x + BOX_W / 2, BOX_Y + BOX_H - HEADER_H / 2, title, ha="center", va="center", fontsize=TITLE_PT,
            fontweight="bold", color="white", zorder=4, linespacing=1.0)
    y = BOX_Y + BOX_H - HEADER_H - 0.12
    for line in shared:
        draw_line(ax, x, y, line, "#0F172A")
        y -= LINE_STEP
    if v6_only:
        y -= 0.05
        ax.text(x + 0.07, y, "v6 only", ha="left", va="top", fontsize=TAG_PT, fontweight="bold", color=V6_COLOR,
                zorder=4)
        y -= 0.15
        for line in v6_only:
            draw_line(ax, x, y, line, V6_COLOR)
            y -= LINE_STEP


def main() -> None:
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(WIDTH_IN, HEIGHT_IN), dpi=300)
    ax.set_xlim(0, WIDTH_IN)
    ax.set_ylim(0, HEIGHT_IN)
    ax.axis("off")
    left = (WIDTH_IN - (len(STAGES) * BOX_W + (len(STAGES) - 1) * GAP)) / 2
    for index, (title, shared, v6_only) in enumerate(STAGES):
        x = left + index * (BOX_W + GAP)
        draw_stage(ax, x, title, shared, v6_only)
        if index < len(STAGES) - 1:
            mid = BOX_Y + BOX_H / 2
            ax.add_patch(patches.FancyArrowPatch((x + BOX_W + 0.02, mid), (x + BOX_W + GAP - 0.02, mid),
                                                 arrowstyle="-|>,head_length=3,head_width=2", color=BORDER,
                                                 linewidth=1.0, zorder=5))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
