import pandas as pd
from data_analysis.com_sent import calculate_comment_sentiment
from data_analysis.cal_acc_age import calculate_account_age
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

def process_comments_data(comments_data, user_data, SIA):
    """
    Processes comments for each submission to identify potential bot accounts based on comment sentiment.
    """
    try:
        bot_df_columns = [
            "id", "Author", "Account Age", "Body", "Score", "Average Comment Sentiment",
        ]
        # Initialize DataFrame with columns but no rows
        bot_df = pd.DataFrame(columns=bot_df_columns)
        rows_to_append = []  # Accumulate row data here
        added_users = set()
        row = []
        logger.info(f"Created DataFrame {bot_df} and added users {added_users}")

        for comment_id, comment_details in comments_data():
            author = comment_details.get("Author")
            if not author or author in added_users:
                logger.warning(f"Username {author} missing or already processed.")
                continue
            body = comment_details.get("Comment Body", "")  # Ensure body is a string
            score = comment_details.get("Score")
            submission_id = comment_details.get("Submission ID")
            continue

        for username, user_info in user_data():
            username = comment_details.get("Author")
            user_info = user_data.get(username, {})
            created_utc = user_info.get('Creation Date')  # Ensure this key matches the one used in fetch_data logging
            account_age_years = calculate_account_age(created_utc)
            logger.info(f"Calculated Account Age while processing comments {account_age_years}")
            pass

            if not author or author in added_users:
                logger.warning(f"Username {author} missing or already processed.")
                continue

            # Calculate sentiment score
            average_comment_sentiment = calculate_comment_sentiment(body, SIA)
            logger.info(f"Calculated Comment Sentiment while processing comments {average_comment_sentiment}")
            logger.info(f"Comment Author: {author}, Comment Body: {body}, Comment ID: {comment_id},\
                        Average Sentiment: {average_comment_sentiment}")

            # Append the new row to the rows list
            row = {
                "id": comment_id,
                "Author": author,
                "Account Age": account_age_years,
                "body": body,
                "Score": score,
                "submission_id": submission_id,
                "Average Comment Sentiment": average_comment_sentiment
            }
            rows_to_append.append(row)
            added_users.add(author)

        # After the loop, check if there are any rows to append
        if rows_to_append:
            new_rows_df = pd.DataFrame(rows_to_append)
            bot_df = pd.concat([bot_df, new_rows_df], ignore_index=True)

        return bot_df
    except Exception as e:
        logger.warning(f"An error occurred while fetching comments from submissions: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of an error