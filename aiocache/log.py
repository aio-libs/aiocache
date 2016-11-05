import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(filename)s(%(lineno)s) | %(message)s")

logger = logging.getLogger('aiocache')
