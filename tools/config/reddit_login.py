'''
This file handles the Reddit login and configuration options
'''
import praw
import logging
import json
from tools.config.logger_config import init_logger

# Initialize logging
logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

def load_config():
    """
    Load the configuration from the config file.
    """
    try:
        with open('tools/config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("Config loaded successfully")
        return config
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding config file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
    return None

def login(config):
    """
    Log in to Reddit using PRAW in read-only mode.
    """
    try:
        reddit = praw.Reddit(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            user_agent=config['user_agent']
        )
        logger.info(f"Logged in as read-only: {reddit.read_only}")
        return reddit
    except KeyError as e:
        logger.error(f"Missing key in config file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
    return None

if __name__ == "__main__":
    if config := load_config():
        if reddit := login(config):
            print(f"Logged in as read-only: {reddit.read_only}")