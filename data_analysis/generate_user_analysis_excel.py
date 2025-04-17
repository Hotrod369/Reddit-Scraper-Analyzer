from tqdm import tqdm  # For the progress bar
import asyncpg
import asyncio
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging
from data_analysis.user_analysis import analyze_users, fetch_users

logger = logging.getLogger(__name__)
logger.info("User Analysis Excel Module Logging Set")
init_logger()

EXCEL_FILE_PATH = 'analysis_results/user_analysis.xlsx'

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

async def generate_user_analysis_excel():
    """
    Connects to the database asynchronously, fetches user data, analyzes it, and writes the results to an Excel file.
    """
    # 1. Connect to the database (asyncpg)
    conn = await connect_to_database()
    if not conn:
        logger.error("Failed to establish database connection.")
        return

    try:
        # 2. Fetch user data (async call)
        users = await fetch_users(conn)
        logger.info(f"Fetched {len(users)} users for analysis.")

        # 3. Analyze user data (synchronous function)
        analyzed_users = analyze_users(CONFIG, users)
        if analyzed_users is None:
            logger.error("User analysis returned None, please check the analyze_users function.")
            return
        logger.info(f"Analyzed {len(analyzed_users)} users.")

        # 4. Create the Excel workbook and worksheet
        workbook = Workbook()
        # workbook.active is the default sheet created; rename it
        sheet = workbook.active
        if sheet is not None:
            sheet.title = "User Data Analysis"
            assert isinstance(sheet, Worksheet), "Active sheet is not a Worksheet instance"
        else:
            logger.error("Failed to get the active sheet from the workbook.")
            return

        # 5. Define and append the header row
        # Make sure these headers match the keys produced by analyze_users
        headers = [
            "User ID",
            "Username",
            "Account Created",
            "Link Karma",
            "Comment Karma",
            "Total Karma",
            "Is Employee",
            "Is Gold",
            "Dormant Days",
            "Has Verified Email",
            "Accepts Followers",
            "Is Subscriber",
            "Account Age",
            "Low Karma",
            "Young Account",
            "Burst Activity"
        ]
        sheet.append(headers)
        logger.debug("Header row appended to the Excel sheet.")

        # 6. Validate that we have data
        if not analyzed_users:
            logger.error("No analyzed user data found!")
            return

        if missing_keys := [h for h in headers if h not in analyzed_users[0]]:
            logger.error(f"Missing data detected: {missing_keys}")
            raise ValueError("Some user data entries are missing expected keys.")

        # 8. Append each analyzed user's data to the sheet
        for user_data in tqdm(analyzed_users, desc="Writing Excel rows", unit="user"):
            row = [user_data.get(h, "") for h in headers]
            sheet.append(row)

        # 9. Save the Excel workbook
        workbook.save(EXCEL_FILE_PATH)
        logger.info(f"User analysis results saved to {EXCEL_FILE_PATH}")

    except Exception as e:
        logger.exception(f"Error during Excel generation: {e}")

    finally:
        # 10. Close the asyncpg connection
        await conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    # 11. Run everything in the event loop
    asyncio.run(generate_user_analysis_excel())
    logger.info("User analysis Excel generation completed.")