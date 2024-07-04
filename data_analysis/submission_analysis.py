import json
import os
import nltk
import psycopg2
from nltk.sentiment import SentimentIntensityAnalyzer
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from tools.config.logger_config import init_logger
import logging

logger = logging.getLogger(__name__)
logger.info("Submission Analysis Basic logging set")
init_logger()

def load_nltk_data():
    """
    Downloads the required NLTK resources only when
    necessary data is not already downloaded.
    """
    nltk_data_path = './nltk_data'  # Define your local path for NLTK data
    if not os.path.exists(nltk_data_path):
        os.makedirs(nltk_data_path)

    # Ensure NLTK knows where to find the local data
    nltk.data.path.append(nltk_data_path)

    # Load specific resources manually if they are not already downloaded
    if not os.path.exists(os.path.join(nltk_data_path, 'vader_lexicon')):
        nltk.download('vader_lexicon', download_dir=nltk_data_path)

    if not os.path.exists(os.path.join(nltk_data_path, 'tokenizers/punkt')):
        nltk.download('punkt', download_dir=nltk_data_path)

load_nltk_data()

def load_config():
    """
    The `load_config` function reads and loads a JSON configuration file located at
    'tools/config/config.json'.
    """
    with open('tools/config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.debug("Config loaded")
    return config

def connect_to_database(config):
    """
    The function `connect_to_database` establishes a connection to a PostgreSQL database using the
    provided configuration.
    """
    db_config = config['database']
    try:
        conn = psycopg2.connect(
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host']
        )
        logger.info("Connected to the database successfully.")
        return conn
    except psycopg2.DatabaseError as e:
        logger.error(f"Database connection failed: {e}")
        return None

def fetch_data(conn):
    """
    The `fetch_data` function retrieves submissions data from a database using a cursor and logs
    relevant information.
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, user_username, title, score, url FROM submissions")
        submissions = cur.fetchall()
        logger.info("Fetched submissions for analysis.")
        return submissions
    except psycopg2.DatabaseError as e:
        logger.error(f"Error fetching data from database: {e}")
        logger.info("Fetched Submission Info")
        return []

def analyze_data(submissions):
    """
    The `analyze_data` function analyzes the sentiment of titles in submissions and adds a sentiment
    label to the results.
    """
    SIA = SentimentIntensityAnalyzer()
    results = []
    for submission in submissions:
        # The submission tuple is structured as (id, username, title, score, url)
        submission_id, username, title, score, url = submission
        sentiment_score = SIA.polarity_scores(title)['compound']
        # Determine the sentiment label
        if sentiment_score >= 0.05:
            sentiment_label = "Positive"
        elif sentiment_score <= -0.05:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        # Combine the score and label
        sentiment_cell_value = f"{sentiment_score} ({sentiment_label})"
        results.append((submission_id, username, title, score, url, sentiment_cell_value))
    logger.info("Data analysis completed.")
    return results

def write_to_excel(analyzed_data, file_path):
    """
    The function `write_to_excel` writes analyzed data to an Excel file with specified headers and saves
    it to the provided file path.
    """
    workbook = Workbook()
    sheet = workbook.active
    if sheet is None:
        sheet = workbook.create_sheet(title="Submission Data Analysis")
    else:
        sheet.title = "Submission Data Analysis"

    # Explicitly cast sheet to Worksheet to satisfy the type checker
    assert isinstance(sheet, Worksheet), "Active sheet is not a Worksheet instance"
    headers = ["Submission ID", "Username", "Title", "Score",  "URL", "Sentiment Score"]
    sheet.append(headers)

    # Analyzed_data is a list of tuples/lists
    # e.g., [(id1, username1, title1, score1, url1, sentiment1), ...]
    for data in analyzed_data:
        sheet.append(data)

    workbook.save(file_path)
    logger.info(f"Analysis results saved to {file_path}")

def submission_analysis():
    """
    The `submission_analysis` function orchestrates the submission data analysis process.
    """
    logger = init_logger()
    load_nltk_data()
    config = load_config()
    if conn := connect_to_database(config):
        submissions = fetch_data(conn)
        analyzed_data = analyze_data(submissions)
        write_to_excel(analyzed_data, 'analysis_results/submission_analysis.xlsx')
        conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    submission_analysis()
    logger.info("Submission analysis completed.")
