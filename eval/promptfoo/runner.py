"""Promptfoo offline runner: runs triage pipeline with stub runner (agent-first composition, no LLM)."""

import json
import sys
from pathlib import Path

# Repo root so we can import app
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.contracts.triage import TriageRequest  # noqa: E402
from app.services.triage_service import TriageService  # noqa: E402
from app.orchestrator.triage_orchestrator import TriageOrchestrator  # noqa: E402
from tests.stubs import StubClassificationLLM, StubRemediationLLM  # noqa: E402


def main() -> None:
    if len(sys.argv) < 3:
        line = sys.stdin.readline()
        if not line.strip():
            sys.stderr.write("expected context JSON or single-line request JSON\n")
            sys.exit(1)
        data = json.loads(line)
        request_dict = data.get("request") or (data.get("vars") or {}).get("request") or data
    else:
        context_str = sys.argv[1]
        context = json.loads(context_str)
        request_dict = context.get("vars", {}).get("request") or context.get("request")
        if not request_dict:
            sys.stderr.write("vars.request or request not found in context\n")
            sys.exit(1)

    request = TriageRequest.model_validate(request_dict)
    stub_orchestrator = TriageOrchestrator(
        classification_llm=StubClassificationLLM(),
        remediation_llm=StubRemediationLLM(),
    )
    service = TriageService(runner=stub_orchestrator.run_triage_from_plan)
    response = service.run_triage(request)
    print(json.dumps(response.model_dump(mode="json")))


if __name__ == "__main__":
    main()
