import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Professional academic typography and styling
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9.0

# 14.5 x 3.3 inches at 300 DPI - formal publication dimensions
fig, ax = plt.subplots(figsize=(14.5, 3.3), dpi=300)
ax.set_xlim(0, 14.5)
ax.set_ylim(0, 3.3)
ax.axis('off')

# Formal academic styling: muted slate and steel-blue palette
# No rainbow or garish colors; elegant corporate/academic IEEE styling
stages = [
    {
        "num": "Stage 1",
        "title": "Disassembly &\nPreprocessing",
        "subtitle": "• Strip CBOR metadata trailer\n• Linear-sweep pyevmasm\n• Recover 4-byte dispatchers",
        "header_bg": "#1E293B",  # Deep Slate Navy
        "box_bg": "#F8FAFC",     # Crisp White-Slate
        "border": "#475569",     # Slate Gray
        "x": 0.3
    },
    {
        "num": "Stage 2",
        "title": "CFG & Abstract\nStack Dataflow",
        "subtitle": "• Basic-block leader partition\n• Monotone stack fixpoint\n• Provenance & value bounds\n• Natural loop extraction",
        "header_bg": "#334155",  # Muted Slate
        "box_bg": "#F8FAFC",
        "border": "#475569",
        "x": 3.2
    },
    {
        "num": "Stage 3",
        "title": "Path-Sensitive\nHazard Checking",
        "subtitle": "• Dominance tree analysis\n• External call reachability\n• Mutex lock recognition\n• Gas bound <= 2300 prune",
        "header_bg": "#1E293B",
        "box_bg": "#F8FAFC",
        "border": "#475569",
        "x": 6.1
    },
    {
        "num": "Stage 4",
        "title": "SMT Constraint\nWitness Synthesis",
        "subtitle": "• Z3 bit-vector templates\n• Z3 parameter solve\n• Target calldata synthesis\n• Concrete witness vector",
        "header_bg": "#334155",
        "box_bg": "#F8FAFC",
        "border": "#475569",
        "x": 9.0
    },
    {
        "num": "Stage 5",
        "title": "Dual-State Dynamic\nSandbox Replay",
        "subtitle": "• Isolated py-evm harness\n• Synthesized attack execution\n• State post-condition check\n• Post-state criterion, not exit status",
        "header_bg": "#0F172A",  # Darkest Navy
        "box_bg": "#F8FAFC",
        "border": "#334155",
        "x": 11.9
    }
]

box_width = 2.38
box_height = 2.65
box_y = 0.35
header_height = 0.68

for s in stages:
    # Outer box container
    rect = patches.FancyBboxPatch(
        (s["x"], box_y), box_width, box_height,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        linewidth=1.4, edgecolor=s["border"], facecolor=s["box_bg"], zorder=2
    )
    ax.add_patch(rect)
    
    # Header box banner
    header = patches.FancyBboxPatch(
        (s["x"], box_y + box_height - header_height), box_width, header_height,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        linewidth=1.4, edgecolor=s["border"], facecolor=s["header_bg"], zorder=3
    )
    ax.add_patch(header)
    
    # Fill the lower corners of header banner to square with the body
    fill_rect = patches.Rectangle(
        (s["x"] + 0.03, box_y + box_height - header_height), box_width - 0.06, 0.15,
        linewidth=0, facecolor=s["header_bg"], zorder=3
    )
    ax.add_patch(fill_rect)

    # Stage Badge & Title in Header
    ax.text(s["x"] + box_width/2.0, box_y + box_height - 0.22, s["num"].upper(),
            ha='center', va='center', fontsize=8.0, fontweight='bold', color='#94A3B8', zorder=4)
    ax.text(s["x"] + box_width/2.0, box_y + box_height - 0.47, s["title"],
            ha='center', va='center', fontsize=9.2, fontweight='bold', color='#FFFFFF', zorder=4,
            linespacing=0.95)

    # Subtitle / bullet items in body
    ax.text(s["x"] + 0.14, box_y + 0.95, s["subtitle"],
            ha='left', va='center', fontsize=8.2, color='#1E293B', zorder=4,
            linespacing=1.35)

# High-precision arrows connecting stages
for i in range(len(stages) - 1):
    start_x = stages[i]["x"] + box_width + 0.03
    end_x = stages[i+1]["x"] - 0.03
    mid_y = box_y + box_height / 2.0
    
    arrow = patches.FancyArrowPatch(
        (start_x, mid_y), (end_x, mid_y),
        arrowstyle='-|>,head_length=5,head_width=3.5',
        color='#475569', linewidth=1.8, zorder=5
    )
    ax.add_patch(arrow)

plt.tight_layout()
plt.savefig("paper/rewrite/figures/fig_pipeline_architecture.png", dpi=300, bbox_inches='tight', facecolor='white')
print("Pipeline figure updated with formal academic palette.")
