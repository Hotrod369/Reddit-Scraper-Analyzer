from nltk.sentiment import SentimentIntensityAnalyzer
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()


# Initialize SentimentIntensityAnalyzer
SIA = SentimentIntensityAnalyzer()
logger.info("Initialized the NLTK sentiment analyzer.")
logger.info(type(SIA))  # Log the type of SIA
logger.info(SIA)  # Log the SIA object


def calculate_comment_sentiment(comment, SIA):
    """
    Calculate the sentiment score of a single comment using the
    SentimentIntensityAnalyzer (SIA) from the NLTK library.
    """
    try:
        if body := comment.get("Comment Body", ""):
            sentiment_score = SIA.polarity_scores(body)['compound']
            logger.info(f"Calculated comment Sentiment {sentiment_score} for Comment ID: {comment.get('id')}")
            return sentiment_score
        else:
            # Handle the case where there's no body for the comment
            logger.info(f"No body found for Comment ID: {comment.get('id')}")
            return 0
    except Exception as e:
        logger.warning(f"An error occurred while calculating comment sentiment: {e}")
        return None  # You might choose to return None or another value to indicate failure


# Assuming you have a comment_data dictionary for a single comment
#comment_data = {"id": "12345", "Comment Body": "This is an example comment."}
#comment_sentiment_score = calculate_comment_sentiment(comment_data, SIA)
#print(f"Sentiment Score for Comment ID {comment_data['id']}: {comment_sentiment_score}")
