import logging
from tools.config.logger_config import init_logger


logger = logging.getLogger(__name__)
logger.info(" id_low_karma Basic logging set")
init_logger()

def identify_low_karma_accounts(total_karma, config):
    try:
        criteria_met_karma = []
        logger.info("Identifying low karma accounts")

        karma_threshold = config.get('karma_threshold', 5000)  # Default to 5000 if not specified
        logger.debug(f"Karma threshold is {karma_threshold}")
        logger.debug(f"User's total karma is {total_karma}")

        if total_karma < karma_threshold:
            criteria_met_karma.append("Low Karma")
            logger.debug("User is a low karma account.")

        return criteria_met_karma
    except Exception as e:
        logger.warning(f"An error occurred while identifying low karma accounts: {e}")
        return []
logger.info("Low karma accounts identified")




