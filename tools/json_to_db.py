import asyncio
import json
import asyncpg
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("json_to_db Basic logging set")
init_logger()

def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load data from redditor_data.json
redditor_data_path = 'analysis_results/redditor_data.json'
redditor_data = load_json_data(redditor_data_path)

# Load data from submission_data.json
submission_data_path = 'analysis_results/submission_data.json'
submission_data = load_json_data(submission_data_path)

# Asynchronous function to insert redditors into the database
async def insert_redditors(conn, redditor_data):
    """
    Inserts or updates redditor data into the database.

    This function iterates through the provided redditor data and inserts or updates
    corresponding records in the 'users' table. It handles potential
    UniqueViolationErrors during insertion.
    
    Args:
        conn: An asyncpg connection object.
        redditor_data (dict): A dictionary containing redditor data.

    Returns:
        set: A set containing the successfully inserted redditor_ids.
    """
    inserted_redditors = set()
    redditor_records = []

    # 1. Collect all redditor records
    for redditor, details in redditor_data.items():
        redditor_id = details.get('redditor_id')
        if not redditor_id:
            logger.warning(f"Skipping redditor {redditor} due to missing redditor_id.")
            continue
        
        # Build the tuple of 13 values
        redditor_records.append((
            redditor_id,
            details.get('redditorname'),
            details.get('created_utc'),
            details.get('link_karma'),
            details.get('comment_karma'),
            details.get('total_karma'),
            details.get('is_employee'),
            details.get('is_mod'),
            details.get('is_gold'),
            details.get('dormant_days'),
            details.get('has_verified_email'),
            details.get('accept_followers'),
            details.get('redditor_is_subscriber'),
        ))
        
        # Track this redditor in our set
        inserted_redditors.add(redditor)

    # 2. Perform one batch insertion if we have records
    if redditor_records:
        logger.info(f"Batch inserting {len(redditor_records)} redditors into 'users' table.")
        try:
            await conn.executemany(
                """
                INSERT INTO users (
                    redditor_id, redditor, created_utc, link_karma, comment_karma, total_karma,
                    is_employee, is_mod, is_gold, dormant_days, has_verified_email,
                    accepts_followers, redditor_is_subscriber
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (redditor_id) DO UPDATE SET
                    redditor = EXCLUDED.redditor,
                    created_utc = EXCLUDED.created_utc,
                    link_karma = EXCLUDED.link_karma,
                    comment_karma = EXCLUDED.comment_karma,
                    total_karma = EXCLUDED.total_karma,
                    is_employee = EXCLUDED.is_employee,
                    is_mod = EXCLUDED.is_mod,
                    is_gold = EXCLUDED.is_gold,
                    dormant_days = EXCLUDED.dormant_days,
                    has_verified_email = EXCLUDED.has_verified_email,
                    accepts_followers = EXCLUDED.accepts_followers,
                    redditor_is_subscriber = EXCLUDED.redditor_is_subscriber;
                """,
                redditor_records
            )
        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error(f"Error in batch insertion: {e}")
    else:
        logger.warning("No valid redditor records found. Skipping insertion.")

    return inserted_redditors

async def insert_submissions(conn, redditor_data, submission_data):
    """
    Inserts submissions into the submissions table.
    """
    logger.info("Inserting submissions")
    # 1. Check if redditor exists in redditor_data
    for submission_id, submission in submission_data.items():
        if submission.get("author") not in redditor_data:
            logger.warning(f"redditor {submission.get('author')} not found in redditor data, skipping submission: {submission_id}")
            continue
        try:
            await conn.executemany(
                """
                INSERT INTO submissions (
                    submission_id,
                    author,
                    title,
                    submission_score,
                    url,
                    submission_created_utc,
                    over_18
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (submission_id) DO UPDATE SET
                    author = EXCLUDED.author,
                    title = EXCLUDED.title,
                    submission_score = EXCLUDED.submission_score,
                    url = EXCLUDED.url,
                    submission_created_utc = EXCLUDED.submission_created_utc,
                    over_18 = EXCLUDED.over_18;
                """,
                [
                    (
                        submission_id,
                        submission.get("author"),
                        submission.get("title"),
                        submission.get("submission_score"),
                        submission.get("url"),
                        submission.get("submission_created_utc"),
                        submission.get("over_18")
                    )
                    for submission_id, submission in submission_data.items()
                ]
            )
        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error(f"Error inserting submission {submission_id}: {e}")
            await conn.rollback()  # Rollback for this error and continue
    logger.info("Finished inserting submissions")

