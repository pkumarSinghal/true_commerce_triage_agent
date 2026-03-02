# Problem Breakdowns

Before implementing non-trivial changes, add a **Problem Breakdown** here. This keeps the reference repo predictable and teaches Cursor agents to think before coding.

## Naming Convention

- **Format:** `NNNN-short-kebab-name.md` (e.g. `0001-example-anomaly-resolution.md`, `0002-add-escalation-tool.md`).
- **NNNN:** Zero-padded number; increment for each new breakdown. Use the next available number.
- **short-kebab-name:** Brief description of the problem or feature.

## How to Add a New Breakdown

1. Copy `docs/PROBLEM_BREAKDOWN_TEMPLATE.md`.
2. Save as `docs/breakdowns/NNNN-your-feature.md` with the next number.
3. Fill every section (objective, events, state, policies, agent, tools, failure modes, observability, evaluation).
4. Implement only after the breakdown is in place; reference it in PRs and commits.

## Index

- `0001-example-anomaly-resolution.md` — Maps to the MVP demo: AnomalyDetected event, case lifecycle, agent plan with ≥3 steps (check_status, notify_user, open_ticket), fallback, DLQ/replay.
