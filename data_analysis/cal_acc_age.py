import datetime as dt
from tools.config.logger_config import init_logger
import logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

def calculate_account_age(created_utc):
    """
    Calculate the age of a user account in years based on the created_utc timestamp.
    """
    try:
        if created_utc is None:
            logger.warning("Created_utc timestamp is None, returning None for account age.")
            return None

        # Ensure the input is a valid timestamp
        if not isinstance(created_utc, (int, float)):
            logger.error(f"Invalid type for created_utc: {type(created_utc)}. Expected int or float.")
            return None

        # Convert the created_utc from seconds to a datetime object
        account_created_time = dt.datetime.fromtimestamp(created_utc, dt.timezone.utc)
        logger.debug(f"Account creation time: {account_created_time}")

        # Calculate the difference in time between now and when the account was created
        current_time = dt.datetime.now(dt.timezone.utc)
        account_age_delta = current_time - account_created_time

        # Convert the time difference to years
        account_age_years = account_age_delta.days / 365.25
        logger.info(f"Calculated account age: {account_age_years:.2f} years for UTC {created_utc}")

        return account_age_years

    except Exception as e:
        logger.exception(f"Error calculating account age for UTC {created_utc}: {e}")
        return None

logger.info("Account ages calculated")