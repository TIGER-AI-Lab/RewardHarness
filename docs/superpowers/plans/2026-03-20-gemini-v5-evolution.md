# gemini_v5 Evolution Run — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Launch a 150-iteration evolution run (gemini_v5) with separate skill/tool rollback, `>=` keep condition, train=60/val=40 split, and 22 vLLM endpoints.

**Architecture:** Two-phase evolution (skills then tools evaluated independently), `>=` threshold to encourage exploration, all iterations checkpointed. Library grows instead of stagnating. Best checkpoint picked post-hoc.

**Tech Stack:** Python, vLLM (Qwen2.5-VL-7B-Instruct), Gemini 3.1 Pro Preview, Slurm

---

## Already Done (pre-plan)

- [x] `pipeline.py` — separate rollback (Phase A: skills, Phase B: tools), `>=` condition, resume bug fix, prominent train_acc logging
- [x] `configs/default.yaml` — train_n=60, val_n=40
- [x] `configs/endpoints.txt` — removed dead node-X/node-X, added node-X×4 + node-X×4 (22 total)

## Chunk 1: Fix Tests & Verify Code

### Task 1: Update test_pipeline.py for new behavior

**Files:**
- Modify: `tests/test_pipeline.py`

The `>=` change and separate rollback break existing test expectations.

- [ ] **Step 1: Fix `test_rollback_on_val_regression`**

With `>=`, equal val_acc now KEEPs (not rollbacks). The test mock returns constant predictions, so val_acc is identical between iter 0 and iter 1. Update assertions:

```python
# OLD: assert log[1]["action"] == "rollback"
# NEW: with >=, equal val_acc is a keep
assert log[1]["action"] == "keep"  # >= means tie keeps
assert log[1]["skill_action"] == "keep"
# The skill SHOULD now be in the registry since we kept it
assert "bad-skill" in pipeline.library.registry  # was: not in
```

Rename test from `test_rollback_on_val_regression` to `test_keep_on_equal_val_acc`.

- [ ] **Step 2: Add a proper rollback test**

Add `test_rollback_on_actual_regression` that forces val_acc to DROP:

```python
@patch("src.pipeline.EndpointPool")
@patch("src.router.call_gemini")
@patch("src.chain_analyzer.call_gemini")
@patch("src.sub_agent.OpenAI")
def test_rollback_on_actual_regression(self, MockSubVLLM, mock_chain_gemini,
                                        mock_router_gemini, MockPool,
                                        config, tmp_path, mock_train_examples, mock_val_examples):
    """Val accuracy decrease triggers rollback even with >= condition."""
    mock_pool = MagicMock()
    mock_pool.next.return_value = "http://localhost:8000/v1"
    MockPool.return_value = mock_pool

    lib_dir = tmp_path / "library"
    lib_dir.mkdir()
    (lib_dir / "skills").mkdir()
    (lib_dir / "tools").mkdir()
    (lib_dir / "registry.json").write_text("{}")

    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # Iter 0 (baseline): predict "A" → all val examples have gt="A" → 100% acc
    answer_a = json.dumps({
        "preference": "A", "score_A_instruction": 3, "score_A_quality": 3,
        "score_B_instruction": 2, "score_B_quality": 2, "reasoning": "A"
    })
    mock_vllm = MagicMock()
    call_count = [0]

    def make_response(pred_str):
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = f'<answer>{pred_str}</answer>'
        return resp

    # Track calls: iter 0 returns "A" (correct), iter 1 returns "B" (wrong for val)
    def dynamic_create(**kwargs):
        call_count[0] += 1
        # iter 0: train(4) + val(2) = 6 calls → all "A"
        # iter 1: train(4) = calls 7-10 → "A", val_skills(2) = calls 11-12 → "B" (regression)
        if call_count[0] > 10:
            return make_response(json.dumps({
                "preference": "B", "score_A_instruction": 2, "score_A_quality": 2,
                "score_B_instruction": 3, "score_B_quality": 3, "reasoning": "B"
            }))
        return make_response(answer_a)

    mock_vllm.chat.completions.create.side_effect = dynamic_create
    MockSubVLLM.return_value = mock_vllm

    mock_router_gemini.return_value = json.dumps({"skills": [], "tools": []})
    signals = json.dumps({
        "skill_updates": [{"action": "add", "name": "bad-skill", "description": "Bad", "content_md": "## Bad"}],
        "tool_updates": [],
        "analysis_summary": "test"
    })
    mock_chain_gemini.return_value = signals

    pipeline = SelfEvolutionPipeline(config, library_dir=str(lib_dir))
    pipeline.results_dir = str(results_dir)
    pipeline.checkpoint_dir = str(results_dir / "checkpoints")

    log = pipeline.evolve(n_iterations=2, train_split=mock_train_examples, val_split=mock_val_examples)

    # Iter 1 should rollback because val predictions switched to "B" (all wrong)
    assert log[1]["skill_action"] == "rollback"
    assert "bad-skill" not in pipeline.library.registry
```

- [ ] **Step 3: Update `test_two_iteration_run` for new log fields**

