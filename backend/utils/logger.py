import logging
import sys

def get_logger(name: str = "zendesk_app") -> logging.Logger:
    """
    Returns a configured logger.
    - Logs to stdout (so Docker/Kubernetes picks it up).
    - INFO by default, but can be overridden via LOG_LEVEL env var.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent duplicate handlers in reloads
        handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
