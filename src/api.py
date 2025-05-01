from flask import Flask, request, jsonify, send_file
import json
import logging
import os
import pandas as pd
import redis
import base64
from io import BytesIO

from jobs import add_job, get_job_by_id, jdb

# Flask setup
app = Flask(__name__)

# Redis databases
rd = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis-test'), port=6379, db=0)  # Raw UFO data
rdb = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis-test'), port=6379, db=3)  # Job results

# Logging setup
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Routes

@app.route('/help', methods=['GET'])
def help():
    return {
        "/help": "List all available routes",
        "/data [POST]": "Load UFO sightings data into Redis",
        "/data [GET]": "Return all UFO sightings",
        "/data [DELETE]": "Delete all UFO sightings",
        "/sightings [GET]": "List all sighting IDs",
        "/sightings/<sighting_id> [GET]": "Get a specific sighting by ID",
        "/jobs [POST]": "Submit a job to analyze data within a date range",
        "/jobs [GET]": "List all job IDs",
        "/jobs/<jobid> [GET]": "Get job status",
        "/results/<jobid> [GET]": "Get analysis result (if ready)"
    }

@app.route('/data', methods=['POST'])
def post_data():
    try:
        df = pd.read_csv(
            "data/ufodata.csv",
            encoding='ISO-8859-1',
            delimiter=',',
            on_bad_lines='skip',
            engine='python'
        )
        rd.flushdb()
        for idx, row in df.iterrows():
            sighting_id = str(idx)
            rd.set(sighting_id, row.to_json())
        logger.info(f"Loaded {len(df)} UFO sightings into Redis")
        return jsonify({'message': f'Successfully loaded {len(df)} sightings'})
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return jsonify({'error': str(e)})

@app.route('/data', methods=['GET'])
def get_data():
    sightings = []
    for key in rd.scan_iter():
        sighting_data = json.loads(rd.get(key))
        sightings.append(sighting_data)
    return jsonify(sightings)

@app.route('/data', methods=['DELETE'])
def delete_data():
    rd.flushdb()
    logger.warning("All UFO sighting data deleted from Redis")
    return jsonify({'message': 'All data deleted'})

@app.route('/sightings', methods=['GET'])
def get_sighting_ids():
    sighting_ids = [key.decode() for key in rd.keys()]
    return jsonify(sighting_ids)

@app.route('/sightings/<string:sighting_id>', methods=['GET'])
def get_sighting(sighting_id):
    sighting_json = rd.get(sighting_id)
    if not sighting_json:
        return jsonify({'error': 'Sighting not found'})
    return jsonify(json.loads(sighting_json))

@app.route('/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    if not start_date or not end_date:
        return jsonify({'error': 'Missing required parameters: start_date and end_date'})

    job = add_job(start_date, end_date)
    return jsonify(job)

@app.route('/jobs', methods=['GET'])
def list_jobs():
    return jsonify([key.decode() for key in jdb.keys()])

@app.route('/jobs/<jobid>', methods=['GET'])
def job_status(jobid):
    job = get_job_by_id(jobid)
    if job:
        return jsonify(job)
    return jsonify({'error': 'Job ID not found'})


@app.route('/results/<jobid>', methods=['GET'])
def get_result(jobid):
    result = rdb.get(jobid)
    if result is None:
        job = get_job_by_id(jobid)
        if job is None:
            return jsonify({'error': 'Invalid job ID'}), 404
        if job['status'] != 'complete':
            return jsonify({'message': 'Job is still processing'}), 202
        return jsonify({'error': 'No result found'}), 404

    result_data = json.loads(result)

    # Return image if format=image
    if request.args.get('format') == 'image':
        try:
            image_data = base64.b64decode(result_data['image_base64'])
            return send_file(BytesIO(image_data), mimetype='image/png')
        except Exception as e:
            return jsonify({'error': f'Image decoding failed: {str(e)}'}), 500

    # Otherwise return full JSON
    return jsonify(result_data)


# Main entry
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
