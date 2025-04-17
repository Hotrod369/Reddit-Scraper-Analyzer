from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging


logger = logging.getLogger(__name__)
logger.info(" id_low_karma Basic logging set")
init_logger()

logger.info("Identifying low karma accounts")


def identify_low_karma_accounts(total_karma, config):
    """
    Identify accounts with low karma based on a specified threshold.
    """
    try:
        criteria_met_karma = []
        # Correctly retrieve the threshold from the CONFIG dictionary:
        karma_threshold = CONFIG["karma_threshold"]
#        logger.debug(f"User's total karma is {total_karma}")

        if total_karma < karma_threshold:
            criteria_met_karma.append("Low Karma")
#            logger.debug("User is a low karma account.")

        return criteria_met_karma
    except Exception as e:
#       logger.warning(f"An error occurred while identifying low karma accounts: {e}")
        return []

logger.info("Low karma accounts identified")





