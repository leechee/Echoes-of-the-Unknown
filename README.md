# The Light of Other Jobs

This repository contains one python script along with instructions on how to deploy the app with docker-compose, run POST GET AND DELETE ROUTES, and specialized routes. The primary script uses Flask and Redis, and can be accessed by 5 different routes. The objective of this homework was to get familiar with using Flask in conjunction with Redis to build a practical application with a new and more complicated data set. Orchestrating docker-compose is important because it simplifies things, while also serving as a foundation of future projects.

### Important Files:

The primary Python script is [api.py](api.py), which ingests the HGNC data using the requests library in a dictionary format. The user can use Flask routes to run the functions from the command line, pulling data from a Redis database.

[docker-compose.yml](docker-compose.yml) is an important file that orchestrates Flask, Redis, and the environment which runs the testing script.

[Dockerfile](Dockerfile) and [requirements.txt](requirements.txt) work in conjunction to load a proper environment which the user can run the scripts. Dockerfile defines the container setup, while requirements.txt lists the necessary Python dependencies.

The [jobs.py](jobs.py) script manages the queuing system and allows for jobs to be submitted and tracked.

[worker.py](worker.py) is the background service which listens for jobs and updates their status accordingly.

## Data Input
You can find the HGNC data on this page: https://www.genenames.org/download/archive/

Scroll to the bottom and look for the link that says "Current tab separated hgnc_complete_set file" or "Current JSON format hgnc_complete_set file". 

The data can be downloaded in two different formats. Additionally, the requests library can be used to derive the data as well. In this homework I chose to go with the json format.

The HGNC dataset provides comprehensive information about human genes, including standardized nomenclature, genomic coordinates, gene families, and cross-references to other databases. This authoritative resource is maintained by the HUGO Gene Nomenclature Committee (HGNC) at the European Bioinformatics Institute.

## Getting Started 
### Deploying the App with Docker Compose
```
docker-compose up
```
This command utilizes docker-compose.yml to deploy Flask, Redis, and the worker container.

### Run Curl Commands and Interpretation

#### How to run POST /data
```
curl -X POST http://localhost:5000/data
```
This route loads the HGNC data into redis

```
"message": "Successfully loaded 44067 genes"
```
This message that pops up indicates that the data was successfully loaded.

#### How to run GET /data
```
curl -X GET http://localhost:5000/data
```
This route returns all of the data from redis, an example output will be listed below in the specific gene route.

#### How to run DELETE /data
```
curl -X DELETE http://localhost:5000/data
```
This route deletes all of the data from redis.
```
"message": "All data deleted"
```
When the above message appears, it means the data has successfully been removed.

#### How to run route /genes
```
curl http://localhost:5000/genes
```
This returns the json-formatted list of all hgnc_ids. Below is an example part of the output:
```
  "HGNC:53258",
  "HGNC:55463",
  "HGNC:47091",
  "HGNC:16534",
  "HGNC:34333",
  "HGNC:27740",
  "HGNC:55099",
  "HGNC:5107",
  "HGNC:20892",
```

#### How to run route /genes/'hgnc_id'
```
curl http://localhost:5000/genes/'hgnc_id'
```
This returns all the data associated with the specific hgnc_id entree. If the user inputs an invalid id, it will return an error warning. Below is an example output of a specific hgnc id. Keep in mind the data is sparse, meaning that the values with N/A are not listed and cleaned out.
```
{
  "agr": "HGNC:5",
  "ccds_id": ["CCDS12976"],
  "date_approved_reserved": "1989-06-30",
  "date_modified": "2023-01-20",
  "ensembl_gene_id": "ENSG00000121410",
  "entrez_id": "1",
  "gene_group": ["Immunoglobulin like domain containing"],
  "gene_group_id": [594],
  "hgnc_id": "HGNC:5",
  "location": "19q13.43",
  "location_sortable": "19q13.43",
  "locus_group": "protein-coding gene",
  "locus_type": "gene with protein product",
  "mane_select": ["ENST00000263100.8", "NM_130786.4"],
  "merops": "I43.950",
  "mgd_id": ["MGI:2152878"],
  "name": "alpha-1-B glycoprotein",
  "omim_id": ["138670"],
  "pubmed_id": [2591067],
  "refseq_accession": ["NM_130786"],
  "rgd_id": ["RGD:69417"],
  "status": "Approved",
  "symbol": "A1BG",
  "ucsc_id": "uc002qsd.5",
  "uniprot_ids": ["P04217"],
  "uuid": "fb61cb93-470c-4c3f-838a-83243c4cfe01",
  "vega_id": "OTTHUMG00000183507"
}
```

---

## New Job Routes

In the context of this project, a job is a request to analyze a subset of genes based on their HGNC IDs. Users must provide a JSON packet with two required fields: `min_hgnc_id` and `max_hgnc_id`, which should be numeric components of the HGNC identifiers (e.g., HGNC:100 to HGNC:5000).

These parameters allow the worker to identify and later analyze all gene entries falling within that numeric ID range. If either `min_hgnc_id` or `max_hgnc_id` is missing from the request, the job will not be submitted, and the user will receive an error message explaining the problem.

#### How to run POST /jobs
```
curl localhost:5000/jobs -X POST -d '{"min_hgnc_id":100, "max_hgnc_id":5000}' -H "Content-Type: application/json"
```
This creates a new job, returning a JSON object with the job id, status, and parameters.
```
{
  "id": "c6f572de-c36f-4915-80e5-b844b05c54ab",
  "max_hgnc_id": 5000,
  "min_hgnc_id": 100,
  "status": "submitted"
}
```

#### How to run GET /jobs
```
curl http://localhost:5000/jobs
```
This returns a list of all job IDs (example output below):
```
[
  "c6f572de-c36f-4915-80e5-b844b05c54ab",
  "97be6782-eb7c-4e32-849f-d9c7414fdc86",
  "7550cdbd-50d6-4ea4-929b-3e2d81e8d449"
]
```

#### How to run GET /jobs/<jobid>
```
curl http://localhost:5000/jobs/c4711fe8-5031-4cb4-b2d6-3e53641fcf4d
```
This returns job info: status, parameters, and ID. If the job doesn’t exist, an error message is returned.
```
{
  "id": "c6f572de-c36f-4915-80e5-b844b05c54ab",
  "max_hgnc_id": 5000,
  "min_hgnc_id": 100,
  "status": "complete"
}
```

---

### Clean Up!

Run these command to close all containers:
```
docker-compose down --remove-orphans # I found this complete reset to be useful
docker rm -f `docker ps -aq`
```
