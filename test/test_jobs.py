import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from jobs import add_job, get_job_by_id

class TestJobsAPI:

    def test_add_job_creates_valid_structure(self):
        """Test job creation and structure of returned dict"""
        job = add_job(100, 200)
        assert isinstance(job, dict)
        assert "id" in job
        assert job["min_hgnc_id"] == 100
        assert job["max_hgnc_id"] == 200
        assert job["status"] == "submitted"

    def test_get_job_by_id_returns_job(self):
        """Test that a created job can be retrieved"""
        job = add_job(100, 200)
        job_id = job["id"]
        fetched = get_job_by_id(job_id)
        assert fetched["id"] == job_id
        assert fetched["status"] == "submitted"
