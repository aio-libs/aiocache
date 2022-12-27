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
    """Test with Apache benchmark tool."""

    total_requests = 1500
    # On some platforms, it's required to enlarge number of "open file descriptors"
    #  with "ulimit -n number" before doing the benchmark.
    cmd = ("ab", "-n", str(total_requests), "-c", "500", "http://127.0.0.1:8080/")
    try:
        result = subprocess.run(cmd, capture_output=True, check=True, encoding="utf-8")
    except subprocess.CalledProcessError as e:
        print("OUT:", e.stdout)
        print("ERR:", e.stderr)
        raise

    m = re.search(r"Failed requests:\s+([0-9]+)", result.stdout)
    assert m, "Missing output from ab: " + result.stdout
    failed_requests = int(m.group(1))

    m = re.search(r"Non-2xx responses:\s+([0-9]+)", result.stdout)
    assert m, "Missing output from ab."
    non_200 = int(m.group(1))

    assert failed_requests / total_requests < 0.75
    assert non_200 / total_requests < 0.75