async def insert_comments(conn, submission_data, inserted_redditors):
    """
    Inserts comments into the comments table.
    """
    logger.info("Inserting comments")
    for submission_id, submission in submission_data.items():
        comments = submission.get('comments', [])
        if not comments:
            continue

        for comment in comments:
            comment_author = comment['comment_author']
            comment_id = comment['comment_id']
            if comment_author not in inserted_redditors:
                logger.warning(f"Author {comment_author} not found in inserted redditors, skipping comment {comment_id}")
                continue
            try:
                logger.debug(f"Checking for existing comment: {comment_id}")
                existing_comment = await conn.fetchrow("SELECT comment_id FROM comments WHERE comment_id = $1", comment_id)
                if existing_comment:
                    logger.warning(f"Comment {comment_id} already exists, skipping insert")
                    continue

                logger.info("Inserting comment")
                await conn.executemany(
                    """
                    INSERT INTO comments (
                        comment_id,
                        comment_author,
                        comment_created_utc,
                        body,
                        comment_score,
                        is_submitter,
                        edited,
                        link_id
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (comment_id) DO UPDATE SET
                        comment_author = EXCLUDED.comment_author,
                        comment_created_utc = EXCLUDED.comment_created_utc,
                        body = EXCLUDED.body,
                        comment_score = EXCLUDED.comment_score,
                        is_submitter = EXCLUDED.is_submitter,
                        edited = EXCLUDED.edited,
                        link_id = EXCLUDED.link_id;
                    """,
                    [
                        (
                            comment['comment_id'],
                            comment['comment_author'],
                            comment['comment_created_utc'],
                            comment['body'],
                            comment['comment_score'],
                            comment['is_submitter'],
                            bool(comment['edited']),  # Ensure edited is a boolean
                            comment['link_id'],
                        )
                        for comment in comments
                    ]
                )
            except asyncpg.exceptions.DataError as e:
                logger.error(f"Error inserting comment {comment_id}: {e}")
                await conn.rollback()  # Rollback for this error and continue
    logger.info("Finished inserting comments")

async def _process_and_insert_data(conn):
    """
    Processes the JSON files and inserts the data into the database.
    """
    logger.info("Processing JSON files for data insertion")
    with open('analysis_results/redditor_data.json', 'r', encoding='utf-8') as file:
        redditor_data = json.load(file)
        logger.debug("Extracted redditor data from redditor_data.json")

    with open('analysis_results/submission_data.json', 'r', encoding='utf-8') as file:
        submission_data = json.load(file)
        logger.debug("Extracted submission data from submission_data.json")

    logger.info("Calling insert_redditors() function...")
    inserted_redditors = await insert_redditors(conn, redditor_data)
    logger.info(f"Inserted redditors: {len(inserted_redditors)}")

    await insert_submissions(conn, redditor_data, submission_data)
    logger.info("Inserted submissions")

    await insert_comments(conn, submission_data, inserted_redditors)
    logger.info("Inserted comments")
    logger.info(f"Total redditors found: {len(redditor_data)}")
    logger.info(f"Total submissions found: {len(submission_data)}")

async def main():
    """
    Executes the process of extracting data from JSON files and inserting it into a PostgreSQL database.
    """
    config = CONFIG['database']
    # Map 'dbname' from the config to 'database' for asyncpg
    conn = await asyncpg.connect(
        user =config['user'],  # Map 'user' to 'redditor'
        password=config['password'],
        database=config['dbname'],  # Map 'dbname' to 'database'
        host=config['host'],
        port=config.get('port', 5432)  # Default to 5432 if port is not provided
    )
    try:
        logger.info("Loaded config and connected to database")
        await _process_and_insert_data(conn)
    except Exception as e:
        logger.exception(f"An error occurred in json_to_db.main: {e}")
        raise
    finally:
        await conn.close()
        logger.info("Committed data and closed connection")

if __name__ == '__main__':
    asyncio.run(main())
    logger.info("Data insertion complete")