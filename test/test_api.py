import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import requests

class TestAPIEndpoints:

    def test_sightings_route(self):
        """Check that /sightings returns a list"""
        response = requests.get("http://localhost:5000/sightings")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_sighting_by_id(self):
        """Assumes at least one item (ID 0) exists in Redis."""
        response = requests.get("http://localhost:5000/sightings/0")
        if response.status_code == 200:
            assert "datetime" in response.json()

    def test_jobs_route(self):
        """Check that /jobs returns a list of job IDs"""
        response = requests.get("http://localhost:5000/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
