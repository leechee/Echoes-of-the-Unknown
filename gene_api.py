from flask import Flask, jsonify, request
import requests
import redis
import json

app = Flask(__name__)
rd = redis.Redis(host='redis-db', port=6379, db=0)

@app.route('/data', methods=['POST'])
def post_data():
    """grab hgnc gene data from url and dump it into redis"""
    url = "https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json"
    
    response = requests.get(url)
    data = response.json()
    genes = data.get('response', {}).get('docs', [])

    rd.flushdb()  # clear existing data

    count = 0
    for gene in genes:
        hgnc_id = gene.get('hgnc_id')
        if hgnc_id:
            # make sure empty stuff is stored as "" not None, for some reason it doesn't display " " but just ignores it?
            cleaned_gene = {k: (v if v is not None else "") for k, v in gene.items()}
            rd.set(hgnc_id, json.dumps(cleaned_gene))
            count += 1

    return jsonify({'message': f'Successfully loaded {count} genes'})

@app.route('/data', methods=['GET'])
def get_data():
    """pull all the gene data from redis"""
    genes = []
    for key in rd.scan_iter():
        gene_data = json.loads(rd.get(key))
        genes.append(gene_data)
    return jsonify(genes)

@app.route('/data', methods=['DELETE'])
def delete_data():
    """wipe all gene data from redis"""
    rd.flushdb()
    return jsonify({'message': 'All data deleted'})

@app.route('/genes', methods=['GET'])
def get_gene_ids():
    """get all the hgnc_ids we have stored"""
    gene_ids = [key.decode() for key in rd.keys()]
    return jsonify(gene_ids)

@app.route('/genes/<string:hgnc_id>', methods=['GET'])
def get_gene(hgnc_id):
    """look up a specific gene by its id"""
    gene_json = rd.get(hgnc_id)
    
    #our error handling for invalid gene ID provided by user
    if not gene_json:
        return jsonify({'error': 'Gene not found'})
    return jsonify(json.loads(gene_json))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)