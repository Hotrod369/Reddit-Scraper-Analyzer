'''
This file handles the Reddit login and configuration options
'''
import json
import praw
import praw.exceptions


def load_config():
    """ Load configuration file """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError("The config file 'config.json' was not found. \
            Please create it or check the path.") from exc

    missing = set(["client_id", "client_secret", "subreddit", \
        "username", "password"]) - set(config.keys())
    if len(missing) > 0:
        raise KeyError(f"Missing keys in config.json: {str(missing)}")
    if "user_agent" not in config:
        config["user_agent"] = "Reddit Scraper (by u/Allan_QuartermainSr)"
    return config


def login(config):
    """ Login to Reddit """
    reddit = praw.Reddit(
        user_agent=config['user_agent'],
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        password=config['password'],
        username=config['username']
    )
    return reddit
