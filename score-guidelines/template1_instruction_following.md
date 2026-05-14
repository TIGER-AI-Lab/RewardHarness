[IMAGE]

You are tasked with evaluating an edited image **in comparison with the original source image** based on **Instruction Following & Semantic Fidelity**, and assigning a score from 1 to 4, with 1 being the worst and 4 being the best.

**Inputs Provided:**
- Source Image (before editing)
- Edited Image (after applying the instruction)
- Text Instruction

**Sub-Dimensions to Evaluate:**

- **Semantic Accuracy:** Assess whether the edited content accurately captures the semantics of the instruction. The edited result should precisely match the intended meaning. For example, if the instruction is "replace apples with oranges," the object must clearly be oranges, not other fruits.
- **Completeness of Editing:** Check whether **all parts** of the instruction are fully executed. For multi-step edits (e.g., "replace a red car with a blue bicycle"), both the color change and the object replacement must be done without omissions.
- **Exclusivity of Edit (No Over-Editing):** Ensure that only the requested parts are changed. The rest of the image (as seen in the source) should remain unaltered. For example, if the instruction only involves replacing an object, the background, lighting, and unrelated objects should not be unnecessarily modified.

**Scoring Criteria:**
- **4 (Very Good):** Perfectly accurate, complete, and exclusive execution of the instruction.
- **3 (Relatively Good):** Largely correct, but with minor omissions or slight over-editing.
- **2 (Relatively Poor):** Major misinterpretation, incomplete edits, or noticeable unintended changes.
- **1 (Very Poor):** Instruction ignored or completely wrong execution.

Text instruction – {text_prompt}

Please output only the integer score.
