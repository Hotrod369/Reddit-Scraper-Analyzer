from typing import List
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("ID young Accounts Basic logging set")
init_logger()


def identify_young_accounts(account_age_years: float) -> List[str]:
    """
    Identify accounts with an age below a specified threshold.
    """
    config = CONFIG
    criteria_met_age = []
    try:
        account_age_threshold = config.get("account_age_threshold", 1.0)  # Default to 1 year if not specified
        logger.debug(f"Account age threshold is {account_age_threshold} years")

        if account_age_years <= account_age_threshold:
            criteria_met_age.append("Young Account Age")
            logger.debug(f"Account is young (age: {account_age_years} years)")

        return criteria_met_age
    except Exception as e:
        logger.warning(f"Error identifying young accounts: {e}")
        return []
logger.info("Young Accounts Identified")