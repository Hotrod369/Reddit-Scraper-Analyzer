
import json
import nltk
import psycopg2
from nltk import FreqDist, bigrams, ngrams, pos_tag
from nltk.chunk import ne_chunk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()
SIA = SentimentIntensityAnalyzer()

# Load the configuration file
with open('tools/config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    logger.info("Config loaded")
    db_config = config['database']
    logger.info("analyze_com Database config loaded")

    # Accessing database connection parameters
    dbname = db_config['dbname']
    user = db_config['user']
    password = db_config['password']
    host = db_config['host']
    logger.info("Accessed database connection parameters")

def download_nltk_data():
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
def run_analyze_com(comments):
    if not comments:
        return 0  # Return neutral score if there are no comments
    scores = [SIA.polarity_scores(comments)['compound'] for comments in comments]
    average_score = sum(scores) / len(scores)
    logger.info(f"Calculated average sentiment score for comments in a submission: {average_score}")
    return average_score

def tokenize_and_tag(text):
    tokens = word_tokenize(text)
    return pos_tag(tokens)

def named_entity_recognition(tagged_tokens):
    logger.info(f"Tagged tokens {tagged_tokens}")
    return ne_chunk(tagged_tokens)

def frequency_distribution(tokens):
    return FreqDist(tokens)

def find_ngrams(tokens, n=2):  # Change n for bigrams (2), trigrams (3), etc.
    return list(ngrams(tokens, n))

def lexical_diversity(text):
    tokens = word_tokenize(text)
    return len(set(tokens)) / len(tokens)

# Connect to the database
try:
    logger.info("Connecting to the database.")
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
    cur = conn.cursor()
    logger.info("Connected to the database successfully.")

    # Fetch comments for analysis
    cur.execute("SELECT author, id, body FROM comments")
    comments = cur.fetchall()
    logger.info("Fetched comments for analysis.")

    for author, comment_id, body in comments:
        logger.info("Performing sentiment analysis")
        # Perform sentiment analysis
        sentiment_score = sia.polarity_scores(body)['compound']
        logger.info("Sentiment analysis complete")

        # Tokenize and tag for part-of-speech
        tagged_tokens = tokenize_and_tag(body)
        logger.info("Tokenized and tag for part-of-speech")

        # Named Entity Recognition
        ner_tree = ne_chunk(tagged_tokens)
        logger.info("Named Entity Recognition Complete")

        # Frequency Distribution
        tokens = [token for token, tag in tagged_tokens]
        freq_dist = frequency_distribution(tokens)
        logger.info("Frequency Distribution Complete")

        # n-grams (e.g., bigrams)
        bigrams = find_ngrams(tokens, 2)
        logger.info("n-grams (e.g., bigrams) Complete")

        # Lexical Diversity
        diversity = lexical_diversity(body)
        logger.info("Lexical Diversity Complete")

        # Process and potentially update analysis results back to the database
        sia = SentimentIntensityAnalyzer()
        # Update sentiment score back to database (you can expand this based on your requirements)
        cur.execute("UPDATE comments SET sentiment = %s WHERE id = %s", (sentiment_score, comment_id))
        logger.info("Updated sentiment score back to database")

    # Commit changes to the database
    conn.commit()
    logger.info("NLTK analysis completed.")
except Exception as e:
    logger.exception(f"An error occurred: {e}")

try:
    # Specify the Excel file path and save the workbook
    EXCEL_FILE_PATH = 'analysis_results/nltk_analysis.xlsx'
    # Prepare a new Excel workbook and sheet
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "NLTK Analysis"
    sheet.append(["Author", "Comment ID", "Comment Body", "Sentiment Score",
                "Named Entities", "Common Bigrams", "Lexical Diversity"])

    for author, comment_id, body in comments:
        # Recalculate sentiment score for this comment's body
        sentiment_score = sia.polarity_scores(body)['compound']

        # Additional NLP processing (tokenization, named entity recognition, etc.)
        tokens = word_tokenize(body)
        tagged_tokens = pos_tag(tokens)
        ner_results = named_entity_recognition(tagged_tokens)
        entities = ', '.join([str(t) for t in ner_results if hasattr(t, 'label')])
        bigram_list = list(ngrams(tokens, 2))
        common_bigrams = ', '.join([' '.join(pair) for pair in bigram_list[:5]])
        diversity_score = lexical_diversity(body)

        # Append analysis results to the Excel sheet
        sheet.append(
            [
                author,
                comment_id,
                f"{body[:100]}...",
                sentiment_score,
                entities,
                common_bigrams,
                diversity_score,
            ]
        )

        # Update sentiment score in the database
        cur.execute("UPDATE comments SET sentiment = %s WHERE id = %s", (sentiment_score, comment_id))

    # Commit changes to the database
    conn.commit()
    logger.info("Database updates completed.")
    # Save The Workbook
    workbook.save(EXCEL_FILE_PATH)
    logger.info(f"NLTK analysis results saved to {EXCEL_FILE_PATH}")
except Exception as e:
    logger.exception(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()
        logger.info("Database connection closed.")

logger.info("All Operations Complete")