# Score guidelines

The scoring rubric templates that `src/sub_agent.py` loads at inference time. Each `SubAgent.evaluate(...)` call reads both files, substitutes `{text_prompt}` with the editing instruction, and includes them in the Sub-Agent's scoring system prompt so every preference judgment scores each image on both dimensions independently.

| Template | Dimension | Scale | Loaded by |
|---|---|---|---|
| `template1_instruction_following.md` | Instruction-following & semantic fidelity | 1–4 (integer) | `src/sub_agent.py` (`SCORE_TEMPLATES_DIR/template1_*`) |
| `template2_visual_quality.md` | Visual quality & realism | 1–4 (integer) | `src/sub_agent.py` (`SCORE_TEMPLATES_DIR/template2_*`) |

The 1–4 scale is the **internal scale used end-to-end** — by human annotators when they produced the 100 calibration demonstrations, by the Sub-Agent at inference time, and by `evaluate_prediction` in `src/evaluator.py` when comparing against ground truth. There is no rescaling step.

## Overriding the templates path

`SCORE_TEMPLATES_DIR` defaults to `<repo>/score-guidelines/`. Set `REWARDHARNESS_TEMPLATES_DIR=/abs/path/to/templates` to point at a different directory — useful for wheel/sdist installs that move the templates out of the source tree, or for ablation studies that swap in alternative rubrics. See `.env.example`.

## Why include these?

The templates are part of the Sub-Agent's runtime contract — anyone reproducing or extending the pipeline needs to see exactly what scoring rubric the model is asked to apply. They're also the rater interface that produced the calibration set, so reviewers can verify what "ground truth" means in the paper's setup.
