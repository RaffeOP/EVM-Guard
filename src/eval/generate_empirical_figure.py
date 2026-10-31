import matplotlib.pyplot as plt
import numpy as np

# Professional academic font styling
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9.0

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.0), dpi=300)

# ----------------- PANEL A: Recall Comparison -----------------
categories = ['Reentrancy\n(31 files)', 'Denial of Service\n(6 files)', 'Access Control\n(18 files)']
x = np.arange(len(categories))
width = 0.25

# Recall data
rec_eg = [93.5, 83.3, 11.1]
rec_sl = [93.5, 33.3, 44.4]
rec_my = [22.6, 16.7, 72.2]

# Clopper-Pearson 95% CIs for recall
err_eg_low = [93.5 - 78.6, 83.3 - 35.9, 11.1 - 1.4]
err_eg_high = [99.2 - 93.5, 99.6 - 83.3, 34.7 - 11.1]
err_sl_low = [93.5 - 78.6, 33.3 - 4.3, 44.4 - 21.5]
err_sl_high = [99.2 - 93.5, 77.7 - 33.3, 69.2 - 44.4]
err_my_low = [22.6 - 9.6, 16.7 - 0.4, 72.2 - 46.5]
err_my_high = [41.1 - 22.6, 64.1 - 16.7, 90.3 - 72.2]

# Formal academic monochrome/steel palette:
# EVM-Guard: Deep Navy Slate (#1E3A8A)
# Slither: Charcoal Slate (#475569)
# Mythril: Cool Neutral Gray (#94A3B8)
rects1 = ax1.bar(x - width, rec_eg, width, yerr=[err_eg_low, err_eg_high], capsize=4,
                 label='EVM-Guard v2 (Ours)', color='#1E3A8A', edgecolor='#0F172A', linewidth=1.2, ecolor='#0F172A')
rects2 = ax1.bar(x, rec_sl, width, yerr=[err_sl_low, err_sl_high], capsize=4,
                 label='Slither 0.11.6', color='#475569', edgecolor='#1E293B', linewidth=1.2, ecolor='#1E293B', hatch='//')
rects3 = ax1.bar(x + width, rec_my, width, yerr=[err_my_low, err_my_high], capsize=4,
                 label='Mythril 0.24.8', color='#94A3B8', edgecolor='#334155', linewidth=1.2, ecolor='#334155', hatch='..')

ax1.set_ylabel('Detection Recall (%)', fontweight='bold', color='#0F172A')
ax1.set_title('(a) Detection Recall with 95% Clopper-Pearson CIs', fontweight='bold', pad=18, color='#0F172A')
ax1.set_xticks(x)
ax1.set_xticklabels(categories, fontweight='medium', color='#1E293B')
ax1.set_ylim(0, 115)
ax1.grid(axis='y', linestyle='--', alpha=0.35, color='#94A3B8')
ax1.legend(frameon=True, facecolor='#F8FAFC', edgecolor='#CBD5E1', framealpha=0.95, loc='upper right')

# Add recall numerical annotations
for rects in [rects1, rects2, rects3]:
    for rect in rects:
        height = rect.get_height()
        ax1.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 14),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=7.5, color='#0F172A', fontweight='semibold')

# ----------------- PANEL B: Tool Completion & Robustness -----------------
tools = ['EVM-Guard v2', 'EVM-Guard v1', 'Slither', 'Mythril']
completed = np.array([143, 143, 141, 86])
timeouts = np.array([0, 0, 0, 37])
errors = np.array([0, 0, 2, 20])

y = np.arange(len(tools))
bar_height = 0.50

# Formal stacked bar chart in academic tones:
# Completed: Deep Navy (#1E3A8A)
# Errors: Muted Slate (#64748B)
# Timeouts: Neutral Tint (#CBD5E1)
p1 = ax2.barh(y, completed, bar_height, label='Completed Analysis (Success)', color='#1E3A8A', edgecolor='#0F172A', linewidth=1.1)
p2 = ax2.barh(y, errors, bar_height, left=completed, label='Tool Execution Errors', color='#64748B', edgecolor='#1E293B', linewidth=1.1, hatch='\\\\')
p3 = ax2.barh(y, timeouts, bar_height, left=completed + errors, label='Execution Timeouts (>60s)', color='#CBD5E1', edgecolor='#334155', linewidth=1.1, hatch='xx')

ax2.set_xlabel('Number of Contracts Processed (Total = 143)', fontweight='bold', color='#0F172A')
ax2.set_title('(b) Execution Reliability and Completion Rates', fontweight='bold', pad=18, color='#0F172A')
ax2.set_yticks(y)
ax2.set_yticklabels(tools, fontweight='medium', color='#1E293B')
ax2.set_xlim(0, 160)
ax2.grid(axis='x', linestyle='--', alpha=0.35, color='#94A3B8')
ax2.legend(frameon=True, facecolor='#F8FAFC', edgecolor='#CBD5E1', framealpha=0.95, loc='lower right')

# Add total count annotations
for i in range(len(tools)):
    total = completed[i] + errors[i] + timeouts[i]
    detail = []
    if timeouts[i] > 0:
        detail.append(f"{timeouts[i]} timeouts")
    if errors[i] > 0:
        detail.append(f"{errors[i]} errors")
    txt = f"{completed[i]}/143 (100%)" if completed[i] == 143 else f"{completed[i]}/143 ({', '.join(detail)})"
    ax2.annotate(txt,
                xy=(145, y[i]),
                xytext=(5, 0),
                textcoords="offset points",
                ha='left', va='center', fontsize=7.5, fontweight='semibold', color='#0F172A')

plt.tight_layout()
plt.savefig("paper/figures/fig_smartbugs_empirical.png", dpi=300, bbox_inches='tight', facecolor='white')
print("Empirical figure updated with formal academic palette.")
