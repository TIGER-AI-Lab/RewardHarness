---
description: Calibrated scoring guidance for evaluating a single edited image using the full 1-4 scale.
name: score-calibration
type: skill
---

# Score Calibration

## Differential Analysis Requirement
Before finalizing scores, ask:
- What specific elements did this edit get RIGHT?
- What specific elements did this edit get WRONG?
- How severe are the errors (catastrophic vs. minor)?

## Full 1-4 Scale Usage

### Instruction Following Scale
| Score | Meaning |
|-------|----------|
| 4 | All instruction elements correctly executed, no significant errors |
| 3 | Mostly correct, minor errors or slight over-editing that doesn't significantly impact the result |
| 2 | Significant failure in one major element (wrong subject, misspelling, key attribute missing, severe over-editing) |
| 1 | Complete failure — instruction not executed, wrong edit performed, or catastrophic misapplication |

### Visual Quality Scale
| Score | Meaning |
|-------|----------|
| 4 | Photorealistic, seamless integration, artifact-free, consistent lighting |
| 3 | Mostly realistic with minor artifacts, slight lighting mismatch, or small blending issues |
| 2 | Noticeable artifacts, lighting inconsistencies, unnatural blending, or over-processed appearance |
| 1 | Severe distortions, obvious AI artifacts, incoherent result |

## Score Compression Warning
Do NOT compress scores to 2-3 by default. Use 4 when the instruction is fully executed. Use 1 when the instruction completely fails. Spread across the full range.
