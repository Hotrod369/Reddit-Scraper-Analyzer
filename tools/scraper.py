import json
import os
import datetime as dt
import prawcore
from tools.config.logger_config import init_logger
from tools.config.reddit_login import load_config, login
import logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

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
    Fetches posts from each subreddit based on the sorting method and limit specified in the configuration.
    """
    logger.info("Fetching posts...")
    subreddit_names = config["subreddit"].split('+')
    post_sort = config.get("post_sort", {"method": "top", "limit": 100})
    sort_method = post_sort["method"]
    posts_limit = post_sort["limit"]
    all_posts = []

    for subreddit_name in subreddit_names:
        subreddit = reddit.subreddit(subreddit_name)
        logger.info(f"Fetching {sort_method} posts from {subreddit_name} with limit {posts_limit}.")
        
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
    
    return all_posts


def fetch_user_info(reddit, username):
    """
    Fetches user info from Reddit's API.
    """
    logger.debug(f"Fetching user info for: {username}")
    user = reddit.redditor(username)
    # Check if the user exists
    if not user:
        return None

    if username.lower() == 'deleted':  # Handle deleted users before making API calls
        logger.info(f"User '{username}' is deleted, skipping.")
        return None

    try:
        # Check if the user has a creation date
        if not hasattr(user, 'created_utc'):
            logger.error(f"User '{username}' has no creation date.")
            return None
        user_data = {
            'username': username,
            'Karma': user.link_karma + user.comment_karma,
            'created_utc': user.created_utc,
            'user_is_verified': user.is_verified if hasattr(user, 'is_verified') else False,
            'awardee_karma': user.awardee_karma,
            'awarder_karma': user.awarder_karma,
            'total_karma': user.total_karma,
            'has_verified_email': user.has_verified_email if hasattr(user, 'has_verified_email') else False,
            'link_karma': user.link_karma,
            'comment_karma': user.comment_karma,
            'accept_followers': user.accept_followers if hasattr(user, 'accept_followers') else False,
        }
        logger.debug(f"{reddit, username}Fetched User Info.")
        return user_data
    except prawcore.exceptions.NotFound:
        logger.error(f"User '{username}' not found.")
        return None
    except Exception as e:
        logger.error(f"Error fetching user info for '{username}': {e}")
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
    logger.info(f"Fetching posts from {config['subreddit']}")
    posts = fetch_posts(reddit, config)
    user_data = {}
    post_data = {}
    logger.info(f"Found {posts} posts.")
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
    
    logger.info(f"Current working directory: {os.getcwd()}")


    logger.info('Scraping complete.')

if __name__ == "__main__":
    run_scraper()
    logger.info("Exiting...")
