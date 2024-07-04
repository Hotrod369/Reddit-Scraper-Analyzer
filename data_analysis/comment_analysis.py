import json
import re
import nltk
import psycopg2
from nltk import FreqDist, bigrams, ngrams, pos_tag
from nltk.chunk import ne_chunk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from tools.config.logger_config import init_logger
import logging

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
    """
    Downloads the required NLTK resources.
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
def run_analyze_com(comments):
    """
    Analyze sentiment of comments and return analyzed comments.
    """
    logger.info("Running analyze_com")   
    if not comments:
        logger.info("No comments to analyze.")
        return []

    analyzed_comments = []
    for comment in comments:
        try:
            id, author, body, score, submission_id = comment
            sentiment_analysis = SIA.polarity_scores(body)
            sentiment_score = sentiment_analysis['compound']

            if sentiment_score >= 0.05:
                sentiment_label = "Positive"
            elif sentiment_score <= -0.05:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"

            sentiment_cell_value = f"{sentiment_score} ({sentiment_label})"
            analyzed_comments.append((id, author, body, sentiment_cell_value))

        except ValueError as e:
            logger.error(f"Error unpacking comment: {e}")
            continue

    logger.info(f"Analyzed {len(analyzed_comments)} comments.")
    return analyzed_comments

def find_duplicate_comments(comments):
    """
    Find duplicate comments in a list of comments.
    """
    logger.info("Finding duplicate comments")
    # sourcery skip: inline-immediately-returned-variable
    # Using a dictionary to count occurrences of each comment body
    
    comment_count = {}
    for _, _, body in comments:
        normalized_body = body.strip().lower()  # Normalize the comment text for accurate comparison
        comment_count[normalized_body] = comment_count.get(normalized_body, 0) + 1

    global duplicates
    duplicates = {body for body, count in comment_count.items() if count > 1}
    return duplicates


def tokenize_and_tag(text):
    """
    Perform named entity recognition on tagged tokens.
    """
    tokens = word_tokenize(text)
    logger.info(f"Tokens {tokens}")
    return pos_tag(tokens)

def named_entity_recognition(tagged_tokens):
    """
    Perform named entity recognition on tagged tokens.
    """
    logger.info(f"Tagged tokens {tagged_tokens}")
    return ne_chunk(tagged_tokens)

def frequency_distribution(tokens):
    """
    Create a frequency distribution of the tokens.
    """
    logger.info(f"Tokens {tokens}")
    # Create a frequency distribution of the tokens
    freq_dist = FreqDist(tokens)
    logger.info(f"Frequency distribution {freq_dist}")
    # Return the frequency distribution as a dictionary
    return dict(freq_dist)

def find_ngrams(tokens, n=2):
    """
    Find n-grams in a list of tokens.
    """
    logger.debug(f"NGRAMS Tokens {tokens}")
    return list(ngrams(tokens, n))

def lexical_diversity(text):
    """
    Calculates the lexical diversity of a text and categorizes it.
    """
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation and special characters
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = text.strip()  # Remove leading and trailing whitespace

    tokens = word_tokenize(text)
    if not tokens:
        return 0, "No text"  # Handle empty or whitespace-only strings

    diversity_score = len(set(tokens)) / len(tokens)
    if diversity_score > 0.7:
        diversity_label = "Highly diverse"
    elif diversity_score > 0.4:
        diversity_label = "Moderately diverse"
    else:
        diversity_label = "Less diverse"

    return diversity_score, diversity_label

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
    logger.info("Analyzing Comments This Will Take Some time.")

    for author, comment_id, body in comments:
        logger.info("Performing sentiment analysis")
        # Perform sentiment analysis
        sentiment_score = SIA.polarity_scores(body)['compound']
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

    # Commit changes to the database
    conn.commit()
    logger.info("Comment analysis completed.")
except Exception as e:
    logger.exception(f"An error occurred: {e}")

def process_comment(author, comment_id, body, duplicates, sheet, SIA):
    is_duplicate = 'Yes' if body.strip().lower() in duplicates else 'No'
    sentiment_score = SIA.polarity_scores(body)['compound']
    sentiment_label = "Positive" if sentiment_score >= 0.05 else "Negative" if sentiment_score <= -0.05 else "Neutral"
    sentiment_cell_value = f"{sentiment_score} ({sentiment_label})"
    diversity_score, diversity_label = lexical_diversity(body)
    diversity_cell_value = f"{diversity_score:.2f} ({diversity_label})"
    tokens = word_tokenize(body)
    tagged_tokens = pos_tag(tokens)
    ner_results = ne_chunk(tagged_tokens)
    entities = ', '.join([str(t) for t in ner_results if hasattr(t, 'label')])
    bigram_list = list(ngrams(tokens, 2))
    common_bigrams = ', '.join([' '.join(pair) for pair in bigram_list[:5]])
    sheet.append([author, comment_id, f"{body[:100]}...", sentiment_cell_value, entities, common_bigrams, diversity_cell_value, is_duplicate])

try:
    logger.info("Connecting to the database.")
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
    cur = conn.cursor()
    logger.info("Connected to the database successfully.")

    # Find duplicates before processing comments
    duplicates = find_duplicate_comments(comments)

    # Specify the Excel file path and save the workbook
    EXCEL_FILE_PATH = 'analysis_results/comment_analysis.xlsx'
    workbook = Workbook()
    sheet = workbook.active
    if sheet is None:
        sheet = workbook.create_sheet(title="Comment Data Analysis")
    else:
        sheet.title = "User Data Analysis"

    # Explicitly cast sheet to Worksheet to satisfy the type checker
    assert isinstance(sheet, Worksheet), "Active sheet is not a Worksheet instance"
    sheet.append(["Author", "Comment ID", "Comment Body", "Sentiment Score", "Named Entities", "Common Bigrams", "Lexical Diversity", "Duplicate"])

    for author, comment_id, body in comments:
        process_comment(author, comment_id, body, duplicates, sheet, SIA)

    # Save the workbook
    workbook.save(EXCEL_FILE_PATH)
    logger.info(f"NLTK analysis results saved to {EXCEL_FILE_PATH}")

    # Commit changes to the database
    conn.commit()
    logger.info("Comment analysis completed.")

except Exception as e:
    logger.exception(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()
        logger.info("Database connection closed.")

logger.info("All Operations Complete")
