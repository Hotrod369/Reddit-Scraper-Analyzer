from data_analysis.cal_acc_age import calculate_account_age
from data_analysis.id_low_karma import identify_low_karma_accounts
from data_analysis.id_young_acc import identify_young_accounts
from data_analysis.sub_sent import calculate_average_sentiment
import pandas as pd
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

def process_submission_data(submissions, users, config):
    bot_df = pd.DataFrame()  # Initialize here to ensure it's not None

    bot_df_columns = [
        "User", "Submission Title", "Criteria", "Account Age", "Awardee Karma",
        "Awarder Karma", "Link Karma", "Comment Karma", "Total Karma",
        "User is Contributor", "Has Verified Email", "Accepts Followers",
        "Average Submission Sentiment"
    ]
    bot_df = pd.DataFrame(columns=bot_df_columns)
    added_users = set()

    try:
        # Process each submission
        for submission_id, submission_info in submissions.items():
            username = submission_info.get("User")
            if username and username not in added_users:
                titles = submission_info.get("Title", "")
                average_submission_sentiment = calculate_average_sentiment(submissions, titles)
                criteria_met_karma = identify_low_karma_accounts(submission_info, config) or []
                criteria_met_age = identify_young_accounts(submission_info, users, config) or []
                logger.info(f"Submission {submission_id} processed.")

                # Prepare a row to be appended
                row = {
                    "User": username,
                    "Submission Title": titles,
                    "Criteria": ", ".join(criteria_met_karma + criteria_met_age),
                    "Account Age": None,  # Placeholder, will be filled in next loop
                    "Awardee Karma": submission_info.get("Awardee Karma", 0),
                    "Awarder Karma": submission_info.get("Awarder Karma", 0),
                    "Link Karma": submission_info.get("Link Karma", 0),
                    "Comment Karma": submission_info.get("Comment Karma", 0),
                    "Total Karma": submission_info.get("Total Karma", 0),
                    "User is Contributor": submission_info.get("User is Contributor", False),
                    "Has Verified Email": submission_info.get("Has Verified Email", False),
                    "Accepts Followers": submission_info.get("Accepts Followers", False),
                    "Average Submission Sentiment": average_submission_sentiment,
                }
                new_row_df = pd.DataFrame([row])  # Convert the single row to a DataFrame
                bot_df = pd.concat([bot_df, new_row_df], ignore_index=True)
                added_users.add(username)
                logger.warning(f"Username {username} missing or already processed.")
    except Exception as e:
        logger.error(f"Error processing submission data: {e}")

    try:
        for username, user_info in users.items():
            created_utc = user_info['Creation Date']
            account_age_years = calculate_account_age(created_utc)
            if account_age_years is not None:
                logger.info(f"The account {username} is approximately {account_age_years:.2f} years old.")
                # Update the Account Age column for this user
                bot_df.loc[bot_df['User'] == username, 'Account Age'] = account_age_years
            else:
                logger.info(f"No account found with the username {username}.")
    except Exception as e:
        logger.error(f"Error processing account age: {e}")

    return bot_df  # Ensure it's always returned, even if empty

