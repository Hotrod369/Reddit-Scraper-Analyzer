from tqdm import tqdm
import asyncio
import json
import os
import time
import prawcore
from prawcore.exceptions import TooManyRequests
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
from tools.config.logger_config import init_logger, logging
from tools.config.reddit_login import load_config, login
from tools.config.config_loader import CONFIG

def trigger_link_karma_fetch(redditor_obj):
    _ = redditor_obj.link_karma  # triggers a fetch

logger = logging.getLogger(__name__)
logger.info("Scraper Basic logging set")
init_logger()

def handle_rate_limit(retry_after):
    if retry_after is None:
        logger.warning("Rate limit exceeded but retry_after time is not set. Using a default sleep of 3 second.")
        time.sleep(3)
    else:
        logger.warning(f"Rate limit exceeded. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after + 2)  # Adding an extra second for safety

# Create a custom session
session = requests.Session()

# Define a retry strategy
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    backoff_factor=1,
    raise_on_status=True,
    raise_on_redirect=True
)

# Create an adapter with the desired connection pool size
adapter = HTTPAdapter(pool_connections=20, pool_maxsize=50, max_retries=retry_strategy)  # type: ignore

# Mount the adapter to the session
session.mount("https://", adapter)
session.mount("http://", adapter)

def setup_reddit():
    """
    Sets up the Reddit instance for scraping data, logging in, and loading the target subreddit.
    """
    logger.debug("Setting up Reddit instance...")
    config = load_config()
    reddit = login(config)
    logger.info("Logged into Reddit.")
    if reddit is None:
        logger.error("Reddit login failed; received None, aborting.")
        raise Exception("Reddit login failed. See logs for details.")
    # Use the Reddit instance to make requests
    subreddit = reddit.subreddit('python')
    for submission in subreddit.hot(limit=10):
        print(submission.title)
    return reddit, config

async def fetch_submissions_async(reddit, config):
    """
    Asynchronous wrapper for fetching submissions.
    This function runs the synchronous fetch_submissions in a thread.
    """
    from functools import partial
    loop = asyncio.get_running_loop()
    # Wrap the synchronous function in a partial to pass the arguments.
    return await loop.run_in_executor(None, partial(fetch_submissions, reddit, config))

def fetch_submissions(reddit, config):
    """
    Synchronous version fetches submissions from each subreddit based on the sorting method and limit specified in the configuration.
    """
    logger.info("Fetching submissions...")
    subreddit_names = config["subreddit"].split('+')
    # Get the submission sort settings
    submission_sort = config.get("submission_sort", {"method": "new", "limit": 250})
    sort_method = submission_sort["method"]
    try:
        submissions_limit = submission_sort["limit"]
        logger.debug(f"Submission sort settings: {config.get('submission_sort')}")
    except (ValueError, TypeError):
        logger.warning("Invalid submission limit value in config. Falling back to default of 10.")
        submissions_limit = 10

    all_submissions = []

    for subreddit_name in tqdm(subreddit_names, desc="Fetching subreddits"):
        logger.info(f"Fetched {len(subreddit_names)} subreddits.")
        try:
            subreddit = reddit.subreddit(subreddit_name)
            logger.debug(f"Fetching {sort_method} submissions from {subreddit_name} with limit {submissions_limit}.")
            if sort_method == "top":
                submissions = subreddit.top(limit=submissions_limit)
            elif sort_method == "hot":
                submissions = subreddit.hot(limit=submissions_limit)
            elif sort_method == "new":
                submissions = subreddit.new(limit=submissions_limit)
            elif sort_method == "rising":
                submissions = subreddit.rising(limit=submissions_limit)
            elif sort_method == "controversial":
                submissions = subreddit.controversial(limit=submissions_limit)
            else:
                raise ValueError(f"Unsupported sort method: {sort_method}")
            all_submissions.extend(submissions)
            time.sleep(2)  # Delay to help avoid rate limits
        except TooManyRequests as e:
            handle_rate_limit(e.response.headers.get('retry-after'))
            continue
        except prawcore.exceptions.Redirect:
            logger.error(f"Failed to fetch submissions from '{subreddit_name}'. Check the subreddit name.")
            continue
        except prawcore.exceptions.RequestException as e:
            logger.error(f"Rate limit exceeded while fetching submissions from '{subreddit_name}': {e}")
            time.sleep(60)
            continue
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching submissions from '{subreddit_name}': {e}")
            continue

    return all_submissions

# Removed duplicate async def fetch_redditor_info_async to resolve the naming conflict.


