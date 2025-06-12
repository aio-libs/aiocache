import platform
import re
import subprocess
import time
from multiprocessing import Process

import pytest

from .server import run_server


# TODO: Fix and readd "memcached" (currently fails >98% of requests)
@pytest.fixture(params=("memory", "redis"))
def server(request):
    p = Process(target=run_server, args=(request.param,))
    p.start()
    time.sleep(1)
    yield
    p.terminate()
    p.join(timeout=15)


@pytest.mark.skipif(platform.python_implementation() == "PyPy", reason="Not working currently.")
def test_concurrency_error_rates(server):
    """Test with Apache benchmark tool."""

    total_requests = 1500
    # On some platforms, it's required to enlarge number of "open file descriptors"
    #  with "ulimit -n number" before doing the benchmark.
    cmd = ("ab", "-n", str(total_requests), "-c", "500", "http://127.0.0.1:8080/")
    result = subprocess.run(cmd, capture_output=True, check=True, encoding="utf-8")

    m = re.search(r"Failed requests:\s+([0-9]+)", result.stdout)
    assert m, "Missing output from ab: " + result.stdout
    failed_requests = int(m.group(1))

    m = re.search(r"Non-2xx responses:\s+([0-9]+)", result.stdout)
    non_200 = int(m.group(1)) if m else 0

    assert failed_requests / total_requests < 0.75, result.stdout
    assert non_200 / total_requests < 0.75, result.stdout
