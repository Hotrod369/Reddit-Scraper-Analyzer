import asyncpg
import asyncio
import datetime as dt
import pandas as pd
import psycopg2
from tools.config.config_loader import CONFIG
from data_analysis.cal_acc_age import calculate_account_age
from data_analysis.id_low_karma import identify_low_karma_accounts
from data_analysis.id_young_acc import identify_young_accounts
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("User analysis Basic logging set")
init_logger()

async def connect_to_database():
    """Establish asyncpg connection."""
    try:
        cfg = CONFIG['database']
        conn = await asyncpg.connect(
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['dbname'],
            host=cfg['host'],
            port=cfg.get('port', 5432)
        )
        logger.info("Async database connection successful.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

async def fetch_users(conn):
    """
    Retrieves user data from the database using asyncpg.
    """
    query = """
        SELECT
            users.redditor_id,
            users.redditor,
            users.created_utc,
            users.link_karma,
            users.comment_karma,
            users.total_karma,
            users.is_employee,
            users.is_mod,
            users.is_gold,
            users.dormant_days,
            users.has_verified_email,
            users.accepts_followers,
            users.redditor_is_subscriber,
            array_agg(submissions.submission_created_utc
                    ORDER BY submissions.submission_created_utc) AS post_times
        FROM users
        LEFT JOIN submissions
            ON users.redditor_id = submissions.author
        GROUP BY
            users.redditor_id,
            users.redditor,
            users.created_utc,
            users.link_karma,
            users.comment_karma,
            users.total_karma,
            users.is_employee,
            users.is_mod,
            users.is_gold,
            users.dormant_days,
            users.has_verified_email,
            users.accepts_followers,
            users.redditor_is_subscriber
    """
    try:
        rows = await conn.fetch(query)
        logger.info(f"Fetched {len(rows)} users for analysis.")
        return rows
    except asyncpg.PostgresError as pg_err:
        logger.error(f"A PostgreSQL error occurred: {pg_err}")
        return []
    except Exception as e:
        logger.exception(f"An error occurred in fetch_users: {e}")
        return []

def analyze_burst_activity(config, post_times):
    """
    Analyzes the burst activity of a user by comparing the time differences 
    between consecutive posts.
    """
    inactivity_days = config.get('inactivity_period', 30)
    burst_days = config.get('burst_period', 2)
    inactivity_period = pd.to_timedelta(f"{inactivity_days} days")
    burst_period = pd.to_timedelta(f"{burst_days} days")

    if not post_times or all(x is None for x in post_times):
        return False

    times = pd.to_datetime(post_times, unit='s').dropna()
    if times.empty:
        return False

    time_diffs = pd.Series(times.diff()[1:])
    for i in range(len(time_diffs) - 1):
        if time_diffs.iloc[i] > inactivity_period:
            # Check if the subsequent diffs are within burst_period
            for j in range(1, len(time_diffs) - i):
                if time_diffs.iloc[i + j] < burst_period:
                    return True
    return False

def analyze_users(config, users):
    """
    Analyzes user data and returns a list of dictionaries containing user analysis results.
    """
    logger.info("Analyzing users")
    results = []
    for row in users:
        (
            redditor_id,
            redditorname,
            created_utc,
            link_karma,
            comment_karma,
            total_karma,
            is_employee,
            is_mod,
            is_gold,
            dormant_days,
            has_verified_email,
            accepts_followers,
            redditor_is_subscriber,
            post_times
        ) = row

        # Calculate account age
        account_age_years = calculate_account_age(created_utc)

        # Check for low-karma / young account
        low_karma = identify_low_karma_accounts(config, total_karma)
        young_account = identify_young_accounts(account_age_years or 0.0)

        # Check burst activity
        burst_activity = analyze_burst_activity(config, post_times)

        user_data = {
            'User ID': redditor_id,
            'Username': redditorname,
            'Account Created': (
                dt.datetime.fromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S') 
                if created_utc else 'Unknown'
            ),
            'Link Karma': link_karma,
            'Comment Karma': comment_karma,
            'Total Karma': total_karma,
            'Is Employee': 'Yes' if is_employee else 'No',
            'Is Gold': 'Yes' if is_gold else 'No',
            'Dormant Days': dormant_days,
            'Has Verified Email': 'Yes' if has_verified_email else 'No',
            'Accepts Followers': 'Yes' if accepts_followers else 'No',
            'Is Subscriber': 'Yes' if redditor_is_subscriber else 'No',
            'Account Age': account_age_years,
            'Low Karma': 'Low Karma' if low_karma else 'No',
            'Young Account': 'Young Account' if young_account else 'No',
            'Burst Activity': 'Yes' if burst_activity else 'No',
        }
        results.append(user_data)

    return results

async def user_analysis():
    """
    Orchestrates the user data analysis process asynchronously.
    """
    logger.info("Starting user analysis")
    conn = await connect_to_database()  # use asyncpg
    if conn is None:
        logger.error("Could not connect to the database.")
        return

    try:
        # 1. Fetch users
        users = await fetch_users(conn)

        # 2. Analyze
        results = analyze_users(CONFIG, users)

        logger.info(f"Analyzed {len(results)} users.")

        # 3. Possibly do something with `results` 
        #    e.g. store them, log them, or hand off to Excel generation.
        # for row in results:
        #     logger.debug(f"User analysis row: {row}")

    except Exception as e:
        logger.exception(f"An error occurred during user analysis: {e}")
    finally:
        await conn.close()
        logger.info("User analysis completed successfully.")

if __name__ == "__main__":
    asyncio.run(user_analysis())
    logger.info("User analysis completed.")