def fetch_comments_from_submissions(config, redditor):
    if not hasattr(redditor, 'created_utc'):
        logger.error(f"redditor '{redditor}' has no creation date.")
        return None

    # ─────────────── NEW MODERATION CHECK ───────────────
    # If they're a moderator of at least one real subreddit, skip them:
    if redditor.is_mod and getattr(redditor.subreddit, "user_is_moderator"):
        logger.debug(f"Skipping moderator: {redditor.name}")
        return None

    creation_time = redditor.created_utc

    try:
        comments_limit = int(config.get("comments_limit", 250))
        logger.debug(f"Comments limit: {config.get('comments_limit')}, Submissions limit for comments: {config.get('submissions_limit')}")
    except (ValueError, TypeError):
        logger.warning("Invalid comments_limit in config; defaulting to 500.")
        comments_limit = 500

    try:
        submissions_limit = int(config.get("submissions_limit", 100))
    except (ValueError, TypeError):
        logger.warning("Invalid submissions_limit in config; defaulting to 100.")
        submissions_limit = 100

    logger.debug(f"Comments limit: {comments_limit}")
    logger.debug(f"Submissions limit: {submissions_limit}")

    comments = list(redditor.comments.new(limit=comments_limit))
    submissions = list(redditor.submissions.new(limit=submissions_limit))

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

    redditor_data = {
        'redditor_id': redditor.id,
        'redditorname': redditor.name,
        'created_utc': redditor.created_utc,
        'link_karma': redditor.link_karma,
        'comment_karma': redditor.comment_karma,
        'total_karma': redditor.total_karma,
        'is_employee': redditor.is_employee,
        'is_mod': redditor.is_mod,
        'is_gold': redditor.is_gold,
        'dormant_days': dormant_days,
        'has_verified_email': getattr(redditor, 'has_verified_email', False),
        'accept_followers': getattr(redditor, 'accept_followers', False),
        'redditor_is_subscriber': getattr(redditor, 'is_subscriber', False),
    }
    logger.debug(f"Fetched redditor Info for {redditor}.")
    return redditor_data

def fetch_and_process_comments(reddit, submission):
    """
    Fetches and processes comments for a given submission on Reddit.
    """
    try:
        submission.comments.replace_more(limit=None)
        logger.debug(f"Processing comments for submission {submission.id}")
        return [
            {
                'comment_id': comment.id,
                'comment_author': comment.author.name if comment.author else 'Deleted',
                'comment_created_utc': comment.created_utc,
                'body': comment.body,
                'comment_score': comment.score,
                'is_submitter': comment.is_submitter,
                'edited': comment.edited,
                'link_id': comment.link_id[3:] if comment.link_id.startswith("t3_") else comment.link_id
            }
            for comment in tqdm(submission.comments.list(), desc=f"Fetching comments for {submission.id}")
            if comment.author 
                and comment.author.name.lower() != "automoderator"
                and comment.author.name.lower() != "reddit"
        ]
    except TooManyRequests as e:
        handle_rate_limit(e.response.headers.get('retry-after'))
        return []
    except Exception as e:
        logger.error(f"Error fetching comments for submission {submission.id}: {e}")
        return []
    
def _fetch_redditor_info_sync(reddit, config, redditor_name):
    """
    Synchronous helper that does the real PRAW logic.
    """
    logger.debug(f"Fetching redditor info for: {redditor_name}")

    # Quick check for 'deleted'
    if redditor_name.lower() == "deleted":
        logger.debug(f"Redditor '{redditor_name}' is deleted, skipping.")
        return None

    try:
        # 1) Build the PRAW object
        redditor_obj = reddit.redditor(redditor_name)
        try:
            _ = redditor_obj.link_karma  # Force fetch of link_karma
        except AttributeError:
            # If link_karma is missing, log and skip the user.
            logger.error(f"Redditor '{redditor_name}' is missing 'link_karma' attribute; skipping.")
            return None

        redditor_data = fetch_comments_from_submissions(config, redditor_obj)
        if redditor_data:
            redditor_data["redditor_id"] = redditor_obj.id
        return redditor_data
    except prawcore.exceptions.RequestException as e:
        logger.error(f"Rate limit or request error for '{redditor_name}': {e}")
        time.sleep(60)
        return None
    except AttributeError as e:
        logger.error(f"Redditor '{redditor_name}' has an attribute error: {e}")
        return None
    except Exception as e:
        logger.error(f"Redditor '{redditor_name}' not found or error occurred: {e}")
        return None

async def fetch_redditor_info_async(reddit, config, redditor_name, sem):
    """
    Asynchronous wrapper that uses a semaphore to limit concurrency.
    """
    async with sem:
        # Offload the synchronous helper to a thread
        return await asyncio.to_thread(
            _fetch_redditor_info_sync,
            reddit,
            config,
            redditor_name
        )
        
