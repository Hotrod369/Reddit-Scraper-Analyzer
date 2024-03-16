import json
import logging
import nltk
import psycopg2
from nltk.sentiment import SentimentIntensityAnalyzer
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

# Initialize Sentiment Analyzer
SIA = SentimentIntensityAnalyzer()

# Load the configuration file
with open('tools/config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    logger.info("Config loaded")
    db_config = config['database']
    logger.info(" sub_sent Database config loaded")

def download_nltk_data():
    """
    This function downloads NLTK data.
    """
    nltk_resources = ['vader_lexicon',
                    'punkt',
                    'averaged_perceptron_tagger',
                    'maxent_ne_chunker',
                    'words'
    ]
    for resource in nltk_resources:
        nltk.download(resource)
    logger.info("NLTK resources downloaded.")

download_nltk_data()

# Calculate average sentiment score for comments in a submission
def calculate_average_sentiment(submissions, titles):
    """
    Calculate the average sentiment score for a list of submission titles.
    """
    try:
        if not submissions:
            return 0  # Avoid division by zero if the list is empty
        scores = [SIA.polarity_scores(titles)['compound'] for _ in titles]
        average_submission_sentiment = sum(scores) / len(scores) if scores else 0
        logger.info(f"Calculated average sentiment score for submissions: {average_submission_sentiment}")
        return average_submission_sentiment
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return 0  # Return a neutral sentiment in case of an error