# Extending the System — Cookbook

Use this cookbook to add features without breaking layers or contracts.

**Relevant paths (True Commerce triage):** Contracts in `app/contracts/triage.py`; service in `app/services/triage_service.py`; orchestrator in `app/orchestrator/triage_orchestrator.py`; planner in `app/planner/triage_planner.py`; classifier in `app/classifier/`; remediation in `app/remediation/`; executor in `app/executor/triage_executor.py`.

## Add a new field to TriageRequest or TriageResponse

1. **Contracts:** Add the field to the Pydantic models in `app/contracts/triage.py`. Keep or bump `schema_version` if you change the wire format.
2. **Planner / Executor:** If the field flows through the pipeline, update `TriagePlanner` (e.g. into `NormalizedError`) and/or `TriageExecutor` (e.g. into `TriageResult` or `TriageResponse`).
3. **Tests:** Update `tests/fixtures.py` and any tests that build requests or assert on responses. Add or adjust promptfoo cases in `eval/promptfoo/` if the runner or assertions depend on the new field.

## Add or change a classifier

1. **Interface:** Classifiers implement the protocol in `app/classifier/protocol.py` (`classify(normalized) -> ClassificationResult`).
2. **Implementation:** Add a new implementation (e.g. in `app/classifier/`) or change `app/classifier/rule_based.py` / `app/classifier/ml_stub.py`. For ML, you can swap the stub for a real model behind the same interface.
3. **Orchestrator / Service:** The orchestrator is constructed in `TriageService` (which uses `TriageOrchestrator`). Inject your classifier when building the orchestrator (e.g. in tests or via a factory). Default construction in `app/orchestrator/triage_orchestrator.py` uses `RuleBasedClassifier`; change there or pass it in from `app/services/triage_service.py` if you need a different default.
4. **Tests:** Add pytest for the new classifier; use stubs in `tests/stubs.py` for API/orchestrator tests. Add promptfoo cases if classification/remediation output behavior changes.

## Add a step in the triage pipeline

1. **Contracts:** If the step consumes or produces new data, add or extend models in `app/contracts/triage.py` (e.g. a new result type or fields on `NormalizedError`).
2. **Orchestrator:** In `app/orchestrator/triage_orchestrator.py`, add the step in `run_triage` (e.g. after planner or between classifier and remediation). Keep the orchestrator deterministic; put stochastic work in the agent/LLM layer.
3. **Service:** No change needed if the orchestrator still exposes `run_triage(request) -> TriageResponse`; the API continues to call `TriageService.run_triage`.
4. **Tests:** Add unit tests for the new step and integration tests that run the full pipeline with mocks. Update promptfoo if the final response shape or assertions change.

## Add or change a prompt (Classification or Remediation LLM)

1. **Code:** Update the prompt in `app/classifier/classification_llm.py` or `app/remediation/remediation_llm.py`. Bump the `CLASSIFICATION_PROMPT_VERSION` or `REMEDIATION_PROMPT_VERSION` constant.
2. **decisions.md:** Add an entry describing what changed and why; note promptfoo impact.
3. **promptfoo:** Add or update cases in `eval/promptfoo/cases/` and assertions in `eval/promptfoo/promptfooconfig.yaml`. Run `npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml` offline.
4. **Observability:** Ensure the prompt version is included in spans or trace payloads when you add OTel.

## Add a promptfoo regression case

1. Add a YAML file under `eval/promptfoo/cases/` with `vars` (input to the runner) and optional `assert` overrides.
2. In `eval/promptfoo/promptfooconfig.yaml`, include the case and set assertions (e.g. schema match, `results.length`, fallback flags).
3. Run `npx promptfoo eval -c eval/promptfoo/promptfooconfig.yaml` and commit.
