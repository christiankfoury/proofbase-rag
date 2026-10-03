"""Development application harness with controlled authorized retrieval and sessions.

No model replacement here. Saved drafts/checker decisions come from transport
receipts. Final 60-case measurement must use the real index instead.
"""
from contextlib import ExitStack
from dataclasses import asdict
import time
from unittest.mock import patch

from fastapi.testclient import TestClient
from apps.api.app import main
from apps.api.app.abuse.limiter import InMemoryLimitBackend, RateLimitManager
from scripts.policy_fact_candidate_support import authorized_sources


def invoke(suite, case):
    sources=authorized_sources(suite,case)
    user=dict(id='00000000-0000-0000-0000-000000002701',business_role=suite['role'],is_admin=False,
        tenant_id='00000000-0000-0000-0000-000000002801',
        memberships=[dict(project_id=suite['project_id'],membership_level='viewer')])
    history=[]; rows=[]
    def add(**kw):
        history.append(dict(role=kw['role'],content=kw['content']));return str(len(history))
    def retrieve(question,role,config):
        if role!=suite['role'] or config.project_id!=suite['project_id'] or config.department_id:
            raise RuntimeError('Development scope differs')
        return sources
    with ExitStack() as stack:
        stack.enter_context(patch.dict(main.app.dependency_overrides,{main.current_demo_user:lambda:user}))
        stack.enter_context(patch.object(main,'get_project',return_value={'id':suite['project_id']}))
        stack.enter_context(patch.object(main,'retrieve_chunks',side_effect=retrieve))
        stack.enter_context(patch.object(main,'get_session',return_value=dict(tenant_id=user['tenant_id'],user_id=user['id'])))
        stack.enter_context(patch.object(main,'list_messages',side_effect=lambda sid:list(history)))
        stack.enter_context(patch.object(main,'add_message',side_effect=add))
        stack.enter_context(patch.object(main,'get_rate_limit_manager',return_value=RateLimitManager(InMemoryLimitBackend())))
        for target in ['apps.api.app.main.log_request','apps.api.app.main.submit_query_telemetry',
            'apps.api.app.main.log_audit_event','apps.api.app.generation.answer_generator.log_audit_event',
            'apps.api.app.reasoning.request_assessment.submit_auxiliary_telemetry',
            'apps.api.app.reasoning.evidence_assessment.submit_auxiliary_telemetry',
            'apps.api.app.generation.conversational_candidate.submit_auxiliary_telemetry',
            'apps.api.app.reasoning.post_generation_validation.submit_auxiliary_telemetry']:
            stack.enter_context(patch(target))
        for index,question in enumerate(case['turns']):
            started=time.perf_counter()
            response=TestClient(main.app).post('/query',json=dict(question=question,project_id=suite['project_id'],
                session_id='00000000-0000-0000-0000-000000009001',multi_doc_mode='off',user_role=suite['role']))
            rows.append(dict(turn=index,question=question,status_code=response.status_code,
                final_response=response.json(),latency_ms=int((time.perf_counter()-started)*1000)))
    return dict(case_id=case['id'],authorized_evidence=[asdict(s) for s in sources],turns=rows)
