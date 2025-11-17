import logging
from pythonjsonlogger import jsonlogger
logger = logging.getLogger()

if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# Add a new handler with our JSON formatter
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(name)-30s %(levelname)-10s %(message)s" # TODO: add user token as the identifier to the log
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

logger.debug("🔥 handler_server.py is being imported")

from mangum import Mangum
from src.main import app

logger.debug("✅ app imported successfully")

handler = Mangum(app, lifespan="off")

logger.debug("✅ handler wrapped with Mangum")
