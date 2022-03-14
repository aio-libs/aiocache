import re
import subprocess
import time
from multiprocessing import Process

import pytest

from .server import run_server


@pytest.fixture
def redis_server():
    p = Process(target=run_server, args=["redis"])
    p.start()
    yield
    p.terminate()
    time.sleep(2)


@pytest.fixture
def memcached_server():
    p = Process(target=run_server, args=["memcached"])
    p.start()
    yield
    p.terminate()
    time.sleep(2)


@pytest.fixture
def memory_server():
    p = Process(target=run_server, args=["memory"])
    p.start()
    yield
    p.terminate()
    time.sleep(2)


@pytest.fixture(params=["memcached_server", "memory_server", "redis_server"])
def server(request):
    return request.getfixturevalue(request.param)


def test_concurrency_error_rates(server):
    total_requests = 1500
    result = subprocess.run(
        ["ab", "-n", str(total_requests), "-c", "500", "http://127.0.0.1:8080/"],
        stdout=subprocess.PIPE,
    )

    failed_requests = total_requests
    m = re.search(r"Failed requests:\s+([0-9]+)", str(result.stdout))
    if m:
        failed_requests = int(m.group(1))

    non_200 = 0
    m = re.search(r"Non-2xx responses:\s+([0-9]+)", str(result.stdout))
    if m:
        non_200 = int(m.group(1))

    print("Failed requests: {}%".format(failed_requests / total_requests * 100))
    print("Non 200 requests: {}%".format(non_200 / total_requests * 100))
    assert (
        failed_requests / total_requests < 0.75
    )  # aioredis is the problem here, need to improve it
    assert non_200 / total_requests < 0.75