The log entries now have new fields. Add assertions:

```python
assert "skill_action" in log[1]
assert "tool_action" in log[1]
assert "best_val_acc" in log[1]
assert "val_acc_after_skills" in log[1]
```

- [ ] **Step 4: Run all tests**

Run: `cd /path/to/your/reward-harness-checkout && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 5: Commit test fixes**

```bash
git add tests/test_pipeline.py
git commit -m "fix: update pipeline tests for separate rollback and >= condition"
```

### Task 2: Verify vLLM endpoints are healthy

**Files:** None (infrastructure only)

- [ ] **Step 1: Health check all 22 endpoints**

```bash
for ep in localhost:8000 localhost:8001 localhost:8002 localhost:8003 \
          node-X:8000 node-X:8001 node-X:8002 node-X:8003 \
          node-X:8000 node-X:8001 node-X:8002 node-X:8003 \
          node-X:8000 node-X:8000 \
          node-X:8000 node-X:8001 node-X:8002 node-X:8003 \
          node-X:8000 node-X:8001 node-X:8002 node-X:8003; do
  status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://$ep/v1/models)
  echo "$ep: $status"
done
```

Expected: All 22 return `200`. If node-X/node-X aren't ready yet, wait and retry.

- [ ] **Step 2: If any endpoints are down, restart them**

Use `srun --overlap` with the appropriate job ID to start vLLM on the failing GPU.

## Chunk 2: Launch gemini_v5 & Monitor

### Task 3: Wait for gemini_v4 to finish (or kill it)

- [ ] **Step 1: Check gemini_v4 status**

```bash
python3 -c "import json; data=json.load(open('results/gemini_v4/evolution_log.json')); print(f'Completed: {len(data)}/150')"
ps -p 1440912 -o pid,stat,etime --no-headers 2>/dev/null || echo 'DONE'
```

If completed (150/150) or dead: proceed. If still running with <5 iters left: wait. If >5 iters: kill it (the run is known to be plateaued, no value continuing).

### Task 4: Launch gemini_v5

**Files:** None (runtime only)

- [ ] **Step 1: Create library and results directories**

```bash
mkdir -p src/library_gemini_v5/skills src/library_gemini_v5/tools
echo '{}' > src/library_gemini_v5/registry.json
mkdir -p results/gemini_v5
```

- [ ] **Step 2: Set environment and launch**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google-credentials.json"
export GEMINI_PROJECT="your-vertexai-project-id"
export GEMINI_LOCATION="global"

nohup python scripts/run_evolution.py \
  --config configs/default.yaml \
  --library-dir src/library_gemini_v5 \
  --results-dir results/gemini_v5 \
  --max-iters 150 \
  > results/gemini_v5/evolution_run.log 2>&1 &
echo "PID=$!"
```

- [ ] **Step 3: Verify process started and iter 0 begins**

```bash
sleep 10 && tail -20 results/gemini_v5/evolution_run.log
```

Expected: "Iteration 0/149" and "Running baseline (empty library)..."

### Task 5: Set up cron monitoring

- [ ] **Step 1: Create cron job (every 8 minutes)**

Monitor script checks:
1. `evolution_log.json` — latest iter, val_acc, skill_action, tool_action, n_skills, n_tools
2. `evolution_run.log` — parse warnings, 429 errors
3. Process alive check
4. **RED FLAG alerts** at:
   - 10+ consecutive ALL-rollback iterations (both skills AND tools rolled back)
   - val_acc below 0.15
   - n_tools stuck at 0 after iter 10
   - Process crash

### Task 6: Post-completion analysis

After 150 iterations complete:

- [ ] **Step 1: Find best checkpoint by val_acc**

```bash
python3 -c "
import json
data = json.load(open('results/gemini_v5/evolution_log.json'))
best = max(data, key=lambda x: x.get('best_val_acc', x.get('val_acc', 0)))
print(f'Best iter: {best[\"iteration\"]}, val_acc: {best.get(\"best_val_acc\", best[\"val_acc\"]):.4f}')
print(f'Skills: {best[\"n_skills\"]}, Tools: {best[\"n_tools\"]}')

# Show keep history
keeps = [d for d in data[1:] if d['action'] == 'keep']
skill_keeps = [d for d in data[1:] if d.get('skill_action') == 'keep']
tool_keeps = [d for d in data[1:] if d.get('tool_action') == 'keep']
print(f'Total keeps: {len(keeps)} (skill_keeps: {len(skill_keeps)}, tool_keeps: {len(tool_keeps)})')
"
```

- [ ] **Step 2: Cancel cron monitoring job**

- [ ] **Step 3: Copy best checkpoint library for benchmark evaluation**

```bash
cp -r results/gemini_v5/checkpoints/iter_BEST/skills/ src/library_gemini_v5_best/skills/
cp -r results/gemini_v5/checkpoints/iter_BEST/tools/ src/library_gemini_v5_best/tools/
cp results/gemini_v5/checkpoints/iter_BEST/registry.json src/library_gemini_v5_best/registry.json
```
