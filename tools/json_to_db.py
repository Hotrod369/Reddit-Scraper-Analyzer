import datetime
import json
import os
import psycopg2
from tools.config.logger_config import init_logger, logging

# Set up logging
global logger
logger = logging.getLogger(__name__)
logger.info("json_to_db Main logging set")


# ISO8601 to UNIX Timestamp Conversion Function
def iso8601_to_unix_timestamp(iso8601_str):
    if not isinstance(iso8601_str, str):
        logger.error(f"json_to_db Expected a string for ISO 8601 conversion, got: {type(iso8601_str)}")
        return None
    try:
        dt_obj = datetime.datetime.fromisoformat(iso8601_str)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)
            return int(dt_obj.timestamp())
    except ValueError as e:
        logger.error(f"json_to_db Invalid ISO 8601 datetime string: {iso8601_str}, error: {e}")
        return None


    # Function to Insert Users
def insert_users(user_data):
    global inserted_users
    inserted_users = set()
    logger.info("json_to_db Inserting users into the users table")
    for username, details in user_data.items():
    # Previous checks and insert logic
        try:
            cur.execute("""
                INSERT INTO users (username, karma, created_utc)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING;
                """,
                (username, details.get('Karma'), details.get('created_utc'))
                # Your existing SQL insert command
            )
            inserted_users.add(username)
            logger.info(f"Number of users inserted: {len(inserted_users)}")
        except Exception as e:
            logger.error(f"Error inserting user {username}: {e}")
    conn.commit()
    return inserted_users

    # Function to Insert Submissions and Associated Comments
def insert_submissions(inserted_users, user_data, submission_data):
    logger.info("json_to_db Inserting submissions and comments")
    try:
        inserted_users = set(user_data.keys())  # Start with users from user_data.json
        logger.info("json_to_db Inserting submissions and comments")
        for submission_id, submission in submission_data.items():
            if submission.get("User") not in inserted_users:
                logger.warning(f"json_to_db User {inserted_users} not found in inserted users, skipping submission: {submission_data}")
    except Exception as e:
        logger.error(f"json_to_db Error inserting submissions: {e}")
        conn.rollback()  # Rollback if an error occurs
        return None
    try:
        cur.execute(
            """
            INSERT INTO submissions (id, user_username, title, score, url, created_utc, awardee_karma,
            awarder_karma, total_karma, has_verified_email, link_karma, comment_karma, accepts_followers)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                awardee_karma = EXCLUDED.awardee_karma,
                awarder_karma = EXCLUDED.awarder_karma,
                total_karma = EXCLUDED.total_karma,
                has_verified_email = EXCLUDED.has_verified_email,
                link_karma = EXCLUDED.link_karma,
                comment_karma = EXCLUDED.comment_karma,
                accepts_followers = EXCLUDED.accepts_followers;
            """,
            (
                submission_id, submission.get("User"), submission.get("title"),
                submission.get("score"), submission.get("url"), submission.get("created_utc"),
                submission.get("awardee_karma", 0), submission.get("awarder_karma", 0),
                submission.get("total_karma", 0), submission.get("has_verified_email", False),
                submission.get("link_karma", 0), submission.get("comment_karma", 0),
                submission.get("accepts_followers", False)
            )
        )
        logger.info(f"Inserted submission: {submission_id}")

        conn.commit()  # Commit after processing each submission to ensure data integrity

        logger.info("json_to_db Finished inserting submissions")
    except Exception as e:
        logger.error(f" json_to_db Error inserting submissions: {e}")
        conn.rollback()  # Rollback if an error occurs
        return None

def insert_comments(submission_data):
    logger.info("Starting to insert comments")
    for submission_id, submission in submission_data.items():
        comments = submission.get('comments', [])
        if not comments:
            logger.info(f"No comments found for submission {submission_id}")
            continue

        for comment in comments:
            try:
                logger.debug(f"Inserting comment: {comment}")
                cur.execute(
                    """
                    INSERT INTO comments (id, author, body, score, submission_id)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (comment['id'], comment['author'], comment['body'], comment['score'], submission_id)
                )

                logger.info(f"Successfully inserted comment {comment['id']} for submission {submission_id}")
            except Exception as e:
                logger.error(f"Error inserting comment {comment['id']} for submission {submission_id}: {e}")
                continue
    conn.commit()

def main():
    try:
        logger.info("json_to_db Starting")
        # Load the configuration file
        logger.info("json_to_db Loading config file")
        with open('tools/config/config.json', 'r', encoding='utf-8') as f:
            logger.info("json_to_db Config file loaded")
            config = json.load(f)
            logger.info("json_to_db Config loaded")
            db_config = config['database']
            logger.info("json_to_db Database config loaded")

        # Load JSON data
        with open('analysis_results/user_data.json', 'r', encoding='utf-8') as file:
            user_data = json.load(file)
            logger.debug("json_to_db User data loaded from user_data.json")

        with open('analysis_results/submission_data.json', 'r', encoding='utf-8') as file:
            submission_data = json.load(file)
            logger.debug("json_to_db Submission data loaded from submission_data.json")

        # Connect to the database
        global conn
        global cur
        conn = psycopg2.connect(dbname=db_config['dbname'], user=db_config['user'], password=db_config['password'], host=db_config['host'])
        cur = conn.cursor()
        logger.info("json_to_db Database connection established")

        init_logger()
        insert_users(user_data)
        insert_submissions(inserted_users, user_data, submission_data)
        insert_comments(submission_data)
    except Exception as e:
        logger.error(f"json_to_db Error: {e}")
        return None

    # Close connection
    cur.close()
    conn.close()
    logger.info("Data insertion complete")

if __name__ == '__main__':
    main()