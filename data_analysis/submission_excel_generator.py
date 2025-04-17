from tqdm import tqdm  # For the progress bar
import asyncpg
import asyncio
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging
from data_analysis.submission_analysis import analyze_data, fetch_submissions

logger = logging.getLogger(__name__)
logger.info("Submission Excel Generator Module Logging Set")
init_logger()

async def connect_to_database():
    """
    Establish an asyncpg connection to the PostgreSQL database.
    """
    cfg = CONFIG['database']
    try:
        conn = await asyncpg.connect(
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['dbname'],
            host=cfg['host'],
            port=cfg.get('port', 5432)
        )
        logger.info("Async database connection successful.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

EXCEL_FILE_PATH = 'analysis_results/submission_analysis.xlsx'

async def generate_submission_excel():
    """
    Connects to the database asynchronously, fetches submission data, analyzes it, and writes the results to an Excel file.
    """
    # 1. Connect to the database (asyncpg)
    conn = await connect_to_database()
    if not conn:
        logger.error("Failed to establish database connection.")
        return
    try:
        # 2. Fetch submission data (async call)

        submissions = await fetch_submissions(conn)
        logger.info(f"Fetched {len(submissions)} submissions for Excel generation.")

        # 3. Analyze the submissions using the analyze_data function.
        analyzed_data = analyze_data(submissions)
        logger.info(f"Analyzed {len(analyzed_data)} submissions.")

        # 4. Create the Excel workbook and worksheet
        workbook = Workbook()
        # workbook.active is the default sheet created; rename it
        sheet = workbook.active
        if sheet is not None:
            sheet.title = "Submission Data Analysis"
            sheet = workbook.create_sheet(title="Submission Data Analysis")
            assert isinstance(sheet, Worksheet), "Active sheet is not a Worksheet instance"
        else:
            logger.error("Failed to get the active sheet from the workbook.")
            return

        # 5. Define and append the header row.
        headers = [
            "Submission ID",
            "Author",
            "Title",
            "Score",
            "URL",
            "Sentiment",
            "Named Entities",
            "Lexical Diversity",
            "Common Bigrams",
            "Is Duplicate"
        ]
        sheet.append(headers)
        logger.debug("Header row appended to the Excel sheet.")

        # 6. Validate that we have data.
        if not analyzed_data:
            logger.error("No analyzed submission data found!")
            return

        # 7. Check if all headers are present in the data.
        if missing_keys := [h for h in headers if h not in analyzed_data[0]]:
            logger.error(f"Missing data detected: {missing_keys}")
            raise ValueError("Some submission data entries are missing expected keys.")

        # 8. Append each analyzed user's data to the sheet
        for data in tqdm(analyzed_data, desc="Writing Excel rows", unit="submission"):
            # Build the row based on the headers.
            row = [data.get(header, "") for header in headers]
            sheet.append(row)

        # 9. Save the Excel workbook.
        workbook.save(EXCEL_FILE_PATH)
        logger.info(f"Submission analysis results saved to {EXCEL_FILE_PATH}")

        logger.info("Database commit successful for Excel generation.")
    except Exception as e:
        logger.exception(f"Error during submission Excel generation: {e}")

    finally:
        # 10. Close the asyncpg connection
        await conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(generate_submission_excel())
    logger.info("Submission analysis Excel generation completed.")
