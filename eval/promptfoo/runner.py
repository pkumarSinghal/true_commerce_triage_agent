"""Promptfoo offline runner: runs triage pipeline with stub LLMs, no network. Reads context (vars) from promptfoo, outputs TriageResponse JSON."""

import json
import sys
from pathlib import Path

# Repo root so we can import app
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.contracts.triage import TriageRequest, TriageResponse
from app.orchestrator.triage_orchestrator import TriageOrchestrator
from tests.stubs import StubClassificationLLM, StubRemediationLLM


def main() -> None:
    if len(sys.argv) < 3:
        # Fallback: read single JSON line from stdin (for manual testing)
        line = sys.stdin.readline()
        if not line.strip():
            sys.stderr.write("expected context JSON or single-line request JSON\n")
            sys.exit(1)
        data = json.loads(line)
        if "request" in data:
            request_dict = data["request"]
        else:
            request_dict = data
    else:
        context_str = sys.argv[1]
        context = json.loads(context_str)
        request_dict = context.get("vars", {}).get("request") or context.get("request")
        if not request_dict:
            sys.stderr.write("vars.request or request not found in context\n")
            sys.exit(1)

    request = TriageRequest.model_validate(request_dict)
    orchestrator = TriageOrchestrator(
        classification_llm=StubClassificationLLM(),
        remediation_llm=StubRemediationLLM(),
    )
    response = orchestrator.run_triage(request)
    out = response.model_dump(mode="json")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
