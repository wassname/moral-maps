# WVS static smoke dependency audit

Target: the no-API WVS map smoke run from `scripts/wvs_map.py`.

Provenance: executed from `/workspace/2026/lite/moralmaps` after `uv sync --locked --extra maps --extra api --dev`. The command was `uv run --no-sync python scripts/wvs_map.py --out /tmp/wvs_static_smoke.png --cache /tmp/wvs_static_smoke_cache.json --records /tmp/wvs_static_smoke_records.jsonl`. It exited with status 1 before loading the WVS data or issuing an OpenRouter request.

| stage | expected | observed | expected? | clues | missing metric | consequence |
|---|---|---|---|---|---|---|
| Python imports | WVS script imports its declared runtime dependencies | `ModuleNotFoundError` during `from datasets import load_dataset` | no | complete stderr quote below | no map or request count | paid diagnostic must not start |
| WVS data load | load the public GlobalOpinionQA data | not reached | no | import failed first | item count | cannot form the twelve-item panel |
| API reader | no API call in this smoke | not reached | unclear | process ended at line 40 | request ledger | no spend evidence, as expected |
| artifact render | write temporary PNG | not reached | no | import failed first | PNG dimensions | no visual check |

Complete primary evidence from the failed process:

```text
Traceback (most recent call last):
  File "/workspace/2026/lite/moralmaps/scripts/wvs_map.py", line 40, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
```

The executable source at `scripts/wvs_map.py:40` imports `datasets`, while `pyproject.toml` does not declare it. The locked sync did install the declared `maps` and `api` extras, so the import failure is before any model request or output generation.

## Hypotheses

### H1 [bug | Highly Likely | 90%]

- Mechanism: `datasets` is a runtime dependency of the WVS renderer but is absent from the project dependency declaration.
- Evidence: the exact `ModuleNotFoundError` above names `datasets`; `scripts/wvs_map.py:40` imports it; `pyproject.toml` has no `datasets` dependency.
- Contrary evidence: a different environment might have `datasets` installed globally, but the locked project environment does not.
- Discriminating test: run the same command with a temporary `uv --with datasets` overlay. Success past the import establishes that the missing module, rather than the WVS code, caused this failure.
- Fix/action: use that overlay for the authorized run without changing the pre-existing `uv.lock`, then report the undeclared runtime dependency as a repository defect.
- Interpretability: no model result is affected because the failure occurred before any request.

### H2 [harness | Unlikely | 10%]

- Mechanism: the initial environment rebuild selected an incomplete extras set.
- Evidence: the command included both declared extras, but the error names an undeclared package.
- Contrary evidence: `pyproject.toml` itself omits `datasets`, which directly explains the failure.
- Discriminating test: inspect the temporary-overlay run's import stage. If it still fails elsewhere, this hypothesis gains support.
- Fix/action: retain the full overlay command and its output.
- Interpretability: no model result is affected.

## Decision

Resolve-condition verdict: met only under a temporary dependency overlay. The follow-up command was `uv run --with 'datasets>=4.0,<5' python scripts/wvs_map.py --out /tmp/wvs_static_smoke.png --cache /tmp/wvs_static_smoke_cache.json --records /tmp/wvs_static_smoke_records.jsonl`, and it exited zero. Its complete relevant output was:

```text
2026-09-16 21:05:31.121 | INFO     | __main__:main:250 - 352 WVS questions -> 90 countries on 2 IW axes
2026-09-16 21:05:32.064 | INFO     | __main__:main:390 - wrote /tmp/wvs_static_smoke.png
```

The earliest unsupported link is still the declared-environment to `load_dataset` import. My validity estimate is almost certain that the first failed run says nothing about the WVS reader or model behavior, because it made no request and never built a panel. The overlay smoke establishes the static WVS data and map path; it does not fix the missing declaration. The next action is the low-cost paid diagnostic under the same overlay, with the fsynced ledger, after preserving this dependency limitation in the journal and final handover.

-- PI[gpt-5.6-terra]
