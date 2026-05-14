[IMAGE]

You are tasked with evaluating an edited image **in comparison with the original source image** based on **Visual Quality & Realism**, and assigning a score from 1 to 4, with 1 being the worst and 4 being the best. This dimension focuses on how realistic, artifact-free, and aesthetically appealing the edited image is, while remaining consistent with the source image.

**Inputs Provided:**
- Source Image (before editing)
- Edited Image (after applying the instruction)
- Text Instruction

**Sub-Dimensions to Evaluate:**

- **Plausibility & Physical Consistency:** Check whether the edit aligns with the laws of physics and the scene context. Lighting, shadows, reflections, perspective, size, and interactions with the environment should all appear natural compared to the source image.
- **Artifact-Free Quality:** Look for technical flaws such as blur, distortions, pixel misalignment, unnatural textures, or seams around edited regions. High-quality results should be free from such visible artifacts.
- **Aesthetic Quality:** Evaluate the overall harmony and visual appeal. The image should look natural, balanced, and pleasant. Colors, composition, and atmosphere should enhance the image rather than degrade it.

**Scoring Criteria:**
- **4 (Very Good):** Perfectly realistic, artifact-free, seamless, and aesthetically pleasing.
- **3 (Relatively Good):** Mostly realistic and clean, with only minor flaws that do not significantly distract.
- **2 (Relatively Poor):** Noticeable physical inconsistencies or visible artifacts that make the edit unnatural.
- **1 (Very Poor):** Severe artifacts, incoherent composition, or visually unusable result.

Text instruction – {text_prompt}

Please output only the integer score.
