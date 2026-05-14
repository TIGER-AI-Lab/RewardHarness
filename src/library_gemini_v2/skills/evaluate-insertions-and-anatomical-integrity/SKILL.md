---
description: Guidelines for evaluating inserted humans, animals, or objects, prioritizing
  anatomical correctness over superficial integration.
name: evaluate-insertions-and-anatomical-integrity
type: skill
---

# Evaluate Insertions and Anatomical Integrity

When a prompt requests inserting a person, animal, or object into a scene, you must rigorously check the structural and anatomical integrity of the inserted entity.

1. **Anatomical Check**: Look closely at the inserted subject. Check for deformed faces, missing or extra limbs, mangled hands/paws, or unnatural body proportions. 
2. **Avoid 'Vibe' Bias**: Do not reward an image for 'natural integration' or 'subtle blending' if the inserted entity is anatomically deformed. A seamlessly blended monster is worse than a slightly awkward but anatomically correct insertion.
3. **Physical Plausibility**: Verify correct scale, perspective, shadows, and ground contact. 
4. **Strict Penalty**: Heavily penalize images that introduce severe anatomical anomalies during insertion, even if they technically follow the instruction.
