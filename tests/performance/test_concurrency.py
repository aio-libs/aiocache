import re
import subprocess
import time
from multiprocessing import Process

import pytest

from .server import run_server


@pytest.fixture(params=("memory", "memcached", "redis"))
def server(request):
    p = Process(target=run_server, args=(request.param,))
    p.start()
    time.sleep(1)
    yield
    p.terminate()
    p.join(timeout=15)


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
    non_200 = int(m.group(1)) if m else 0

    print(failed_requests / total_requests, non_200 / total_requests)
    assert failed_requests / total_requests < 0.75
    assert non_200 / total_requests < 0.75
