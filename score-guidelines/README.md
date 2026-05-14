# Score guidelines

Human-rater rubric templates used to **collect** the preference demonstrations RewardHarness learns from. These are NOT what the Sub-Agent reads at inference time — those are the Skills in `src/library/skills/`. These templates were the prompts shown to human annotators when they produced the 100 demonstrations in the calibration set.

| Template | Dimension | Scale |
|---|---|---|
| `template1_instruction_following.md` | Instruction-following & semantic fidelity | 1–4 |
| `template2_visual_quality.md` | Visual quality & realism | 1–4 |

Both templates resolve `{text_prompt}` against the editing instruction at rendering time. Output is a single integer 1–4.

## Why include these?

Reviewers reproducing the paper sometimes want to inspect the rater interface — both for re-collecting their own demonstrations and for understanding what "ground truth" means in our setup. The 1–4 scale is mapped to a 1–5 internal scale in `src/library/skills/` so the Sub-Agent stays consistent with the original demonstrations.
