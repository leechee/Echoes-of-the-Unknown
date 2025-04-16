# src/worker.py
import json
import time
import redis
from hotqueue import HotQueue
import os

redis_ip = os.environ.get('REDIS_HOST', 'redis-db')
q = HotQueue('queue', host=redis_ip, port=6379, db=1)
jdb = redis.Redis(host=redis_ip, port=6379, db=2)

@q.worker
def do_work(jid):
    job_data = jdb.get(jid)
    #simple error case
    if not job_data:
        print(f"No job found for jid: {jid}")
        return
    job = json.loads(job_data)
    job['status'] = 'in progress'
    jdb.set(jid, json.dumps(job))
    time.sleep(10)
    job['status'] = 'complete'
    jdb.set(jid, json.dumps(job))

do_work()
