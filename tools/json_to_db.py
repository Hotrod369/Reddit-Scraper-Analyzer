import datetime
import json
import os
import psycopg2
from tools.config.reddit_login import load_config
from tools.config.logger_config import init_logger
import logging


logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()


# Function to insert users into the database
def insert_users(cur, user_data):
    logger.info("Starting to insert users")
    inserted_usernames = set()
    for username, details in user_data.items():
        logger.info(f"Inserting user: {username}")
        cur.execute("BEGIN")  # Start a transaction to ensure atomicity
        try:
            cur.execute("""
                INSERT INTO users (username, karma, awardee_karma, awarder_karma, total_karma,
                has_verified_email, link_karma, comment_karma, accepts_followers, created_utc)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                karma = EXCLUDED.karma,
                awardee_karma = EXCLUDED.awardee_karma,
                awarder_karma = EXCLUDED.awarder_karma,
                total_karma = EXCLUDED.total_karma,
                has_verified_email = EXCLUDED.has_verified_email,
                link_karma = EXCLUDED.link_karma,
                comment_karma = EXCLUDED.comment_karma,
                accepts_followers = EXCLUDED.accepts_followers,
                created_utc = EXCLUDED.created_utc;
                """, (
                    username, details.get('Karma'), details.get('awardee_karma'),
                    details.get('awarder_karma'), details.get('total_karma'),
                    details.get('has_verified_email'), details.get('link_karma'),
                    details.get('comment_karma'), details.get('accept_followers'),
                    details.get('created_utc')
                )
            )
            inserted_usernames.add(username)
            logger.info(f"Successfully inserted/updated user: {username}")
        except Exception as e:
            logger.error(f"Error inserting user {username}: {e}")
        conn.commit()
    return inserted_usernames

def extract_comment_authors(submission_data):
    try:
        comment_authors = {}
        for submission_id, submission in submission_data.items():
            logger.info(f"Extracting comment authors from submission {submission_id}")
            # Extract the comment authors from the submission data, and add them to the comment_authors dict if they don't exist yet
            comments = submission.get('comments', [])
            logger.info(f"Found {len(comments)} comments in submission {submission_id}")
            for comment in comments:
                logger.info(f"Extracting comment authors from comment {comment['id']}")
                author = comment['author']
                logger.info(f"Found author {author} in comment {comment['id']}")
                if author not in comment_authors:
                    logger.info(f"Author {author} not found in comment_authors, adding to dict")
                    comment_authors[author] = {
                        'Karma': None,  # You might need logic to determine actual values
                        'awardee_karma': 0,
                        'awarder_karma': 0,
                        'total_karma': 0,
                        'has_verified_email': False,
                        'link_karma': 0,
                        'comment_karma': 0,
                        'accept_followers': False,
                        'created_utc': datetime.datetime.now().timestamp()  # Placeholder
                    }
                    logger.info(f"Added author {author} to comment_authors")
    except Exception as e:
        logger.error(f"Error extracting comment authors: {e}")
        return comment_authors



def insert_submissions(cur, user_data, submission_data):
    logger.info("Starting to insert submissions")
    for submission_id, submission in submission_data.items():
        cur.execute("BEGIN")
        if submission.get("User") not in user_data:
            logger.warning(f"User {submission.get('User')} not found in user data, skipping submission: {submission_id}")
            cur.execute("ROLLBACK")  # Rollback to end the transaction cleanly
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
            logger.info(f"Successfully inserted/updated submission: {submission_id}")
        except Exception as e:
            logger.error(f"Error inserting submission {submission_id}: {e}")
        conn.commit()
        logger.info("Committing transaction")
    logger.info("Finished inserting submissions")

def insert_comments(cur, submission_data, inserted_usernames):
    logger.info("Starting to insert comments")
    for submission_id, submission in submission_data.items():
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
                    logger.info(f"Comment {comment['id']} already exists, skipping insert")
                    continue

                logger.debug(f"Inserting comment: {comment}")
                cur.execute(
                    """
                    INSERT INTO comments (id, author, body, score, submission_id)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (comment['id'], author, comment['body'], comment['score'], submission_id)
                )
            except psycopg2.IntegrityError as e:
                logger.error(f"Error inserting comment {comment['id']}: {e}")
                conn.rollback()
            else:
                conn.commit()
    logger.info("Finished inserting comments")



def main():
    """
    Executes the process of extracting data from JSON files and inserting it into a PostgreSQL database.
    """
    try:
        global conn, cur  # It's better to avoid global when possible, but ensure these are defined in the scope needed.
        logger.info("Starting json_to_db process")
        config = load_config()
        logger.info("Loaded config")
        conn = psycopg2.connect(**config['database'])
        logger.info("Connected to database")
        cur = conn.cursor()
        logger.info("Created cursor")

        with open('analysis_results/user_data.json', 'r', encoding='utf-8') as file:
            user_data = json.load(file)
            logger.info("Extracted user data from user_data.json:")

        with open('analysis_results/submission_data.json', 'r', encoding='utf-8') as file:
            submission_data = json.load(file)
            logger.info("Extracted submission data from submission_data.json:")

        if comment_authors := extract_comment_authors(submission_data):
            logger.info(f"Extracted comment authors: {len(comment_authors)}")
            user_data.update(comment_authors)
        else:
            logger.info("No additional comment authors found")

        inserted_usernames = insert_users(cur, user_data)
        logger.info("Inserted users")

        # Move the call to extract_comment_authors after insert_users
        if comment_authors := extract_comment_authors(submission_data):
            logger.info(f"Extracted comment authors: {len(comment_authors)}")
            user_data.update(comment_authors)
            inserted_usernames.update(comment_authors.keys())
        else:
            logger.info("No additional comment authors found")

        insert_submissions(cur, user_data, submission_data)
        logger.info("Inserted submissions")
        insert_comments(cur, submission_data, inserted_usernames)
        logger.info("Inserted comments")

    except Exception as e:
        raise e

    cur.close()
    conn.commit()
    logger.info("Committing changes")
    conn.close()
    logger.info("Closing connection")
    logger.info("Data insertion complete")


if __name__ == '__main__':
    main()