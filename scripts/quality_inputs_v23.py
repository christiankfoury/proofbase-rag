"""Capture authorized database titles and bind them to unchanged source text."""
from scripts.reanalyze_saved_answers import build_inputs as text_inputs, DIMS
from scripts.quality_eval_contract_v23 import metadata


def authoritative_evidence(settings, case, payload):
    from scripts.run_fresh_eval import authoritative_evidence as capture_text
    import psycopg
    evidence, flags = capture_text(settings, case, payload)
    # Only IDs already admitted by the independent role/tenant/project check.
    # Do not trust titles supplied in the answer's citation objects.
    with psycopg.connect(settings.database_url) as conn:
        for item in evidence:
            row = conn.execute('''select d.title from chunks c join documents d
                on d.id=c.document_id where c.id::text=%s
                and d.external_document_id=%s and d.tenant_id::text=%s
                and d.project_id::text=%s''',
                (item['chunk_id'], item['document_id'], item['tenant_id'], item['project_id'])).fetchone()
            if not row or not isinstance(row[0], str) or not row[0].strip():
                raise ValueError('Authoritative document title missing')
            item['document_title'] = row[0]
    return evidence, flags


def build_inputs(case, row):
    inputs = text_inputs(case, row)
    evidence = row['authorized_evidence']
    if any(not isinstance(e.get('document_title'), str) or not e['document_title'].strip() for e in evidence):
        raise ValueError('Authoritative document titles required')
    inputs['source_metadata'] = metadata(evidence)
    return inputs
