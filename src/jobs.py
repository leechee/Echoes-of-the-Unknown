import json
import uuid
import redis
from hotqueue import HotQueue
import os

redis_ip = os.environ.get('REDIS_HOST', 'redis-db')
rd = redis.Redis(host=redis_ip, port=6379, db=0)
q = HotQueue("queue", host=redis_ip, port=6379, db=1)
jdb = redis.Redis(host=redis_ip, port=6379, db=2)

def _generate_jid():
    return str(uuid.uuid4())

def _instantiate_job(jid, status, min_hgnc_id, max_hgnc_id):
    return {
        'id': jid,
        'status': status,
        'min_hgnc_id': min_hgnc_id,
        'max_hgnc_id': max_hgnc_id
    }

def _save_job(jid, job_dict):
    jdb.set(jid, json.dumps(job_dict))
    return

def _queue_job(jid):
    q.put(jid)
    return

def add_job(min_hgnc_id, max_hgnc_id, status="submitted"):
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, min_hgnc_id, max_hgnc_id)
    _save_job(jid, job_dict)
    _queue_job(jid)
    return job_dict

def get_job_by_id(jid):
    job_data = jdb.get(jid)
    if job_data:
        return json.loads(job_data)
    return None

def update_job_status(jid, status):
    job = get_job_by_id(jid)
    if job:
        job['status'] = status
        _save_job(jid, job)
    else:
        raise Exception("Job not found")
