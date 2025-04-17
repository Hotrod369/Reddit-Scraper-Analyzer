import logging

def init_logger(file="app.log"):
    """
    Initialize logger with production-level settings.
    """
    logging.basicConfig(
        level=logging.INFO,  # Change to DEBUG or WARNING if desired
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(file, encoding='utf-8', delay=True),
        ],
    )
    return logging.getLogger()