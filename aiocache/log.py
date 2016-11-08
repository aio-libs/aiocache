import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s(%(lineno)s) | %(message)s")

logger = logging.getLogger(__name__)
