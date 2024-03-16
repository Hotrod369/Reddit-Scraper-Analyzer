import datetime as dt
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()




def calculate_account_age(created_utc):
    if created_utc is None:
        return None
    logger.info(f"User account created_utc: {created_utc}")
    # Get the current time in UTC
    current_time = dt.datetime.now(dt.timezone.utc)
    logger.info(f"Current time in UTC: {current_time}")

    # Convert the created_utc from seconds to a datetime object
    account_created_time = dt.datetime.fromtimestamp(created_utc, dt.timezone.utc)
    logger.info(f"User account created_utc converted to datetime: {account_created_time}")

    # Calculate the difference in time between now and when the account was created
    account_age_years = current_time - account_created_time
    logger.info(f"User account age calculated: {account_age_years}")

    # Convert the time difference to years and return it
    account_age_years = (
        dt.datetime.now(dt.timezone.utc) - account_created_time
    ).days / 365.25
    logger.info(f"User account age calculated with created_utc {created_utc}: {account_age_years:.2f} years")

    return account_age_years
logger.info("Account ages calculated")