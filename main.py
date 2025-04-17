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
8. Generates an Excel report for comment analysis.
9. Analyzes submissions using the submission data.
10. Generates an Excel report for submission analysis.
11. Analyzes users using the user data.
12. Logs the completion of all operations.
"""
import asyncio
import argparse
import json
import os
import time
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("Main Basic logging set")
init_logger()

# Load centralized configuration parameters
db_config = CONFIG["database"]
logger.debug("Main Loading config file")
logger.info("main json_to_db Database config loaded")

def check_files_exist(file1, file2):
    """Check if two files exist."""
    return os.path.exists(file1) and os.path.exists(file2)

async def run_full_pipeline():
    # (1) Run the scraper (if needed)
    from tools.scraper import run_scraper_async
    await run_scraper_async()  # directly await the async function
    logger.debug("Scraper package executed")

    # (2) Wait until JSON files exist (if applicable)
    file1_path = "analysis_results/redditor_data.json"  # Updated to match scraper output
    file2_path = "analysis_results/submission_data.json"
    timeout_seconds = 5 * 60  # 5 minutes
    start_time = time.time()

    while not check_files_exist(file1_path, file2_path):
        logger.debug(f"Waiting for {file1_path} and {file2_path} to be created...")
        await asyncio.sleep(60)  # Wait for 1 minute
        if time.time() - start_time > timeout_seconds:
            raise FileNotFoundError(
                f"JSON files {file1_path} and {file2_path} not found after 5 minutes."
            )

    logger.debug("JSON files found! Continuing execution...")

    # (3) Load JSON data
    with open(file1_path, 'r', encoding='utf-8') as f:
        logger.debug("User data loaded")
        if not (user_data := json.load(f)):
            raise ValueError("User data is empty")
        else:
            logger.debug("User data is not empty")
    with open(file2_path, 'r', encoding='utf-8') as f:
        submission_data = json.load(f)
        logger.debug("Submission data loaded")
        if not submission_data:
            raise ValueError("Submission data is empty")
        logger.debug("Submission data is not empty")

    # (4) Insert JSON data into the database
    from tools.json_to_db import main as json_to_db_main
    logger.info('Converting JSON to database')
    await json_to_db_main()

    # (5) Generate Excel reports
    from data_analysis.generate_comment_analysis import generate_comment_analysis_excel
    logger.info('Generating Comment Analysis Results Excel')
    await generate_comment_analysis_excel()

    from data_analysis.submission_excel_generator import generate_submission_excel
    logger.info('Generating Submission Analysis Results Excel')
    await generate_submission_excel()

    from data_analysis.generate_user_analysis_excel import generate_user_analysis_excel
    logger.info('Generating User Analysis Results Excel')
    await generate_user_analysis_excel()

async def run_excel_generation_only():
    # Only run the Excel generation modules.
    from data_analysis.generate_user_analysis_excel import generate_user_analysis_excel
    logger.info('Generating User Analysis Results Excel')
    await generate_user_analysis_excel()
    
    from data_analysis.generate_comment_analysis import generate_comment_analysis_excel
    logger.info('Generating Comment Analysis Results Excel')
    await generate_comment_analysis_excel()

    from data_analysis.submission_excel_generator import generate_submission_excel
    logger.info('Generating Submission Analysis Results Excel')
    await generate_submission_excel()

    logger.info('Excel generation complete.')

async def run_generate_comment_analysis_excel_only():
    from data_analysis.generate_comment_analysis import generate_comment_analysis_excel
    logger.info('Generating Comment Analysis Results Excel')
    await generate_comment_analysis_excel()
    logger.info('Comment analysis Excel generation complete.')

async def run_generate_submission_excel_only():
    from data_analysis.submission_excel_generator import generate_submission_excel
    logger.info('Generating Submission Analysis Results Excel')
    await generate_submission_excel()
    logger.info('Submission analysis Excel generation complete.')

async def run_generate_user_analysis_excel_only():
    from data_analysis.generate_user_analysis_excel import generate_user_analysis_excel
    logger.info('Generating User Analysis Results Excel')
    await generate_user_analysis_excel()
    logger.info('User analysis Excel generation complete.')
    
async def main():
    parser = argparse.ArgumentParser(description="Run Reddit Scraper & Analyzer")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--excel-only", action="store_true", help="Run Excel generation only")
    group.add_argument("--scraper-only", action="store_true", help="Run scraper only")
    group.add_argument("--json-to-db-only", action="store_true", help="Run JSON-to-DB only")
    group.add_argument("--comment-analysis-excel-only", action="store_true", help="Run comment analysis Excel generation only")
    group.add_argument("--submission-excel-only", action="store_true", help="Run submission analysis Excel generation only")
    group.add_argument("--user-analysis-excel-only", action="store_true", help="Run user analysis Excel generation only")
    args = parser.parse_args()

    if args.excel_only:
        logger.info("Running in Excel-only mode.")
        await run_excel_generation_only()
        
    elif args.scraper_only:
        logger.info("Running in scraper-only mode.")
        from tools.scraper import run_scraper_async
        await run_scraper_async()
        logger.info("Scraper package executed")
        
    elif args.json_to_db_only:
        logger.info("Running in JSON-to-DB-only mode.")
        from tools.json_to_db import main as json_to_db_main
        await json_to_db_main()

    elif args.comment_analysis_excel_only:
        logger.info("Running in comment analysis Excel-only mode.")
        await run_generate_comment_analysis_excel_only()

    elif args.submission_excel_only:
        logger.info("Running in submission analysis Excel-only mode.")
        await run_generate_submission_excel_only()

    elif args.user_analysis_excel_only:
        logger.info("Running in user analysis Excel-only mode.")
        await run_generate_user_analysis_excel_only()
        
    else:
        logger.info("Running the full pipeline.")
        await run_full_pipeline()

    logger.info("All operations complete.")

if __name__ == "__main__":
    asyncio.run(main())