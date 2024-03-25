'''
This file handles the Reddit login and configuration options
'''
import json
import praw
import praw.exceptions
from tools.config.logger_config import init_logger
import logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()


def load_config():
    """
    Loads the configuration from a JSON file and returns it as a dictionary.
    """
    config_path = 'tools/config/config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info("Config loaded successfully")
            return config  # Ensure this is inside the try block to return the loaded config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found.")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from the configuration file {config_path}.")
        raise
def login(config):  # sourcery skip: inline-immediately-returned-variable
    """
    The `login` function logs into Reddit using the provided configuration parameters.
    """
    reddit = praw.Reddit(
        user_agent=config['user_agent'],
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        password=config['password'],
        username=config['username']
    )
    logger.info(f"Logged in as {reddit.user.me()}")
    return reddit
