"""
The code sets up a Python package with logging, console script entry point, and downloads NLTK
resources for natural language processing tasks.
"""
from setuptools import setup, find_packages
import subprocess
import nltk
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()


setup(
    name="your_package_name",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "praw>=7.7.1",
        "pandas>=1.3.3",
        "openpyxl>=3.0.9",
        "requests>=2.31.0",
        "nltk>=3.8.1",
        "psycopg2>=2.9.9",
        # Add other dependencies here
    ],
    entry_points={
        "console_scripts": [
            "your_console_script=your_package.module:function",
        ],
    },
)
def download_nltk_data():
    """
    The function `download_nltk_data` downloads specified NLTK resources for natural language processing
    tasks.
    """
    try:
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
    except ImportError as e:
        logger.error(f"Error downloading NLTK resources: {e}")
        subprocess.run(["python", "-m", "nltk.downloader", "all" ])


if __name__ == "__main__":
    download_nltk_data()