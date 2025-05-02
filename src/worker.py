import json
import redis
from hotqueue import HotQueue
import os
import logging
import matplotlib.pyplot as plt
import pandas as pd
import base64
import io
import sys
from datetime import datetime

# Redis connection
redis_ip = os.environ.get('REDIS_HOST', 'redis-prod')
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

rd = redis.Redis(host=redis_ip, port=6379, db=0)
jdb = redis.Redis(host=redis_ip, port=6379, db=2)
rdb = redis.Redis(host=redis_ip, port=6379, db=3)
q = HotQueue('queue', host=redis_ip, port=6379, db=1)

def do_work(jid: str) -> None:
    job_data = jdb.get(jid)
    if not job_data:
        logger.error(f"No job found for jid: {jid}")
        return

    job = json.loads(job_data)
    job['status'] = 'in progress'
    jdb.set(jid, json.dumps(job))
    logger.info(f"Job {jid} in progress")

    try:
        start_date = datetime.strptime(job['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(job['end_date'], '%Y-%m-%d')

        # Collect sightings
        all_data = []
        for key in rd.scan_iter():
            raw = rd.get(key)
            if not raw:
                continue
            entry = json.loads(raw)
            date_str = entry.get("datetime", "")
            state = entry.get("state", "unknown")

            try:
                entry_date = datetime.strptime(date_str.split()[0], '%m/%d/%Y')
                if start_date <= entry_date <= end_date:
                    all_data.append(state.lower())
            except Exception:
                continue

        state_counts = pd.Series(all_data).value_counts().sort_values(ascending=False)

        if state_counts.empty:
            logger.warning(f"No sightings found for job {jid}")
            result = {
                "job_id": jid,
                "title": f"No UFO sightings found from {job['start_date']} to {job['end_date']}",
                "image_base64": ""
            }
            rdb.set(jid, json.dumps(result))
            job['status'] = 'complete'
            jdb.set(jid, json.dumps(job))
            return

        plt.figure(figsize=(12, 6))
        state_counts.plot(kind='bar')
        plt.title(f"UFO Sightings from {job['start_date']} to {job['end_date']}")
        plt.xlabel("State")
        plt.ylabel("Number of Sightings")
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()

        result = {
            "job_id": jid,
            "title": f"UFO Sightings from {job['start_date']} to {job['end_date']}",
            "image_base64": img_base64
        }

        rdb.set(jid, json.dumps(result))
        job['status'] = 'complete'
        jdb.set(jid, json.dumps(job))
        logger.info(f"Job {jid} completed successfully")

    except Exception as e:
        job['status'] = 'failed'
        jdb.set(jid, json.dumps(job))
        logger.exception(f"Error processing job {jid}: {str(e)}")

if __name__ == '__main__':
    for jid in q.consume(block=True):
        do_work(jid)
