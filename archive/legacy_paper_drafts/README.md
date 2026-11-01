# Scripts of the earlier manuscript drafts

These scripts generated the tables and figures of the earlier journal and conference drafts
(`paper/rewrite/`, `paper/conference_main.tex`), which have been removed; the drafts remain in
the git history. They are kept for reference and are not used by the current manuscript.

- `make_tables.py` wrote `paper/rewrite/generated_tables*.tex` for engine v3. The current
  `paper/generated_tables.tex` started from its output and has since been updated from the
  result files (engine v5, precision intervals).
- `generate_results_figure.py` and `generate_ablation_figure.py` drew figures for the drafts.
  The current figures are drawn by `src/eval/generate_pipeline_figure.py` and
  `src/eval/generate_empirical_figure.py`.
