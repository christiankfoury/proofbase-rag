"""Local token reservations for the bounded six-question diagnostic."""
import json
from decimal import Decimal
from functools import lru_cache
from importlib.metadata import version

from scripts.application_reliability_live import Stop


@lru_cache(maxsize=2)
def encoding(model):
    import tiktoken
    if version('tiktoken') != '0.12.0':
        raise Stop('Tokenizer version differs from reviewed preflight')
    return tiktoken.encoding_for_model(model)


def reservation(body, operation):
    # Complete serialized schema/messages plus generous framing allowance.
    # Conservative reservation, not a promise of exact provider usage.
    if body.get('stream') or body.get('tools') or body.get('functions') or body.get('n', 1) != 1:
        raise Stop('Only single synchronous text responses are priced')
    model = body.get('model')
    if body.get('service_tier') not in (None, 'default'):
        raise Stop('Only standard synchronous pricing is authorized')
    if operation == 'chat':
        if model != 'gpt-4.1-mini' or not body.get('messages') or not all(
                isinstance(m.get('content'), str) for m in body['messages']):
            raise Stop('Unpriced model or nontext messages')
        cap = body.get('max_completion_tokens', body.get('max_tokens'))
        if type(cap) is not int or not 1 <= cap <= 2048:
            raise Stop('Output cap exceeded')
        limit, rate = 16384, Decimal('.40')
    elif operation == 'embedding':
        values = body.get('input')
        single = isinstance(values, str) or (isinstance(values, list) and len(values) == 1 and isinstance(values[0], str))
        if model != 'text-embedding-3-small' or not single:
            raise Stop('Unpriced embedding model or batch input')
        limit, rate, cap = 8192, Decimal('.02'), 0
    else:
        raise Stop('No other operation authorized')
    serialized = json.dumps(body, ensure_ascii=False)
    bound = len(encoding(model).encode(serialized, disallowed_special=())) + 2048
    if bound > limit:
        raise Stop('Complete payload exceeds token reservation limit')
    return bound, cap, (bound * rate + cap * Decimal('1.60')) / 1_000_000


def payload_preflight():
    """Reassemble complete captured payloads with current schema/prompts.

    Include previously rejected bodies and reserve 4096 additional input tokens
    for changed candidate/repair text. Every actual body is guarded separately.
    """
    from pathlib import Path
    from copy import deepcopy
    from apps.api.app.prompts.prompt_registry import get_prompt
    from apps.api.app.reasoning.evidence_assessment import SemanticEvidenceDecision
    from apps.api.app.reasoning.post_generation_validation import SemanticValidationV3, candidate_units
    root = Path(__file__).resolve().parents[1] / 'data/evaluation/application-reliability-live-v1'
    bodies = [json.loads(p.read_bytes())['request'] for p in sorted(root.glob('*/raw/*.json'))]
    blocked = json.loads((root/'offline-source-diagnostics.json').read_bytes())['blocked_requests']
    bodies += [row['reconstructed_request'] for row in blocked]
    maxima, recovered = {}, []
    for original in bodies:
        body = deepcopy(original)
        schema = body.get('response_format', {}).get('json_schema', {})
        stage = schema.get('name', 'embedding' if 'input' in body else 'generation_or_repair')
        if stage.startswith('evidence_assessment'):
            schema['schema'] = SemanticEvidenceDecision.model_json_schema()
            body['messages'][0]['content'] = get_prompt('evidence_assessment', 'v3').content
        elif stage.startswith('post_generation_validation'):
            schema['schema'] = SemanticValidationV3.model_json_schema()
            body['messages'][0]['content'] = get_prompt('post_generation_validation', 'v3').content
            payload = json.loads(body['messages'][1]['content'])
            payload['candidate_units'] = candidate_units(payload['candidate']['answer'])
            body['messages'][1]['content'] = json.dumps(payload)
        operation = 'embedding' if 'input' in body else 'chat'
        bound, _, _ = reservation(body, operation)
        maxima[stage] = max(maxima.get(stage, 0), bound)
        if original in [r['reconstructed_request'] for r in blocked]:
            recovered.append(bound)
    if not bodies or len(recovered) != 3 or max(v for k,v in maxima.items() if k != 'embedding') + 4096 > 16384:
        raise Stop('Offline full-payload preparation lacks dynamic headroom')
    return {'payloads_checked': len(bodies), 'max_input_bound_by_stage': maxima,
            'previously_blocked_reassembled_bounds': recovered, 'extra_dynamic_headroom': 4096,
            'method': 'tiktoken 0.12.0 full JSON plus 2048 framing; pre-submit guard on every actual body'}
