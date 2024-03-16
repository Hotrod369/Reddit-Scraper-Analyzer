import nltk
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()


def download_nltk_data():
    """
    The function `download_nltk_data` downloads specified NLTK resources for natural language processing
    tasks.
    """
    # List of NLTK resources to download
    resources = [
        'vader_lexicon',
        'punkt',
        'averaged_perceptron_tagger',
        'maxent_ne_chunker',
        'words',# For sentiment analysis
        # Add any other NLTK resources needed for your application
    ]

    for resource in resources:
        print(f"Downloading NLTK resource: {resource}...")
        nltk.download(resource)

    logger.info("NLTK resources have been downloaded.")

if __name__ == "__main__":
    download_nltk_data()
