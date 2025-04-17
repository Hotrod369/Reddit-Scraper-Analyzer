from tqdm import tqdm  # For progress display
import asyncpg
import asyncio
import re
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk import word_tokenize, pos_tag, ne_chunk, ngrams
from tools.download_nltk_data import load_nltk_data
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging


logger = logging.getLogger(__name__)
logger.info("Submission Analysis Module Logging Set")
init_logger()
load_nltk_data()

# ------------------------------------------------
# 1) CONNECT TO DATABASE (asyncpg)
# ------------------------------------------------
async def connect_to_database():
    """
    Establish an asyncpg connection using the config in CONFIG.
    """
    cfg = CONFIG["database"]
    try:
        conn = await asyncpg.connect(
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["dbname"],
            host=cfg["host"],
            port=cfg.get("port", 5432),
        )
        logger.info("Async database connection successful.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


# ------------------------------------------------
# 2) FETCH SUBMISSIONS
# ------------------------------------------------
async def fetch_submissions(conn):
    """
    Retrieves submission data from the database using asyncpg.

    Returns:
        List of asyncpg.Record objects, each with columns:
            - submission_id
            - author
            - title
            - submission_score
            - url
            - submission_created_utc
            - over_18
    """
    query = """
        SELECT
            submissions.submission_id,
            submissions.author,
            submissions.title,
            submissions.submission_score,
            submissions.url,
            submissions.submission_created_utc,
            submissions.over_18
        FROM submissions
        JOIN users
        ON submissions.author = users.redditor
        ORDER BY submissions.submission_id
    """
    try:
        rows = await conn.fetch(query)
        logger.info(f"Fetched {len(rows)} submissions for analysis.")
        return rows
    except asyncpg.PostgresError as pg_err:
        logger.error(f"A PostgreSQL error occurred: {pg_err}")
        return []
    except Exception as e:
        logger.exception(f"An error occurred in fetch_submissions: {e}")
        return []

# ------------------------------------------------
# 3) UTILITY / ANALYSIS FUNCTIONS
# ------------------------------------------------
def analyze_submission_title(title: str) -> dict:
    """
    Perform NLTK-based analysis on a submission title.
    Returns a dict with named_entities, lexical_diversity, and common_bigrams.
    """
    # Tokenize the title.
    tokens = word_tokenize(title)
    # POS-tag the tokens.
    tagged_tokens = pos_tag(tokens)
    # Run named entity recognition.
    ner_tree = ne_chunk(tagged_tokens)
    named_entities = ", ".join(
        str(chunk) for chunk in ner_tree if hasattr(chunk, "label")
    )

    # Lexical diversity
    lex_div = len(set(tokens)) / len(tokens) if tokens else 0.0
    # Extract bigrams
    bigrams_list = list(ngrams(tokens, 2))
    common_bigrams = ", ".join([" ".join(b) for b in bigrams_list[:5]])

    return {
        "named_entities": named_entities,
        "lexical_diversity": lex_div,
        "common_bigrams": common_bigrams,
    }


def lex_div(text: str) -> tuple[float, str]:
    """
    Calculates lexical diversity of a text and returns (diversity_score, label).
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = word_tokenize(text)
    if not tokens:
        return 0.0, "No text"

    diversity_score = len(set(tokens)) / len(tokens)
    if diversity_score > 0.7:
        diversity_label = "Highly diverse"
    elif diversity_score > 0.4:
        diversity_label = "Moderately diverse"
    else:
        diversity_label = "Less diverse"

    return diversity_score, diversity_label

def mark_duplicate_submissions(analysis_results):
    """
    Given a list of submission dicts (each with at least
    'Author', 'Title', 'URL'), find duplicates posted by the same user
    with the same title and same link.

    Returns a modified copy of analysis_results, where each dict
    has a new key "Is Duplicate" (bool).
    """
    from collections import defaultdict

    # 1) Group submissions by (Author, Title, URL)
    #    Normalizing them is optional but recommended (e.g. .lower(), strip()).
    groups = defaultdict(list)
    for idx, sub in enumerate(analysis_results):
        author = sub["Author"].strip().lower()
        title = sub["Title"].strip().lower()
        url = sub["URL"].strip().lower()
        key = (author, (title, url))
        groups[key].append(idx)

    # 2) Mark duplicates
    #    If a group has more than 1 submission, all of them are duplicates.
    for indices in groups.values():
        if len(indices) > 1:
            # We have duplicates
            for i in indices:
                analysis_results[i]["Is Duplicate"] = True
        else:
            # Only 1 submission in that group => not a duplicate
            analysis_results[indices[0]]["Is Duplicate"] = False

    return analysis_results

def analyze_data(submissions):
    """
    Analyze a list of submissions.
    Returns a list of dicts with:
        - Submission ID
        - Author
        - Title
        - Submission Score
        - URL
        - Created UTC
        - Sentiment
        - Named Entities
        - Lexical Diversity
        - Common Bigrams
        - Is Duplicate
    """
    SIA = SentimentIntensityAnalyzer()
    results = []
    
    # Process each submission and build the analysis record
    for submission in tqdm(submissions, desc="Analyzing Submissions", unit="submission"):
        # submission is an asyncpg.Record or tuple
        (submission_id, author, title, submission_score, url, submission_created_utc, over_18) = submission

        # Sentiment analysis
        sentiment_score = SIA.polarity_scores(title)["compound"]
        if sentiment_score >= 0.05:
            sentiment_label = "Positive"
        elif sentiment_score <= -0.05:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        sentiment_cell_value = f"{sentiment_score:.3f} ({sentiment_label})"

        # Additional NLTK-based analysis
        title_analysis = analyze_submission_title(title)

        # Build a record without the duplicate flag first
        record = {
            "Submission ID": submission_id,
            "Author": author,
            "Title": title,
            "Score": submission_score,
            "URL": url,
            "Created UTC": submission_created_utc,
            "NSFW": over_18,
            "Sentiment": sentiment_cell_value,
            "Named Entities": title_analysis["named_entities"],
            "Lexical Diversity": title_analysis["lexical_diversity"],
            "Common Bigrams": title_analysis["common_bigrams"],
            # "Is Duplicate" will be set later
        }
        results.append(record)
    
    # Mark duplicates on the entire results list
    results = mark_duplicate_submissions(results)
    logger.info("Submission data analysis completed.")
    return results

# --------------------------------
# 4) MAIN SUBMISSION ANALYSIS FLOW
# --------------------------------
async def submission_analysis():
    """
    Orchestrates the submission data analysis process.
    1) Connect to DB
    2) Fetch submissions
    3) Analyze
    4) Optionally: store or return results
    """
    logger.info("Starting submission analysis")

    # 1) Connect to DB
    conn = await connect_to_database()
    if conn is None:
        logger.error("Could not connect to the database.")
        return

    try:
        # 2) Fetch submissions
        submissions = await fetch_submissions(conn)
        if not submissions:
            logger.warning("No submissions found to analyze.")
            return

        # 3) Analyze
        analysis_results = analyze_data(submissions)
        logger.info("Analyzing submissions completed.")

        # 3a) Mark duplicates
        analysis_results = mark_duplicate_submissions(analysis_results)

        # 4) Optionally: store or return results
        logger.debug(analysis_results)

    except asyncpg.PostgresError as e:
        logger.error(f"Error during submission analysis (asyncpg): {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during submission_analysis: {e}")
    finally:
        # 5) Clean up
        await conn.close()
        logger.info("Submission analysis completed, connection closed.")


if __name__ == "__main__":
    asyncio.run(submission_analysis())
    logger.info("Submission analysis completed.")