import json
import os
import datetime as dt
import time
import prawcore
from tools.config.logger_config import init_logger
from tools.config.reddit_login import load_config, login
import logging

logger = logging.getLogger(__name__)
logger.info("Scraper Basic logging set")
init_logger()

def setup_reddit():
    """
    Sets up the Reddit instance for scraping data, logging in, and loading the target subreddit.
    """
    logger.debug("Setting up Reddit instance...")
    config = load_config()
    reddit = login(config)
    logger.info("Logged into Reddit.")
    return reddit, config

def fetch_posts(reddit, config):
    """
    Fetches posts from each subreddit based on the sorting method and limit specified in the configuration.
    """
    logger.info("Fetching posts...")
    subreddit_names = config["subreddit"].split('+')
    post_sort = config.get("post_sort", {"method": "top", "limit": 1000})
    sort_method = post_sort["method"]
    posts_limit = post_sort["limit"]
    all_posts = []

    for subreddit_name in subreddit_names:
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
        except prawcore.exceptions.Redirect:
            logger.error(f"Failed to fetch posts from '{subreddit_name}'. This may be due to a typo in the subreddit name, the subreddit being private, banned, or non-existent. Please check the subreddit name in the config file.")
            continue
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching posts from '{subreddit_name}': {e}")
            continue

    return all_posts


def fetch_user_info(reddit, username):
    """
    Fetches user info from Reddit's API.
    """
    logger.debug(f"Fetching user info for: {username}")

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
        if not hasattr(user, 'created_utc'):
            logger.error(f"User '{username}' has no creation date.")
            return None

        creation_time = user.created_utc

        # Get the oldest of the first 1000 comments and submissions
        comments = list(user.comments.new(limit=1000))
        submissions = list(user.submissions.new(limit=1000))

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
    except Exception as e:
        logger.error(f"Error while fetching user info for '{username}': {e}")
        return None


def fetch_and_process_comments(reddit, submission):
    """
    Fetches and processes comments for a given submission on Reddit.
    """
    submission.comments.replace_more(limit=None)
    logger.debug(f"Processing comments for submission {submission.id}")
    return [
        {
            'author': comment.author.name if comment.author else 'Deleted',
            'body': comment.body,
            'score': comment.score,
            'id': comment.id,
        }
        for comment in submission.comments.list()
        if comment.author and comment.author.name.lower() != "automoderator"
        and comment.author.name.lower() != "reddit"
    ]


def process_submission(reddit, submission, user_data, post_data):
    """
    Processes a single submission, extracting data and comments.
    """
    user_info = None  # Initialize user_info to ensure it is available later
    author_name = submission.author.name if submission.author else 'Deleted'

    if author_name != 'Deleted':
        user_info = fetch_user_info(reddit, author_name)
        logger.debug(f"User info for {author_name}: {user_info}")

    comments_data = fetch_and_process_comments(reddit, submission)
    logger.debug(f"Comments for {submission.id}: {comments_data}")
    for comment in comments_data:
        comment_author = comment['author']
        logger.debug(f"Comment author: {comment_author}")
        if comment_author != 'Deleted' and comment_author not in user_data:
            comment_user_info = fetch_user_info(reddit, comment_author)
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
    logger.debug(f"Fetching posts from {config['subreddit']}")
    posts = fetch_posts(reddit, config)
    user_data = {}
    post_data = {}
    logger.debug(f"Found {posts} posts.")
    for submission in posts:
        process_submission(reddit, submission, user_data, post_data)
        logger.debug(f"Processed submission {submission.id}")

    # Saving logic here
    data_analysis_dir = os.path.join('analysis_results')
    logger.debug(f"Data analysis directory: {data_analysis_dir}")
    if not os.path.exists(data_analysis_dir):
        logger.debug("Data analysis directory does not exist, creating...")
        # Create the directory if it doesn't exist already
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
