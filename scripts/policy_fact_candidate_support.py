"""Controlled application boundary shared by offline tests and one live diagnostic.

Identity and retrieval are explicit fixtures. Semantic stages and finalization are
real application code; this module never installs provider mocks or selects a key.
"""
from contextlib import ExitStack
from dataclasses import asdict
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.app import main
from apps.api.app.abuse.limiter import InMemoryLimitBackend, RateLimitManager
from apps.api.app.permissions.access_control import role_can_access
from apps.api.app.retrieval.types import RetrievedChunk


def authorized_sources(suite, case):
    sources = [RetrievedChunk(**s) for s in suite['sources'] if s['chunk_id'] in case['source_ids']]
    return [s for s in sources if role_can_access(s.access_roles, suite['role'])
            and s.project_id == suite['project_id'] and s.department_id is None]


def invoke(suite, case, *, streaming=False):
    sources = authorized_sources(suite, case)
    user = dict(id='00000000-0000-0000-0000-000000002701', business_role=suite['role'],
        is_admin=False, tenant_id='00000000-0000-0000-0000-000000002801',
        memberships=[dict(project_id=suite['project_id'], membership_level='viewer')])
    assessments = []
    original = main.assess_evidence

    def assess(*args, **kwargs):
        result = original(*args, **kwargs)
        assessments.append(dict(result=result.model_dump(mode='json'),
            policy_facts=[f.model_dump(mode='json') for f in result.policy_facts or []]))
        return result

    def retrieve(question, role, config):
        if role != suite['role'] or config.project_id != suite['project_id'] or config.department_id:
            raise ValueError('Diagnostic identity/scope differs')
        return sources

    with ExitStack() as stack:
        stack.enter_context(patch.dict(main.app.dependency_overrides, {main.current_demo_user: lambda: user}))
        stack.enter_context(patch.object(main, 'get_project', return_value={'id': suite['project_id']}))
        stack.enter_context(patch.object(main, 'retrieve_chunks', side_effect=retrieve))
        stack.enter_context(patch.object(main, 'get_rate_limit_manager',
                                       return_value=RateLimitManager(InMemoryLimitBackend())))
        stack.enter_context(patch.object(main, 'assess_evidence', side_effect=assess))
        # Suppress unrelated persistence/network sinks; receipts are captured separately.
        for target in ['apps.api.app.main.log_request', 'apps.api.app.main.submit_query_telemetry',
                       'apps.api.app.main.log_audit_event', 'apps.api.app.generation.answer_generator.log_audit_event',
                       'apps.api.app.reasoning.request_assessment.submit_auxiliary_telemetry',
                       'apps.api.app.reasoning.evidence_assessment.submit_auxiliary_telemetry',
                       'apps.api.app.reasoning.post_generation_validation.submit_auxiliary_telemetry']:
            stack.enter_context(patch(target))
        response = TestClient(main.app).post('/query/stream' if streaming else '/query', json={
            'question': case['question'], 'project_id': suite['project_id'],
            'multi_doc_mode': 'off', 'user_role': suite['role']})
    if response.status_code != 200:
        raise ValueError(f'Application HTTP {response.status_code}')
    if streaming:
        events = [(p.splitlines()[0][7:], json.loads(p.splitlines()[1][6:]))
                  for p in response.text.strip().split('\n\n')]
        if any(e == 'error' for e, _ in events):
            raise ValueError('Application streaming error')
        final = next(value for event, value in events if event == 'metadata')
    else:
        final = response.json()
    return dict(case_id=case['id'], question=case['question'], authorized_evidence=[asdict(s) for s in sources],
                assessments=assessments, final_response=final)