def process_submission(config, reddit, submission, redditor_data, submission_data):
    """
    Processes a single submission, extracting data and comments.
    """
    try:
        redditor_info = None  # Initialize redditor_info to ensure it is available later
        author_name = submission.author.name if submission.author else 'Deleted'
        
        if author_name != 'Deleted':
            redditor_info = _fetch_redditor_info_sync(reddit, config, author_name)  # Corrected order: reddit, config, author_name
            logger.debug(f"redditor info for {author_name}: {redditor_info}")
            if redditor_info:
                redditor_data[author_name] = redditor_info

        comments_data = fetch_and_process_comments(reddit, submission)
        logger.debug(f"Comments for {submission.id}: {comments_data}")
        for comment in comments_data:
            comment_author = comment['comment_author']
            logger.debug(f"Comment author: {comment_author}")
            if comment_author != 'Deleted' and comment_author not in redditor_data:
                comment_redditor_info = _fetch_redditor_info_sync(reddit, config, comment_author)  # Corrected order: reddit, config, comment_author
                logger.debug(f"Comment redditor info: {comment_redditor_info}")
                if comment_redditor_info:
                    redditor_data[comment_author] = comment_redditor_info
                    logger.debug(f"Added comment redditor info for {comment_author}")

        submission_data[submission.id] = {
            'submission_id': submission.id,
            'author': submission.author.name if submission.author else 'Deleted',
            'title': submission.title,
            'submission_score': submission.score,
            'url': submission.url,
            'submission_created_utc': submission.created_utc,
            'over_18': submission.over_18,
            "comments": comments_data,
        }
        logger.debug(f"Processed submission {submission.id}")
    except TooManyRequests as e:
        handle_rate_limit(e.response.headers.get('retry-after'))
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing submission '{submission.id}': {e}")

async def run_scraper_async():
    """
    Asynchronous entry point for the scraper.
    """
    try:
        reddit, config = setup_reddit()

        # Fetch submissions asynchronously (in a background thread)
        submissions = await fetch_submissions_async(reddit, config)
        logger.debug(f"Found {len(submissions)} submissions.")
        redditor_data = {}
        submission_data = {}

        # Create a semaphore to limit the number of concurrent tasks (e.g., 10)
        max_tasks = config.get("max_concurrent_requests", 4)
        semaphore = asyncio.Semaphore(max_tasks)

        # Define an async helper that wraps the synchronous process_submission call.
        async def process_submission_with_semaphore(submission):
            async with semaphore:
                return await asyncio.to_thread(
                    process_submission,
                    config,
                    reddit,
                    submission,
                    redditor_data,
                    submission_data,
                )

        # Build a list of tasks—one for each submission.
        tasks = [
            process_submission_with_semaphore(submission)
            for submission in submissions
        ]

        # Wait for all submission processing tasks to complete.
        await asyncio.gather(*tasks)

        # Once all tasks are complete, save the output as JSON.
        data_analysis_dir = os.path.join('analysis_results')
        logger.debug(f"Data analysis directory: {data_analysis_dir}")
        if not os.path.exists(data_analysis_dir):
            logger.debug("Data analysis directory does not exist, creating...")
            os.makedirs(data_analysis_dir)
            logger.debug(f"Created directory {data_analysis_dir}")

        redditor_data_file_path = os.path.join(data_analysis_dir, 'redditor_data.json')
        logger.debug(f"Redditor data file path: {redditor_data_file_path}")
        with open(redditor_data_file_path, 'w', encoding='utf-8') as redditor_file:
            logger.debug(f"Writing redditor data to {redditor_data_file_path}")
            json.dump(redditor_data, redditor_file, ensure_ascii=False, indent=4)
            logger.debug(f"Saved redditor data to {redditor_data_file_path}")

        submission_data_file_path = os.path.join(data_analysis_dir, 'submission_data.json')
        logger.debug(f"Submission data file path: {submission_data_file_path}")
        with open(submission_data_file_path, 'w', encoding='utf-8') as submission_file:
            logger.debug(f"Writing submission data to {submission_data_file_path}")
            json.dump(submission_data, submission_file, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping: {e}")

#    logger.debug(f"Scraping complete. Processed {len(submissions)} submissions.")


def run_scraper():
    """
    Synchronous wrapper to run the async scraper.
    """
    asyncio.run(run_scraper_async())

if __name__ == "__main__":
    run_scraper()
    logger.info('Scraping complete.')