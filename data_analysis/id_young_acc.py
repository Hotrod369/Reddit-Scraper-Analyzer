"""
The `identify_young_accounts` function takes in `submission_info`,
`user_data`, and `config` as parameters. It checks if the user associated
with the submission is considered a young account based on the account age
compared to a threshold defined in the `config`.
"""
import datetime as dt
import pandas as pd
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

def identify_young_accounts(submission_info, user_data, config):
    criteria_met_age = []
    try:
        account_age_threshold = config.get("account_age_threshold", 2)
        username = submission_info.get("User")
        if user_creation_utc := user_data.get(username, {}).get("created_utc"):
            current_time = pd.Timestamp.now(tz=dt.timezone.utc)
            account_creation_time = pd.Timestamp.fromtimestamp(user_creation_utc, tz=dt.timezone.utc)
            account_age_years = (current_time - account_creation_time).total_seconds() / (365.25 * 24 * 3600)
            if account_age_years <= account_age_threshold:
                criteria_met_age.append("Young Account Age")
            logger.info(f"Calculated the user's account age: {account_age_years} years for user {username}.")
        return criteria_met_age
    except Exception as e:
        logger.warning(f"An error occurred while identifying young accounts: {e}")
        return criteria_met_age