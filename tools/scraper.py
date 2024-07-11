import json
import os
import datetime as dt  # noqa: F401
import time
import prawcore
from prawcore.exceptions import TooManyRequests
from tqdm import tqdm
from requests import get  # noqa: F401
from tools.config.logger_config import init_logger
from tools.config.reddit_login import load_config, login
import logging

logger = logging.getLogger(__name__)
logger.info("Scraper Basic logging set")
init_logger()

def handle_rate_limit(retry_after):
    if retry_after is None:
        logger.warning("Rate limit exceeded but retry_after time is not set. Using a default sleep of 1 second.")
        time.sleep(1)
    else:
        logger.warning(f"Rate limit exceeded. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after + 1)  # Adding an extra second for safety

def setup_reddit():
    """
    Sets up the Reddit instance for scraping data, logging in, and loading the target subreddit.
    """
    logger.debug("Setting up Reddit instance...")
    config = load_config()
    reddit = login(config)
    reddit.config.ratelimit_seconds = 60  # PRAW will sleep for 60 seconds when hitting the rate limit
    logger.info("Logged into Reddit.")
    return reddit, config

def fetch_posts(reddit, config):
    """
    Fetches posts from each subreddit based on the sorting method and limit specified in the configuration.
    """
    logger.info("Fetching posts...")
    subreddit_names = config["subreddit"].split('+')
    post_sort = config.get("post_sort", {"method": "new", "limit": 1000})
    sort_method = post_sort["method"]
    posts_limit = post_sort["limit"]
    all_posts = []

    for subreddit_name in tqdm(subreddit_names, desc="Fetching subreddits"):
        try:
            subreddit = reddit.subreddit(subreddit_name)
            logger.debug(f"Fetching {sort_method} posts from {subreddit_name} with limit {posts_limit}.")
            # The method below will trigger the API call and may raise an exception if there's an issue
            if sort_method == "top":
                posts = subreddit.top(limit=posts_limit)
            elif sort_method == "hot":
                posts = subreddit.hot(limit=posts_limit)
            elif sort_method == "new":
                posts = subreddit.new(limit=posts_limit)
            elif sort_method == "rising":
                posts = subreddit.rising(limit=posts_limit)
            elif sort_method == "controversial":
                posts = subreddit.controversial(limit=posts_limit)
            else:
                raise ValueError(f"Unsupported sort method: {sort_method}")

            all_posts.extend(posts)
        except TooManyRequests as e:
            handle_rate_limit(e.response.headers.get('retry-after'))
            continue
        except prawcore.exceptions.Redirect:
            logger.error(f"Failed to fetch posts from '{subreddit_name}'. This may be due to a typo in the subreddit name, the subreddit being private, banned, or non-existent. Please check the subreddit name in the config file.")
            continue
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching posts from '{subreddit_name}': {e}")
            continue

    return all_posts

def fetch_user_info(reddit, username, config):
    """
    Fetches user info from Reddit's API using configurable limits.
    """
    logger.debug(f"Fetching user info for: {username}")
    logger.debug(f"Type of username before fetch_user_info call: {type(username)}")

    if username.lower() == 'deleted':
        logger.debug(f"User '{username}' is deleted, skipping.")
        return None

    try:
        user = reddit.redditor(username)
        _ = user.link_karma  # Trigger an attribute access to check user existence
    except Exception as e:
        logger.error(f"User '{username}' not found: {e}.")
        return None

    try:
        return fetch_comments_from_submissions(user, username, config)
    except Exception as e:
        logger.error(f"Error while fetching user info for '{username}': {e}")
        return None

def fetch_comments_from_submissions(user, username, config):
    if not hasattr(user, 'created_utc'):
        logger.error(f"User '{username}' has no creation date.")
        return None

    creation_time = user.created_utc
    # Use configurable limits from the config
    comments_limit = config.get("comments_limit", 1000) # Default to 100 if not set
    submissions_limit = config.get("submissions_limit", 1000) # Default to 25 if not set

    logger.debug(f"Comments limit: {comments_limit}")
    logger.debug(f"Submissions limit: {submissions_limit}")

    comments = list(user.comments.new(limit=comments_limit))
    submissions = list(user.submissions.new(limit=submissions_limit))

    first_comment = comments[-1] if comments else None
    first_submission = submissions[-1] if submissions else None

    if first_comment and first_submission:
        first_activity_time = min(first_comment.created_utc, first_submission.created_utc)
    elif first_comment:
        first_activity_time = first_comment.created_utc
    elif first_submission:
        first_activity_time = first_submission.created_utc
    else:
        first_activity_time = time.time()

    dormant_time = first_activity_time - creation_time
    dormant_days = dormant_time // (24 * 60 * 60)

    user_data = {
        'username': username,
        'Karma': user.link_karma + user.comment_karma,
        'created_utc': user.created_utc,
        'dormant_days': dormant_days,
        'user_is_verified': getattr(user, 'is_verified', False),
        'awardee_karma': user.awardee_karma,
        'awarder_karma': user.awarder_karma,
        'total_karma': user.total_karma,
        'has_verified_email': getattr(user, 'has_verified_email', False),
        'link_karma': user.link_karma,
        'comment_karma': user.comment_karma,
        'accept_followers': getattr(user, 'accept_followers', False),
    }
    logger.debug(f"Fetched User Info for {username}.")
    return user_data

def fetch_and_process_comments(reddit, submission):
    """
    Fetches and processes comments for a given submission on Reddit.
    """
    try:
        submission.comments.replace_more(limit=None)
        logger.debug(f"Processing comments for submission {submission.id}")
        return [
            {
                'author': comment.author.name if comment.author else 'Deleted',
                'body': comment.body,
                'score': comment.score,
                'id': comment.id,
            }
            for comment in tqdm(submission.comments.list(), desc=f"Fetching comments for {submission.id}")
            if comment.author and comment.author.name.lower() != "automoderator"
            and comment.author.name.lower() != "reddit"
        ]
    except TooManyRequests as e:
        handle_rate_limit(e.response.headers.get('retry-after'))
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching comments for submission '{submission.id}': {e}")
        return []

def process_submission(config, reddit, submission, user_data, post_data):
    """
    Processes a single submission, extracting data and comments.
    """
    user_info = None  # Initialize user_info to ensure it is available later
    author_name = submission.author.name if submission.author else 'Deleted'

    if author_name != 'Deleted':
        user_info = fetch_user_info(reddit, author_name, config)  # Corrected order: reddit, author_name, config
        logger.debug(f"User info for {author_name}: {user_info}")

    comments_data = fetch_and_process_comments(reddit, submission)
    logger.debug(f"Comments for {submission.id}: {comments_data}")
    for comment in tqdm(comments_data, desc=f"Processing comments for {submission.id}"):
        comment_author = comment['author']
        logger.debug(f"Comment author: {comment_author}")
        if comment_author != 'Deleted' and comment_author not in user_data:
            # Corrected order of arguments
            comment_user_info = fetch_user_info(reddit, comment_author, config)
            logger.debug(f"Comment user info: {comment_user_info}")
            if comment_user_info:
                user_data[comment_author] = comment_user_info
                logger.debug(f"Added comment user info for {comment_author}")

    post_data[submission.id] = {
        'User': author_name,
        'title': submission.title,
        'score': submission.score,
        'id': submission.id,
        'url': submission.url,
        'created_utc': submission.created_utc,
        'comments': comments_data,
    }
    logger.debug(f"Processed submission {submission.id}")

    # Only add user_info if it has been set
    if user_info:
        user_data[author_name] = user_info
        logger.debug(f"Added user info for {author_name}")

def run_scraper():
    """
    Main function to run the scraper.
    """
    reddit, config = setup_reddit()
    if not reddit:
        logger.error("Scraping aborted due to configuration errors.")
        return
    logger.debug(f"Fetching posts from {config['subreddit']}")
    posts = fetch_posts(reddit, config)
    user_data = {}
    post_data = {}
    logger.debug(f"Found {len(posts)} posts.")
    for submission in tqdm(posts, desc="Processing submissions"):
        process_submission(config, reddit, submission, user_data, post_data)
        logger.debug(f"Processed submission {submission.id}")

    # Saving logic here
    data_analysis_dir = os.path.join('analysis_results')
    logger.debug(f"Data analysis directory: {data_analysis_dir}")
    if not os.path.exists(data_analysis_dir):
        logger.debug("Data analysis directory does not exist, creating...")
        os.makedirs(data_analysis_dir)
        logger.debug(f"Created directory {data_analysis_dir}")

    user_data_file_path = os.path.join(data_analysis_dir, 'user_data.json')
    logger.debug(f"User data file path: {user_data_file_path}")
    with open(user_data_file_path, 'w', encoding='utf-8') as user_file:
        logger.debug(f"Writing user data to {user_data_file_path}")
        json.dump(user_data, user_file, ensure_ascii=False, indent=4)
        logger.debug(f"Saved user data to {user_data_file_path}")

    post_data_file_path = os.path.join(data_analysis_dir, 'submission_data.json')
    logger.debug(f"Post data file path: {post_data_file_path}")
    with open(post_data_file_path, 'w', encoding='utf-8') as submission_file:
        logger.debug(f"Writing submission data to {post_data_file_path}")
        json.dump(post_data, submission_file, ensure_ascii=False, indent=4)
        logger.debug(f"Saved submission data to {post_data_file_path}")

    logger.debug(f"Current working directory: {os.getcwd()}")

if __name__ == "__main__":
    run_scraper()
    logger.info('Scraping complete.')
