"""Custody and schema for a newly authored current-runtime holdout."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import io
import tarfile
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/evaluation/current-runtime-v3"
COUNTS = dict(factual=8, multi_document=10, memory=8, permissions=10,
              ambiguity=6, missing_information=6, injection=6,
              conflicting_policies=4, uploaded_document_isolation=2)
PROJECT = "00000000-0000-0000-0000-000000000019"
USERS = {role: f"00000000-0000-0000-0000-00000000270{i}" for i, role in enumerate(
    ["Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin"], 1)}
FROZEN = ["apps/api/app", "data/synthetic-documents", "requirements.txt",
          "scripts/fresh_eval_grader.py", "scripts/fresh_eval_budget.py",
          "scripts/fresh_eval_protocol.py", "scripts/run_fresh_eval.py",
          "scripts/fresh_eval_environment.py", "scripts/reliable_evaluation_run.py",
          "scripts/run_independent_generalization_eval.py", "scripts/check_fresh_overlap.py",
          "docs/phase-64/authoring-contract.md", "scripts/current_eval_budget.py",
          "scripts/current_dimension_grader.py", "scripts/current_eval_calibration.py",
          "scripts/current_eval_environment.py", "scripts/current_eval_capture.py",
          "scripts/current_eval_protocol.py", "scripts/current_eval_run.py",
          "scripts/check_current_overlap.py", "scripts/reanalyze_saved_answers.py",
          "scripts/dimension_grader.py", "docs/phase-68/authoring-contract.md"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def file_inventory():
    paths = subprocess.check_output(["git", "ls-files", "--", *FROZEN], cwd=ROOT, text=True).splitlines()
    return {p: hashlib.sha256((ROOT / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in sorted(paths)}


def validate_suite(suite):
    """Structural validation; the separate author/validator attest semantic truth."""
    errors = []
    cases = suite.get("cases", [])
    if len(cases) != 60 or Counter(c.get("category") for c in cases) != Counter(COUNTS):
        errors.append("category_counts")
    ids = [c.get("case_id") for c in cases]
    if len(set(ids)) != len(ids):
        errors.append("duplicate_case_id")
    questions = [" ".join(c.get("question", "").lower().split()) for c in cases]
    if len(set(questions)) != len(questions):
        errors.append("duplicate_question")
    for c in cases:
        cid = str(c.get("case_id"))
        if not cid.startswith("fresh-") or not cid[6:].isdigit():
            errors.append(cid + ":id")
        if USERS.get(c.get("user_role")) != c.get("user_id") or c.get("project_id") != PROJECT:
            errors.append(cid + ":identity")
        if c.get("expected_behavior") not in {"answer", "clarify", "not_found", "refuse_no_access"}:
            errors.append(cid + ":behavior")
        if c.get("difficulty") not in {"easy", "medium", "hard"} or not c.get("rationale"):
            errors.append(cid + ":difficulty_rationale")
        facts = c.get("required_facts", [])
        if c.get("expected_behavior") == "answer" and not facts:
            errors.append(cid + ":missing_gold")
        if len({f.get("fact_id") for f in facts}) != len(facts):
            errors.append(cid + ":duplicate_fact")
        for fact in facts:
            if not all(isinstance(fact.get(k), str) and fact[k].strip() for k in ("fact_id", "text", "source_path", "source_quote")):
                errors.append(cid + ":fact_schema")
                continue
            source = (ROOT / fact["source_path"]).resolve()
            corpus = (ROOT / "data/synthetic-documents").resolve()
            if not source.is_relative_to(corpus) or not source.is_file():
                errors.append(cid + ":source_path")
            elif " ".join(fact["source_quote"].split()) not in " ".join(source.read_text(encoding="utf-8").split()):
                errors.append(cid + ":source_quote")
        turns = c.get("previous_turns", [])
        if c.get("category") == "memory" and not turns:
            errors.append(cid + ":missing_memory")
        if any(t.get("role") not in {"user", "assistant"} or not isinstance(t.get("content"), str) for t in turns):
            errors.append(cid + ":turn_schema")
        if c.get("category") == "uploaded_document_isolation":
            fixture = c.get("upload_fixture", {})
            if not all(isinstance(fixture.get(k), str) and fixture[k].strip() for k in ("title", "text")):
                errors.append(cid + ":upload_fixture")
            if c.get("expected_behavior") != "not_found":
                errors.append(cid + ":upload_isolation_behavior")
    return errors


def committed_inventory(freeze):
    commit = freeze["commit"]
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Invalid frozen commit")
    data = subprocess.check_output(["git", "archive", "--format=tar", commit, "--", *freeze["files"]], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        return {m.name: hashlib.sha256(archive.extractfile(m).read().replace(b"\r\n", b"\n")).hexdigest()
                for m in archive.getmembers() if m.isfile()}


def verify_custody(*, folder=None, require_current=True):
    folder = folder or FOLDER
    freeze = json.loads((folder / "freeze.json").read_text(encoding='utf-8'))
    inventory = file_inventory() if require_current else committed_inventory(freeze)
    if freeze["files"] != inventory:
        raise ValueError("Frozen files changed; do not execute holdout")
    if not require_current:
        grader = "scripts/current_dimension_grader.py"
        current_grader = hashlib.sha256((ROOT / grader).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if current_grader != freeze["files"][grader]:
            raise ValueError("Offline replay requires the frozen grader version")
    seal = json.loads((folder / "seal.json").read_text(encoding='utf-8'))
    if seal["freeze_sha256"] != digest(folder / "freeze.json") or seal["suite_sha256"] != digest(folder / "holdout.json"):
        raise ValueError("Custody hash mismatch")
    review = json.loads((folder / "author-validation.json").read_text(encoding='utf-8'))
    if (review.get("suite_sha256") != seal["suite_sha256"] or review.get("status") != "approved"
        or digest(folder / "author-validation.json") != seal["validation_sha256"]):
        raise ValueError("Separate author validation missing")
    suite = json.loads((folder / "holdout.json").read_text(encoding='utf-8'))
    if suite.get("authored_after_freeze") != freeze["commit"]:
        raise ValueError("Authorship does not reference the frozen revision")
    errors = validate_suite(suite)
    if errors:
        raise ValueError(str(errors))
    return freeze, suite
