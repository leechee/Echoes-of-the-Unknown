import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import redis
import pytest

class TestWorkerIntegration:

    def test_can_connect_to_results_db(self):
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        try:
            r = redis.Redis(host=redis_host, port=6379, db=3)
            keys = r.keys()
            assert isinstance(keys, list)
        except redis.exceptions.ConnectionError:
            pytest.fail("Redis connection failed. Is your Redis container running?")
