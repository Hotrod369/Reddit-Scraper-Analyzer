import json
import os
import datetime as dt
import praw
from tools.config.logger_config import init_logger, logging
from tools.config.reddit_login import load_config, login

# Initialize and configure logger
init_logger()
logger = logging.getLogger(__name__)
logger.info("Basic logging set")

def setup_reddit():
    """
    Sets up the Reddit instance for scraping data, logging in, and loading the target subreddit.
    """
    logger.info("Setting up Reddit instance...")
    config = load_config()
    reddit = login(config)
    logger.info("Logged into Reddit.")
    return reddit, config

def fetch_posts(reddit, config):
    """
    Fetches posts from a subreddit based on the sorting method and limit specified in the configuration.
    """
    subreddit_name = config["subreddit"]
    post_sort = config.get("post_sort", {"method": "top", "limit": 100})
    subreddit = reddit.subreddit(subreddit_name)
    sort_method = post_sort["method"]
    posts_limit = post_sort["limit"]
    logger.info(f"Fetching {sort_method} posts from {subreddit_name} with limit {posts_limit}.")
    if sort_method == "top":
        return subreddit.top(limit=posts_limit)
    elif sort_method == "hot":
        return subreddit.hot(limit=posts_limit)
    elif sort_method == "new":
        return subreddit.new(limit=posts_limit)
    elif sort_method == "rising":
        return subreddit.rising(limit=posts_limit)
    elif sort_method == "controversial":
        return subreddit.controversial(limit=posts_limit)
    else:
        raise ValueError(f"Unsupported sort method: {sort_method}")

def fetch_user_info(reddit, username):
    """
    Fetches user info from Reddit's API.
    """
    logger.debug(f"Fetching user info for: {username}")
    try:
        user = reddit.redditor(username)
        return {'created_utc': user.created_utc} if hasattr(user, 'created_utc') else None
    except Exception as e:
        logger.error(f"Error fetching user info for '{username}': {e}")
        return None

def fetch_and_process_comments(reddit, submission):
    """
    Fetches and processes comments for a given submission on Reddit.
    """
    submission.comments.replace_more(limit=None)
    return [
        {
            'author': comment.author.name if comment.author else 'Deleted',
            'body': comment.body,
            'score': comment.score,
            'id': comment.id,
        }
        for comment in submission.comments.list()
        if comment.author and comment.author.name.lower() != "automoderator"
    ]

def process_submission(reddit, submission, user_data, post_data):
    """
    Processes a single submission, extracting data and comments.
    """
    author_name = submission.author.name if submission.author else 'Deleted'
    if author_name != 'Deleted':
        user_info = fetch_user_info(reddit, author_name)
        comments_data = fetch_and_process_comments(reddit, submission)
        post_data[submission.id] = {
            'User': author_name,
            'title': submission.title,
            'score': submission.score,
            'id': submission.id,
            'url': submission.url,
            'created_utc': submission.created_utc,
            'comments': comments_data
        }
        if user_info:
            user_data[author_name] = user_info

def run_scraper():
    """
    Main function to run the scraper.
    """
    reddit, config = setup_reddit()
    posts = fetch_posts(reddit, config)
    user_data = {}
    post_data = {}
    for submission in posts:
        process_submission(reddit, submission, user_data, post_data)

    # Saving logic here
    data_analysis_dir = os.path.join('..', 'Reddit-Scraper-Analyzer', 'analysis_results')
    if not os.path.exists(data_analysis_dir):
        os.makedirs(data_analysis_dir)
        logger.debug(f"Created directory {data_analysis_dir}")

    user_data_file_path = os.path.join(data_analysis_dir, 'user_data.json')
    with open(user_data_file_path, 'w', encoding='utf-8') as user_file:
        json.dump(user_data, user_file, ensure_ascii=False, indent=4)

    post_data_file_path = os.path.join(data_analysis_dir, 'submission_data.json')
    with open(post_data_file_path, 'w', encoding='utf-8') as submission_file:
        json.dump(post_data, submission_file, ensure_ascii=False, indent=4)

    logger.info('Scraping complete.')

if __name__ == "__main__":
    run_scraper()
