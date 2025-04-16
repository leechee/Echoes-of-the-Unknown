from flask import Flask, request, jsonify
import redis
import json
from jobs import add_job, get_job_by_id, jdb

app = Flask(__name__)
rd = redis.Redis(host='redis-db', port=6379, db=0)

@app.route('/data', methods=['POST'])
def post_data():
    import requests
    url = "https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json"
    response = requests.get(url)
    data = response.json()
    genes = data.get('response', {}).get('docs', [])

    rd.flushdb()
    count = 0
    for gene in genes:
        hgnc_id = gene.get('hgnc_id')
        if hgnc_id:
            cleaned_gene = {k: (v if v is not None else "") for k, v in gene.items()}
            rd.set(hgnc_id, json.dumps(cleaned_gene))
            count += 1

    return jsonify({'message': f'Successfully loaded {count} genes'})

@app.route('/data', methods=['GET'])
def get_data():
    genes = []
    for key in rd.scan_iter():
        gene_data = json.loads(rd.get(key))
        genes.append(gene_data)
    return jsonify(genes)

@app.route('/data', methods=['DELETE'])
def delete_data():
    rd.flushdb()
    return jsonify({'message': 'All data deleted'})

@app.route('/genes', methods=['GET'])
def get_gene_ids():
    gene_ids = [key.decode() for key in rd.keys()]
    return jsonify(gene_ids)

@app.route('/genes/<string:hgnc_id>', methods=['GET'])
def get_gene(hgnc_id):
    gene_json = rd.get(hgnc_id)
    if not gene_json:
        return jsonify({'error': 'Gene not found'})
    return jsonify(json.loads(gene_json))

@app.route('/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    min_hgnc_id = data.get('min_hgnc_id')
    max_hgnc_id = data.get('max_hgnc_id')
    if min_hgnc_id is None or max_hgnc_id is None:
        return jsonify({'error': 'Missing required parameters: min_hgnc_id and max_hgnc_id'})

    job = add_job(min_hgnc_id, max_hgnc_id)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
