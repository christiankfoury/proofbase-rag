"""Isolated local index clone for the accepted development candidate."""
import os
from scripts.bounded_redesign_preflight import configure as configure_profile
from scripts.phase73_v6_environment import fingerprint as base_fingerprint
from scripts.conversation_continuation import ROOT

DBNAME='proofbase_conversation_eval_20261003'


def configure():
    from apps.api.app.core.config import get_settings
    from psycopg.conninfo import conninfo_to_dict,make_conninfo
    from urllib.parse import urlsplit,urlunsplit
    original=get_settings();parts=conninfo_to_dict(original.database_url)
    if parts.get('host') not in {'localhost','127.0.0.1'}:raise ValueError('Local database required')
    parts['dbname']=DBNAME
    configure_profile('candidate-challenger')
    os.environ['DATABASE_URL']=make_conninfo(**parts)
    # Admission does not spend money; the shared receipt ledger enforces USD12.50.
    os.environ['TENANT_DAILY_AI_BUDGET_USD']='12.50'
    if original.rate_limit_backend=='redis':
        redis=urlsplit(original.redis_url)
        os.environ['REDIS_URL']=urlunsplit(redis._replace(path='/14'))
    for key,name in {'OBSERVABILITY_LOG_PATH':'requests.jsonl','AUDIT_LOG_PATH':'audit.jsonl',
        'SECURITY_EVENT_LOG_PATH':'security.jsonl','SECURITY_NOTIFICATION_LOG_PATH':'notifications.jsonl',
        'UPLOAD_STORAGE_DIR':'uploads','FILE_QUARANTINE_DIR':'quarantine'}.items():
        os.environ[key]=str(ROOT/'data/evaluation/local-runs/conversation-final'/name)
    get_settings.cache_clear();return get_settings()


def fingerprint(settings):
    value=base_fingerprint(settings)
    value['database']=DBNAME
    value['candidate_settings']=dict(enabled=settings.conversational_candidate_enabled,model=settings.conversational_candidate_model)
    return value


def prepare():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict,make_conninfo
    from apps.api.app.core.config import get_settings
    parts=conninfo_to_dict(get_settings().database_url)
    if parts.get('host') not in {'localhost','127.0.0.1'} or parts.get('dbname')==DBNAME:raise ValueError('Expected original local database')
    source=parts['dbname'];parts['dbname']='postgres'
    with psycopg.connect(make_conninfo(**parts),autocommit=True) as conn:
        if conn.execute('select 1 from pg_database where datname=%s',(DBNAME,)).fetchone():raise ValueError('Preserve existing clone')
        conn.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(DBNAME),sql.Identifier(source)))
    print('Created isolated index clone; original database retained')


if __name__=='__main__':
    import sys,json
    if sys.argv[1:] == ['prepare']:prepare()
    else:print(json.dumps(fingerprint(configure()),indent=2))
