import json
import datetime as dt
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet  # noqa: F401
import pandas as pd
import psycopg2
from tqdm import tqdm
from data_analysis.cal_acc_age import calculate_account_age
from data_analysis.id_low_karma import identify_low_karma_accounts
from data_analysis.id_young_acc import identify_young_accounts
from tools.config.logger_config import init_logger
import logging

logger = logging.getLogger(__name__)
logger.info("User analysis Basic logging set")
init_logger()

def load_config():
    """
    The `load_config` function loads the configuration from a JSON file.
    """
    with open('tools/config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info("Config loaded")
    return config

def connect_to_database(config):
    """
    The `connect_to_database` function connects to a PostgreSQL database using the provided configuration.
    """
    try:
        return psycopg2.connect(
            dbname=config['database']['dbname'],
            user=config['database']['user'],
            password=config['database']['password'],
            host=config['database']['host'],
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.info("Database connection successful")
        return None

def fetch_users(conn):
    """
    The `fetch_users` function retrieves users data from a database using a cursor and logs
    relevant information.
    """
    try:
        with conn.cursor() as cur:
            # Corrected SQL query that performs a left join and aggregates data correctly
            cur.execute("""
                SELECT
                    users.username,
                    users.karma,
                    users.awardee_karma,
                    users.awarder_karma,
                    users.total_karma,
                    users.has_verified_email,
                    users.link_karma,
                    users.comment_karma,
                    users.accepts_followers,
                    users.created_utc,
                    users.dormant_days,
                    array_agg(submissions.created_utc ORDER BY submissions.created_utc) AS post_times
                FROM users
                LEFT JOIN submissions ON users.username = submissions.user_username
                GROUP BY users.username
            """)
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching users from database: {e}")
        return []

def analyze_burst_activity(post_times, config):
    """
    Analyzes the burst activity of a user by comparing the time differences between consecutive posts,
    adjusted to handle TimedeltaIndex with iloc.
    """
    # Fetch period values from the config
    inactivity_days = config.get('inactivity_period', 30)  # Default to 30 if not set
    burst_days = config.get('burst_period', 2)  # Default to 2 if not set

    # Define inactivity and burst activity periods using values from the config
    inactivity_period = pd.to_timedelta(f"{inactivity_days} days")
    burst_period = pd.to_timedelta(f"{burst_days} days")

    # Filter out None values and ensure the list is not empty
    if not post_times or all(x is None for x in post_times):
        return False

    # Convert to pandas datetime series and drop any NaT or NaN entries
    times = pd.to_datetime(post_times, unit='s').dropna()

    # Ensure times is not empty and has valid datetime entries
    if times.empty:
        return False

    # Calculate time differences between consecutive timestamps and convert to Series
    time_diffs = pd.Series(times.diff()[1:])  # Skip the first entry which is NaT

    # Check for burst activity
    burst_activity_exists = False
    for i in range(len(time_diffs) - 1):
        if time_diffs.iloc[i] > inactivity_period:
            # Check if the following entries are within the burst period
            for j in range(1, len(time_diffs) - i):
                if time_diffs.iloc[i + j] < burst_period:
                    burst_activity_exists = True
                    break
            if burst_activity_exists:
                break

    return burst_activity_exists

# Example usage (commented out for now):
# config = {"inactivity_period": 30, "burst_period": 2}
# post_times = [1609459200, 1612137600, 1612224000]  # Unix timestamps
# print(analyze_burst_activity_fixed(post_times, config))


def analyze_users(users, config):
    """
    Analyzes users and returns a list of dictionaries containing user data.
    """
    logger.info("Analyzing users")
    results = []
    for user in tqdm(users, desc=f"Analyzing users ({len(users)})"):
        # Each 'user' is a list or tuple with the correct order of values
        # Adjust the unpacking according to the actual structure of 'user'
        username, karma, awardee_karma, awarder_karma, total_karma, has_verified_email, link_karma,\
            comment_karma, accepts_followers, created_utc, dormant_days, post_times = user

        account_age_years = calculate_account_age(created_utc)
        criteria_met_age = identify_young_accounts(account_age_years, config)
        criteria_met_karma = identify_low_karma_accounts(total_karma, config)
        criteria_met = criteria_met_age or criteria_met_karma

        # New burst activity analysis
        burst_activity = analyze_burst_activity(post_times, config)
        logger.info(f"Burst activity for {username}: {burst_activity}")

        user_data = {
            'Username': username,
            'Karma': karma,
            'Awardee Karma': awardee_karma,
            'Awarder Karma': awarder_karma,
            'Has Verified Email': 'Yes' if has_verified_email else 'No',
            'Link Karma': link_karma,
            'Comment Karma': comment_karma,
            'Accepts Followers': 'Yes' if accepts_followers else 'No',
            'Account Created': dt.datetime.fromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S')\
                if created_utc else 'Unknown',
            'Dormant Days': dormant_days,
            'Account Age': account_age_years,
            'Total Karma': total_karma,
            'Low Karma': 'Low Karma' if criteria_met_karma else '',
            'Criteria': 'Criteria Met' if criteria_met else 'Not Met',
            'Young Account': 'Young Account' if criteria_met_age else '',
            'Burst Activity': 'Yes' if burst_activity else 'No',  # Add burst activity to the results
        }
        results.append(user_data)
        logger.info("Analyzed users")
    return results

def write_to_excel(analyzed_users, file_path):
    """
    Writes user data to an Excel file.
    """
    logger.info("Writing users analysis results to Excel file")
    workbook = Workbook()
    sheet = workbook.active
    if not sheet:
        sheet = workbook.create_sheet(title="User Data Analysis")
    else:
        sheet.title = "User Data Analysis"

    headers = ["Username", "Karma", "Awardee Karma", "Awarder Karma", "Has Verified Email", 
                "Link Karma", "Comment Karma", "Accepts Followers", "Account Created", 
                "Account Age", "Total Karma", "Low Karma", "Criteria", "Young Account", 
                "Dormant Days", "Burst Activity"]
    sheet.append(headers)

    # Append each user's data to the sheet
    for user_data in analyzed_users:
        row = [user_data.get(header, "N/A") for header in headers]  # Use .get() to handle missing keys safely
        sheet.append(row)

    workbook.save(file_path)
    logger.info(f"User analysis results saved to {file_path}")

    def validate_data(headers, analyzed_users):
        return [header for header in headers if header not in analyzed_users[0]]

    if missing_data := validate_data(headers, analyzed_users):
        logger.error(f"Missing data detected: {missing_data}")
        # Handle missing data (e.g., raise an exception, skip writing, write defaults, etc.)
        raise ValueError("Some user data entries are missing expected keys.")

    for user_data in analyzed_users:
        row = [user_data[header] for header in headers]  # Using direct access instead of .get() to force an error if key is missing
        sheet.append(row)
        logger.debug(f"User data for Excel row: {user_data}")

    workbook.save(file_path)
    logger.info(f"Users analysis results saved to {file_path}")

def user_analysis():
    """
    The `user_analysis` function orchestrates the user data analysis process.
    """
    logger.info("Starting user analysis")
    # Load the configuration file and connect to the database
    config = load_config()
    if conn := connect_to_database(config):
        users = fetch_users(conn)
        analyzed_users = analyze_users(users, config)
        write_to_excel(analyzed_users, 'analysis_results/users_analysis.xlsx')
        conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    user_analysis()
    logger.info("User analysis completed.")