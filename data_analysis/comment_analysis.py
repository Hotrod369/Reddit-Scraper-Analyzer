import asyncpg
import asyncio
import datetime
import re
import concurrent.futures
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk import word_tokenize, pos_tag, ne_chunk, ngrams
from nltk.corpus import words
from tqdm import tqdm
from tools.download_nltk_data import load_nltk_data
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
SIA = SentimentIntensityAnalyzer()

# Global cache dictionary
analyze_heavy_cache = {}

# ------------------------------------------------
# 1) CONNECT TO DATABASE (asyncpg)
# ------------------------------------------------
async def connect_to_database():
    """
    Establishes an asyncpg connection using configuration from CONFIG.
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
# 2) FETCH COMMENTS
# ------------------------------------------------
async def fetch_comments(conn):
    """
    Retrieves comment data from the database.
    Expected columns:
        - comment_id, comment_author, comment_created_utc, body, comment_score, is_submitter, edited, link_id
    """
    query = """
        SELECT
            comment_id,
            comment_author,
            comment_created_utc,
            body,
            comment_score,
            is_submitter,
            edited,
            link_id
        FROM comments
        ORDER BY comment_id;
    """
    try:
        rows = await conn.fetch(query)
        logger.info(f"Fetched {len(rows)} comments for analysis.")
        return rows
    except Exception as e:
        logger.exception(f"Error fetching comments: {e}")
        return []

# ------------------------------------------------
# 3) UTILITY / HEAVY ANALYSIS FUNCTIONS
# ------------------------------------------------
def analyze_heavy(body: str) -> dict:
    """
    Performs heavy analysis on a comment body:
        - Sentiment analysis
        - Named entity recognition
        - Lexical diversity calculation
        - Extraction of common bigrams
    Returns a dictionary with these fields.
    """
    try:
        logger.debug(f"Starting heavy analysis for body: {body[:20]}...")
        # Sentiment analysis
        sentiment_scores = SIA.polarity_scores(body)
        compound = sentiment_scores.get("compound", 0)
        if compound >= 0.05:
            sentiment_label = "Positive"
        elif compound <= -0.05:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        sentiment = f"{compound:.3f} ({sentiment_label})"

        # Named Entities
        tokens = word_tokenize(body)
        tagged = pos_tag(tokens)
        try:
            tree = ne_chunk(tagged)
            named_entities = ", ".join(
                " ".join(token for token, _ in subtree)
                for subtree in tree if hasattr(subtree, "label")
            )
        except Exception as e:
            logger.exception("Named entity extraction failed")
            named_entities = ""

        # Lexical Diversity
        body_lower = body.lower()
        body_clean = re.sub(r"[^\w\s]", "", body_lower)
        body_clean = re.sub(r"\s+", " ", body_clean).strip()
        if tokens_clean := word_tokenize(body_clean):
            ld_score = len(set(tokens_clean)) / len(tokens_clean)
            if ld_score > 0.7:
                ld_label = "Highly diverse"
            elif ld_score > 0.4:
                ld_label = "Moderately diverse"
            else:
                ld_label = "Less diverse"
        else:
            ld_score = 0
            ld_label = "No text"
        lexical_diversity_str = f"{ld_score:.2f} ({ld_label})"

        # Common Bigrams
        bigrams_list = list(ngrams(tokens, 2))
        common_bigrams = ", ".join(" ".join(b) for b in bigrams_list[:5])

        result = {
            "Sentiment": sentiment,
            "Named Entities": named_entities,
            "Lexical Diversity": lexical_diversity_str,
            "Common Bigrams": common_bigrams,
        }
        analyze_heavy_cache[body] = result
        logger.debug(f"Analyze heavy result for body {body[:20]}: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error in analyze_heavy for body {body[:20]}: {e}")
        return {
            "Sentiment": "Error",
            "Named Entities": "",
            "Lexical Diversity": "Error",
            "Common Bigrams": "",
        }

def mark_duplicate_comments(analysis_results: list) -> list:
    """
    Given a list of comment analysis dictionaries, mark duplicates based on
    the normalized comment body. Updates each dictionary's "Is Duplicate" key
    to "Yes" if the normalized body appears more than once, else "No".
    """
    freq = {}
    for result in analysis_results:
        normalized = result["Body"].strip().lower()
        freq[normalized] = freq.get(normalized, 0) + 1
    for result in analysis_results:
        normalized = result["Body"].strip().lower()
        result["Is Duplicate"] = "Yes" if freq.get(normalized, 0) > 1 else "No"
    return analysis_results

# ------------------------------------------------
# 4) ANALYZE DATA (ASYNC)
# ------------------------------------------------
async def analyze_data(comments) -> list:
    """
    Processes each comment and builds an analysis dictionary using cached heavy analysis data.
    Schema keys:
        - Comment ID, Author, Created ON, Body, Comment Score, Is Submitter, Edited,
        - Submission ID, Is Duplicate, Sentiment, Named Entities, Lexical Diversity, Common Bigrams
    """
    # Build set of unique comment bodies (using stripped text to avoid duplicates)
    unique_bodies = {row["body"].strip() for row in comments if row["body"]}
    loop = asyncio.get_running_loop()

    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        # 1) Build a dictionary mapping each *wrapped* future -> body
        tasks_map = {}
        for body in unique_bodies:
            cf_future = loop.run_in_executor(executor, analyze_heavy, body)
            aio_future = asyncio.wrap_future(cf_future)
            tasks_map[aio_future] = body  # store the wrapped future

        heavy_results_dict = {}

        # 2) Wait for all tasks to complete
        done, _ = await asyncio.wait(tasks_map.keys())
        for wrapped_future in done:
            result = wrapped_future.result()
            body = tasks_map[wrapped_future]
            heavy_results_dict[body] = result
        
    # 3) Build final results
    results = []
    for row in comments:
        body = row["body"]
        heavy = heavy_results_dict.get(body.strip(), {
            "Sentiment": "",
            "Named Entities": "",
            "Lexical Diversity": "",
            "Common Bigrams": ""
        })
        record = {
            "Comment ID": row["comment_id"],
            "Author": row["comment_author"],
            "Created ON": row["comment_created_utc"],
            "Body": body,
            "Comment Score": row["comment_score"],
            "Is Submitter": row["is_submitter"],
            "Edited": row["edited"],
            "Submission ID": row["link_id"],
            "Sentiment": heavy["Sentiment"],
            "Named Entities": heavy["Named Entities"],
            "Lexical Diversity": heavy["Lexical Diversity"],
            "Common Bigrams": heavy["Common Bigrams"],
            # "Is Duplicate" will be set later
        }
        results.append(record)
        logger.debug(f"Appended comment {row['comment_id']}: {record}")
        logger.debug(f"Loaded comment_analysis from {__file__}")

    return results

# ------------------------------------------------
# 5) MAIN COMMENT ANALYSIS FLOW
# ------------------------------------------------
async def comment_analysis():
    """
    Orchestrates the comment analysis:
        1) Connect to DB
        2) Fetch comments
        3) analyze_data
        4) Return results
    """
    # 1) Connect to DB
    conn = await connect_to_database()
    if conn is None:
        logger.error("Could not connect to the database.")
        return []
    try:
        # 2) Fetch comments
        rows = await fetch_comments(conn)
        if not rows:
            logger.warning("No comments found to analyze.")

        # 3) Analyze
        analysis_results = await analyze_data(rows) if rows else []

        # 3a Mark duplicates
        analysis_results = mark_duplicate_comments(analysis_results)

        # 4) Optionally: store or return results
        logger.debug(analysis_results)
        return analysis_results

    except Exception as e:
        logger.exception(f"An error occurred during comment analysis: {e}")
        return []
    finally:
        # 5) Clean up
        await conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    init_logger()
    load_nltk_data()
    _ = words.words("en-basic")  # Preload the "en-basic" word list
    results = asyncio.run(comment_analysis())
    logger.info(f"Analyzed {len(results)} comments.")
