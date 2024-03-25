"""
The `main` function is the entry point of the script.
It performs the following steps:
1. Loads the configuration file.
2. Checks if two JSON files exist.
3. Runs the scraper package.
4. Waits until both JSON files are created.
5. Loads the JSON data from the created files.
6. Converts the JSON data to a database.
7. Analyzes comments using the user data.
8. Analyzes submissions using the submission data.
9. Analyzes users using the user data.
10. Logs the completion of all operations.
"""
import json
import os
import time
import logging
from tools.config.logger_config import init_logger
from tools.config.logger_config import init_logger, logging


logger = logging.getLogger(__name__)
logger.info("Basic logging set")
init_logger()

# Load the configuration file
with open('tools/config/config.json', 'r', encoding='utf-8') as f:
    logger.info("Main Loading config file")
    config = json.load(f)
    logger.info("Main Config loaded")
    db_config = config['database']
    logger.info("main json_to_db Database config loaded")

def check_files_exist(file1, file2):
    """
    Check if two files exist.
    """
    return os.path.exists(file1) and os.path.exists(file2)

def main():
    """
    Execute the main workflow of the program.
    """
    # Paths to the JSON files you're waiting for
    file1_path = "analysis_results/user_data.json"
    file2_path = "analysis_results/submission_data.json"


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
    with open(file1_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    with open(file2_path, 'r', encoding='utf-8') as f:
        submission_data = json.load(f)


    from tools.json_to_db import main
    logger.info('Converting JSON to database')
    main()  # Pass both data sets
    

    from data_analysis.comment_analysis import run_analyze_com

    logger.info('Analyzing Comments')
    run_analyze_com(user_data)  # Pass user_data to analyze comments

    from data_analysis.submission_analysis import submission_analysis

    logger.info('Analyzing Submissions')
    submission_analysis()  # Pass submission_data to analyze submissions

    from data_analysis.user_analysis import user_analysis

    logger.info('Analyzing Users')
    user_analysis()  # Pass user_data to analyze users

    logger.info('All operations complete')

if __name__ == "__main__":
    main()