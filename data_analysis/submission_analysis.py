import json
import psycopg2
from nltk.sentiment import SentimentIntensityAnalyzer
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from tools.config.logger_config import init_logger
import logging

logger = logging.getLogger(__name__)
init_logger()

def download_nltk_data(logger):
    import nltk
    nltk_resources = ['vader_lexicon', 'punkt', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']
    for resource in nltk_resources:
        nltk.download(resource)
    logger.info("NLTK resources downloaded.")

def load_config(logger):
    with open('tools/config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info("Config loaded")
    return config

def connect_to_database(config, logger):
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

def fetch_data(conn, logger):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, user_username, title, score, url FROM submissions")
        submissions = cur.fetchall()
        logger.info("Fetched submissions for analysis.")
        return submissions
    except psycopg2.DatabaseError as e:
        logger.error(f"Error fetching data from database: {e}")
        return []

def analyze_data(submissions, logger):
    SIA = SentimentIntensityAnalyzer()
    results = []
    for submission in submissions:
        # Assuming the submission tuple is structured as (id, username, title, score, url)
        submission_id, username, title, score, url = submission
        sentiment_score = SIA.polarity_scores(title)['compound']
        results.append((submission_id, username, title, score, url, sentiment_score))
    logger.info("Data analysis completed.")
    return results


def write_to_excel(analyzed_data, file_path, logger):
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

    # Assuming analyzed_data is a list of tuples/lists
    # e.g., [(id1, username1, title1, score1, url1, sentiment1), ...]
    for data in analyzed_data:
        sheet.append(data)

    workbook.save(file_path)
    logger.info(f"Analysis results saved to {file_path}")

def submission_analysis():
    logger = init_logger()
    download_nltk_data(logger)
    config = load_config(logger)
    if conn := connect_to_database(config, logger):
        submissions = fetch_data(conn, logger)
        analyzed_data = analyze_data(submissions, logger)
        write_to_excel(analyzed_data, 'analysis_results/submission_analysis.xlsx', logger)
        conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    submission_analysis()
