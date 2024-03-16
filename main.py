import json
import os
import time
from tools.config.logger_config import logging, init_logger

# Initialize and configure logger
init_logger()
logger = logging.getLogger(__name__)
logger.info("Main Basic logging set")

# Load the configuration file
with open('tools/config/config.json', 'r', encoding='utf-8') as f:
    logger.info("Main Loading config file")
    config = json.load(f)
    logger.info("Main Config loaded")
    db_config = config['database']
    logger.info("main json_to_db Database config loaded")

def check_files_exist(file1, file2):
    return os.path.exists(file1) and os.path.exists(file2)

def main():
    # Paths to the JSON files you're waiting for
    file1_path = "./analysis_results/user_data.json"
    file2_path = "./analysis_results/submission_data.json"

    from tools.scraper import run_scraper
    # Run the scraper package
    run_scraper()

    # Wait until both JSON files are created
    while not check_files_exist(file1_path, file2_path):
        print(f"Waiting for {file1_path} and {file2_path} to be created...")
        time.sleep(60)  # Wait for 1 minute before checking again

    # Both files exist, continue with the next package
    print("JSON files found! Continuing execution...")

    # Load JSON data
    import json
    with open(file1_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    with open(file2_path, 'r', encoding='utf-8') as f:
        submission_data = json.load(f)


    from tools.json_to_db import main
    logger.info('Converting JSON to database')
    main()  # Pass both data sets

    from data_analysis.analyze_com import run_analyze_com

    logger.info('Analyzing Comments')
    run_analyze_com(user_data)  # Pass user_data to analyze comments

    from data_analysis.analyze_sub import run_analyze_sub

    logger.info('Analyzing Submissions')
    run_analyze_sub()  # Pass submission_data to analyze submissions

    logger.info('All operations complete')

if __name__ == "__main__":
    main()