import json
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from data_analysis.fetch_data import fetch_data_from_database
from data_analysis.cal_acc_age import calculate_account_age
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

# Load configuration
def load_config():
    with open('tools/config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        logger.info(" analyze_sub Configuration loaded successfully.")
    return config

# Initialize SIA
def init_sia():
    logger.info("Initializing SentimentIntensityAnalyzer...")
    return SentimentIntensityAnalyzer()

# Main function to execute the processing
def run_analyze_sub():
    try:
        bot_df = None
        config = load_config()
        users, submissions, comments = fetch_data_from_database()
        logger.info("Data fetched successfully.")
        from data_analysis.cal_acc_age import calculate_account_age
        bot_df = calculate_account_age(bot_df)
        logger.info("Account age calculated successfully.")
        from data_analysis.proc_sub import process_submission_data
        bot_df = process_submission_data(submissions, users, config)
        logger.info("Data processed successfully.")



        if bot_df is not None:
            bot_df.to_excel("analysis_results/potential_bot_accounts.xlsx", index=False)
        else:
            logger.error("Attempted to write to Excel, but bot_df is None.")

        # Save bot_df to an Excel file
        if bot_df is not None and not bot_df.empty:
            excel_file_path = 'analysis_results/potential_bot_accounts.xlsx'
            logger.info(f"Writing data to {excel_file_path}")
            bot_df.to_excel(excel_file_path, index=False)
            logger.info(f"Data successfully written to {excel_file_path}")
        else:
            logger.error("No data to write to Excel.")
    except Exception as e:
        logger.error(f"Error occurred while analyzing the data: {e}")
        raise e

if __name__ == "__main__":
    run_analyze_sub()

