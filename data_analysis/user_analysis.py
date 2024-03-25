import json
import datetime as dt
import json
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
import pandas as pd
import psycopg2
from data_analysis.cal_acc_age import calculate_account_age
from data_analysis.id_low_karma import identify_low_karma_accounts
from data_analysis.id_young_acc import identify_young_accounts
from tools.config.logger_config import init_logger
import logging

logger = logging.getLogger(__name__)
init_logger()

def load_config(logger):
    with open('tools/config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info("Config loaded")
    return config

def connect_to_database(config):
    try:
        return psycopg2.connect(
            dbname=config['database']['dbname'],
            user=config['database']['user'],
            password=config['database']['password'],
            host=config['database']['host'],
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def fetch_users(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, karma, awardee_karma, awarder_karma, total_karma, has_verified_email,\
                link_karma, comment_karma, accepts_followers, created_utc FROM users")
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching users from database: {e}")
        return []


def analyze_users(users, config):
    results = []
    for user in users:
        # Assuming each 'user' is a list or tuple with the correct order of values
        # Adjust the unpacking according to the actual structure of 'user'
        username, karma, awardee_karma, awarder_karma, total_karma, has_verified_email, link_karma,\
            comment_karma, accepts_followers, created_utc = user

        account_age_years = calculate_account_age(created_utc)
        criteria_met_age = identify_young_accounts(account_age_years, config)
        criteria_met_karma = identify_low_karma_accounts(total_karma, config)
        criteria_met = criteria_met_age or criteria_met_karma

        user_data = {
            'Username': username,
            'Karma': karma,
            'Awardee Karma': awardee_karma,
            'Awarder Karma': awarder_karma,
            'Has Verified Email': 'Yes' if has_verified_email else 'No',
            'Link Karma': link_karma,
            'Comment Karma': comment_karma,
            'Accepts Followers': 'Yes' if accepts_followers else 'No',
            'Account Created': dt.datetime.fromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M:%S') if created_utc else 'Unknown',
            'Account Age': account_age_years,
            'Total Karma': total_karma,
            'Low Karma': 'Low Karma' if criteria_met_karma else '',
            'Criteria': 'Criteria Met' if criteria_met else 'Not Met',
            'Young Account': 'Young Account' if criteria_met_age else ''
        }
        results.append(user_data)

    return results




def write_to_excel(analyzed_users, file_path):
    workbook = Workbook()
    sheet = workbook.active
    if sheet is None:
        sheet = workbook.create_sheet(title="User Data Analysis")
    else:
        sheet.title = "User Data Analysis"

    # Explicitly cast sheet to Worksheet to satisfy the type checker
    assert isinstance(sheet, Worksheet), "Active sheet is not a Worksheet instance"

    headers = ["Username", "Karma", "Awardee Karma", "Awarder Karma", "Has Verified Email",
            "Link Karma", "Comment Karma", "Accepts Followers", "Account Created", "Account Age",
            "Total Karma", "Low Karma", "Criteria", "Young Account"]
    sheet.append(headers)

    for user_data in analyzed_users:
        row = [user_data.get(header) for header in headers]
        sheet.append(row)

    workbook.save(file_path)
    logger.info(f"Users analysis results saved to {file_path}")



def user_analysis():
    config = load_config(logger)
    if conn := connect_to_database(config):
        users = fetch_users(conn)
        analyzed_users = analyze_users(users, config)
        write_to_excel(analyzed_users, 'analysis_results/users_analysis.xlsx')
        conn.close()
        logger.info("Database connection closed.")




if __name__ == "__main__":
    user_analysis()
    logger.info("User analysis completed.")
