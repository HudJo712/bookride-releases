import logging
import os
from config_loader import load_config

config = load_config()
active_env = os.getenv("APP_ENV", "dev").lower()

# Configure logging based on environment debug flag
log_level = logging.DEBUG if config["DEBUG"] else logging.INFO
logging.basicConfig(level=log_level, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("bookride")
logger.setLevel(log_level)

print(f"Environment: {active_env}")
print(f"Connecting to {config['DB_URL']}")
print(f"Logging level set to {logging.getLevelName(log_level)}")
print(f"Debug logging enabled: {logger.isEnabledFor(logging.DEBUG)}")
