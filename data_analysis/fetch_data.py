"""
This Python function `fetch_data_from_database()` is responsible for fetching user data, comments data, and submission data from a PostgreSQL database. Here's a breakdown of what the function does:
"""
import json
import pandas as pd
import psycopg2
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()


# Load configuration
with open('tools/config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    logger.info("Loaded the config.json")
    db_config = config["database"]
    logger.info("fetch_user_data Database config loaded")

logger.info("Connecting to the database.")
db_config = config["database"]
try:
    conn = psycopg2.connect(
    dbname=db_config["dbname"],
    user=db_config["user"],
    password=db_config["password"],
    host=db_config["host"],
)
    cur = conn.cursor()
    logger.info("Connected to the database successfully.")
except Exception as e:
    logger.exception(f"Failed to connect to the database: %s {e}")


def fetch_data_from_database():
    # Fetch User data
    cur.execute("SELECT username, karma, created_utc FROM users")

    user_data = {
    username: {
        "Karma": karma,
        "Creation Date": created_utc}
    for username, karma, created_utc in cur.fetchall()
    }
    logger.info(f"Fetched user data {user_data} from the database")

    # Fetch comments for analysis
    cur.execute("SELECT id, author, body, score, submission_id FROM comments")
    comments_data = {
    id: {
        "Author": author,
        "Comment Body": body,
        "Score": score,
        "Submission ID": submission_id,
    }
    for id, author, body, score, submission_id in cur.fetchall()
    }
    logger.info(f"Fetched comments for analysis: {comments_data}")

    # Fetch submission data
    cur.execute(
    "SELECT id, user_username, title, score, url, created_utc, "
    "awardee_karma, awarder_karma, total_karma, has_verified_email, "
    "link_karma, comment_karma, accepts_followers FROM submissions"
    )
    submission_data = {
    id: {
        "User": user_username,
        "Title": title,
        "Score": score,
        "URL": url,
        "Creation Date": created_utc,
        "Awardee Karma": awardee_karma,
        "Awarder Karma": awarder_karma,
        "Total Karma": total_karma,
        "Verified Email": has_verified_email,
        "Link Karma": link_karma,
        "Comment Karma": comment_karma,
        "Accepts Followers": accepts_followers,
    }
    for id, user_username, title, score, url, created_utc, awardee_karma,
    awarder_karma, total_karma, has_verified_email, link_karma,
    comment_karma, accepts_followers in cur.fetchall()
    }
    logger.info(f"Fetched Submission data {submission_data} from database")

    # Create a DataFrame from the user data
    bot_df = pd.DataFrame.from_dict(
    user_data | comments_data | submission_data, orient="index"
    )
    logger.info(f"Created a DataFrame from the user data: {bot_df}")

    return user_data, submission_data, comments_data
