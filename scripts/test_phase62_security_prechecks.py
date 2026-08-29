from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.main import app

ADMIN_USER = "00000000-0000-0000-0000-000000002706"
EMPLOYEE_USER = "00000000-0000-0000-0000-000000002701"


def static_python_findings() -> list[str]:
    findings: list[str] = []
    for base in (ROOT / "apps" / "api" / "app", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                    findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:builtin_{node.func.id}")
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if (node.func.value.id, node.func.attr) in {("pickle", "loads"), ("yaml", "load")}:
                        findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:unsafe_deserialization")
                if any(keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True for keyword in node.keywords):
                    findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:subprocess_shell_true")
    return findings


def test_targeted_static_precheck() -> None:
    assert static_python_findings() == []


def test_container_runtime_is_non_root() -> None:
    api = (ROOT / "apps" / "api" / "Dockerfile").read_text(encoding="utf-8")
    web = (ROOT / "apps" / "web" / "Dockerfile").read_text(encoding="utf-8")
    assert "USER proofbase" in api
    assert "USER node" in web
    assert api.rfind("USER proofbase") < api.rfind("CMD ")
    assert web.rfind("USER node") < web.rfind("CMD ")


def test_dependency_inventory_is_reproducible_or_declared() -> None:
    lock = ROOT / "apps" / "web" / "package-lock.json"
    assert lock.is_file() and json.loads(lock.read_text(encoding="utf-8"))["lockfileVersion"] >= 3
    requirements = [line.strip() for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    unpinned = [line for line in requirements if "==" not in line]
    assert unpinned, "Update the Phase 62 dependency finding when Python dependencies become fully pinned."


def test_local_dast_headers_and_negative_paths() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    expected_headers = {
        "cache-control": "no-store",
        "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
        "permissions-policy": "camera=(), microphone=(), geolocation=()",
        "referrer-policy": "no-referrer",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
    }
    for name, value in expected_headers.items():
        assert response.headers[name] == value

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "script-src https://cdn.jsdelivr.net" in docs.headers["content-security-policy"]

    denied = client.get("/security/monitoring", headers={"X-Demo-User-Id": EMPLOYEE_USER})
    assert denied.status_code == 403 and "tenant" not in denied.text.lower()
    private = "phase62-private-validation-input"
    invalid = client.post("/query", headers={"X-Demo-User-Id": EMPLOYEE_USER}, json={"question": private + "x" * 4_100})
    assert invalid.status_code == 422 and private not in invalid.text
    with patch("apps.api.app.main.security_snapshot", return_value={"status": "implemented_local_only", "events": [], "alerts": [], "integrity": {"valid": True, "record_count": 0, "head_hash": "0" * 64}, "taxonomy": [], "limitations": []}):
        allowed = client.get("/security/monitoring", headers={"X-Demo-User-Id": ADMIN_USER})
        assert allowed.status_code == 200


def test_assessment_documents_and_external_label() -> None:
    phase = ROOT / "docs" / "phase-62"
    required = {
        "threat-model.md", "assessment-plan.md", "control-mapping.md",
        "internal-prechecks.md", "finding-and-retest-workflow.md", "verification.md",
    }
    assert required.issubset({path.name for path in phase.glob("*.md")})
    combined = "\n".join((phase / name).read_text(encoding="utf-8") for name in required)
    assert "Independent validation required" in combined
    assert "Phase 47-49" in combined and "sealed" in combined.lower()


def main() -> None:
    test_targeted_static_precheck()
    test_container_runtime_is_non_root()
    test_dependency_inventory_is_reproducible_or_declared()
    test_local_dast_headers_and_negative_paths()
    test_assessment_documents_and_external_label()
    print("Phase 62 security assessment readiness checks passed.")


if __name__ == "__main__":
    main()
