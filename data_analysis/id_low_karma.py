from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

def identify_low_karma_accounts(submission_info, config):
    """
    This function `identify_low_karma_accounts` takes two parameters `submission_info` and `config`. It checks if the total karma in the `submission_info` is less than or equal to the karma threshold specified in the `config` (default is 5000 if not specified). If the total karma meets this criteria, it appends "Low Karma" to the `criteria_met_karma` list and logs a message using the logger. Finally, it returns the `criteria_met_karma`, `submission_info`, and `config`.
    """
    try:
        criteria_met_karma = []
        total_karma = submission_info.get("total_karma", 0)
        if total_karma <= config.get("karma_threshold", 5000):
            criteria_met_karma.append("Low Karma")
            logger.info("Identified low karma accounts")
        return criteria_met_karma
    except Exception as e:
        logger.warning(f"An error occurred while low karma accounts: {e}")
