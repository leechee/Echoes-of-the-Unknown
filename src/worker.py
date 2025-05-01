import json
import redis
from hotqueue import HotQueue
import os
import logging
import matplotlib.pyplot as plt
import pandas as pd
import base64
import io
from datetime import datetime

redis_ip = os.environ.get('REDIS_HOST', 'redis-prod')
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

rd = redis.Redis(host=redis_ip, port=6379, db=0)
jdb = redis.Redis(host=redis_ip, port=6379, db=2)
rdb = redis.Redis(host=redis_ip, port=6379, db=3)
q = HotQueue('queue', host=redis_ip, port=6379, db=1)

@q.worker
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

        # Retrieve and filter data
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

        # Count by state
        state_counts = pd.Series(all_data).value_counts().sort_values(ascending=False)

        # Plot
        plt.figure(figsize=(12, 6))
        state_counts.plot(kind='bar')
        plt.title(f"UFO Sightings from {job['start_date']} to {job['end_date']}")
        plt.xlabel("State")
        plt.ylabel("Number of Sightings")
        plt.tight_layout()

        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        plt.close()

        result = {
            "job_id": jid,
            "title": f"UFO Sightings from {job['start_date']} to {job['end_date']}",
            "image_base64": img_base64
        }

        rdb.set(jid, json.dumps(result))
        logger.info(f"Job {jid} complete with {len(state_counts)} states plotted")
        job['status'] = 'complete'
        jdb.set(jid, json.dumps(job))

    except Exception as e:
        job['status'] = 'failed'
        jdb.set(jid, json.dumps(job))
        logger.exception(f"Error processing job {jid}: {str(e)}")

if __name__ == '__main__':
    do_work()
