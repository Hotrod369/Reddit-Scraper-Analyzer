import datetime
import json
import psycopg2
from tqdm import tqdm
from tools.config.reddit_login import load_config
from tools.config.logger_config import init_logger
import logging

logger = logging.getLogger(__name__)
logger.info("json to db Basic logging set")
init_logger()

# Function to insert users into the database
def insert_users(cur, user_data):
    """
    Inserts users into the users table.
    """
    logger.info("Starting to insert users")
    inserted_usernames = set()
    for username, details in tqdm(user_data.items(), desc="Inserting users"):
        logger.debug(f"Inserting user: {username}")
        cur.execute("BEGIN")  # Start a transaction to ensure atomicity
        try:
            cur.execute("""
                INSERT INTO users (username, karma, awardee_karma, awarder_karma,
                total_karma, has_verified_email, link_karma, comment_karma,
                accepts_followers, created_utc, dormant_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                karma = EXCLUDED.karma,
                awardee_karma = EXCLUDED.awardee_karma,
                awarder_karma = EXCLUDED.awarder_karma,
                total_karma = EXCLUDED.total_karma,
                has_verified_email = EXCLUDED.has_verified_email,
                link_karma = EXCLUDED.link_karma,
                comment_karma = EXCLUDED.comment_karma,
                accepts_followers = EXCLUDED.accepts_followers,
                created_utc = EXCLUDED.created_utc,
                dormant_days = EXCLUDED.dormant_days;
                """, (
                    username, details.get('Karma'), details.get('awardee_karma'),
                    details.get('awarder_karma'), details.get('total_karma'),
                    details.get('has_verified_email'), details.get('link_karma'),
                    details.get('comment_karma'), details.get('accept_followers'),
                    details.get('created_utc'), details.get('dormant_days'),
                )
            )
            inserted_usernames.add(username)
            logger.debug(f"Successfully inserted/updated user: {username}")
        except Exception as e:
            logger.error(f"Error inserting user {username}: {e}")
            cur.execute("ROLLBACK")
            continue
        cur.execute("COMMIT")
    return inserted_usernames

def extract_comment_authors(submission_data):
    """
    Extracts comment authors from the submission data and returns a dict
    """
    comment_authors = {}
    try:
        for submission_id, submission in tqdm(submission_data.items(), desc="Extracting comment authors"):
            logger.info("Extracting comment authors from submissions")
            # Extract the comment authors from the submission data, and add them to
            # the comment_authors dict if they don't exist yet
            comments = submission.get('comments', [])
            for comment in comments:
                author = comment['author']
                if author not in comment_authors:
                    comment_authors[author] = {
                        'Karma': None,
                        'awardee_karma': 0,
                        'awarder_karma': 0,
                        'total_karma': 0,
                        'has_verified_email': False,
                        'link_karma': 0,
                        'comment_karma': 0,
                        'accept_followers': False,
                        'created_utc': datetime.datetime.now().timestamp()
                    }
                    logger.debug(f"Added author {author} to comment_authors")
    except Exception as e:
        logger.error(f"Error extracting comment authors: {e}")
    return comment_authors

def insert_submissions(cur, user_data, submission_data):
    """
    Inserts submissions into the submissions table.
    This function assumes that the user_data and submission_data dicts have been
    """
    logger.info("Inserting submissions")
    for submission_id, submission in tqdm(submission_data.items(), desc="Inserting submissions"):
        cur.execute("BEGIN")
        if submission.get("User") not in user_data:
            logger.warning(f"User {submission.get('User')} not found in user data, skipping submission: {submission_id}")
            cur.execute("ROLLBACK")
            continue
        # Insert the submission into the submissions table, or update if it already exists
        try:
            cur.execute("""
                INSERT INTO submissions (id, user_username, title, score, url, created_utc)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                score = EXCLUDED.score,
                url = EXCLUDED.url,
                created_utc = EXCLUDED.created_utc;
                """, (
                    submission_id, submission.get("User"), submission.get("title"),
                    submission.get("score"), submission.get("url"), submission.get("created_utc")
                )
            )
            logger.debug(f"Successfully inserted/updated submission: {submission_id}")
        except Exception as e:
            logger.error(f"Error inserting submission {submission_id}: {e}")
            cur.execute("ROLLBACK")
            continue
        cur.execute("COMMIT")
    logger.info("Finished inserting submissions")

def insert_comments(cur, submission_data, inserted_usernames):
    """
    Inserts comments into the comments table.
    This function assumes that the submission_data dict has been populated with
    """
    logger.info("Inserting comments")
    for submission_id, submission in tqdm(submission_data.items(), desc="Inserting comments"):
        comments = submission.get('comments', [])
        if not comments:
            logger.warning(f"No comments found for submission {submission_id}, skipping")
            continue

        for comment in comments:
            author = comment['author']
            if author not in inserted_usernames:
                logger.warning(f"Author {author} not found in inserted users, skipping comment {comment['id']}")
                continue
            try:
                logger.debug(f"Checking for existing comment: {comment['id']}")
                cur.execute("SELECT id FROM comments WHERE id = %s", (comment['id'],))
                if cur.fetchone():
                    logger.warning(f"Comment {comment['id']} already exists, skipping insert")
                    continue

                logger.info(f"Inserting comment {comment['id']}")
                cur.execute(
                    """
                    INSERT INTO comments (id, author, body, score, submission_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    author = EXCLUDED.author,
                    body = EXCLUDED.body,
                    score = EXCLUDED.score,
                    submission_id = EXCLUDED.submission_id;
                    """,
                    (comment['id'], author, comment['body'], comment['score'], submission_id)
                )
            except psycopg2.IntegrityError as e:
                logger.error(f"Error inserting comment {comment['id']}: {e}")
                cur.execute("ROLLBACK")
                continue
            cur.execute("COMMIT")
    logger.info("Finished inserting comments")

def main():
    """
    Executes the process of extracting data from JSON
    files and inserting it into a PostgreSQL database.
    """
    try:
        # It's better to avoid global when possible,
        #but ensure these are defined in the scope needed.
        global conn, cur
        config = load_config()
        conn = psycopg2.connect(**config['database'])
        cur = conn.cursor()
        logger.info("Loaded config and connected to database")

        with open('analysis_results/user_data.json', 'r', encoding='utf-8') as file:
            user_data = json.load(file)
            logger.debug("Extracted user data from user_data.json")

        with open('analysis_results/submission_data.json', 'r', encoding='utf-8') as file:
            submission_data = json.load(file)
            logger.debug("Extracted submission data from submission_data.json")

        comment_authors = extract_comment_authors(submission_data)
        logger.debug(f"Extracted comment authors: {len(comment_authors)}")
        user_data.update(comment_authors)

        inserted_usernames = insert_users(cur, user_data)
        logger.info("Inserted users")

        insert_submissions(cur, user_data, submission_data)
        logger.info("Inserted submissions")
        insert_comments(cur, submission_data, inserted_usernames)
        logger.info("Inserted comments")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e

    finally:
        cur.close()
        conn.commit()
        conn.close()
        logger.info("Committed data and closed connection")

if __name__ == '__main__':
    main()
    logger.info("Data insertion complete")
