import asyncio
from tqdm import tqdm
from openpyxl import Workbook
from tools.config.config_loader import CONFIG
from tools.config.logger_config import init_logger, logging
from data_analysis.comment_analysis import comment_analysis

logger = logging.getLogger(__name__)

EXCEL_FILE_PATH = 'analysis_results/comment_analysis.xlsx'

async def generate_comment_analysis_excel():
    """
    Asynchronously fetches and analyzes comments, then writes the results to an Excel file.
    """
    try:
        # 1. Call your comment_analysis function to get the final data
        analyzed_comments = await comment_analysis()
        logger.info(f"Fetched and analyzed {len(analyzed_comments)} comments for Excel generation.")

        if not analyzed_comments:
            logger.warning("No analyzed comment data found! Excel generation aborted.")
            return

        # 2. Create the Excel workbook and sheet
        workbook = Workbook()
        sheet = workbook.active if workbook.active is not None else workbook.create_sheet("Comment Data Analysis")
        sheet.title = "Comment Data Analysis"

        # 3. Define the header row
        headers = [
            "Comment ID",
            "Author",
            "Created ON",
            "Body",
            "Comment Score",
            "Is Submitter",
            "Edited",
            "Submission ID",
            "Sentiment",
            "Named Entities",
            "Lexical Diversity",
            "Common Bigrams",
            "Is Duplicate"
        ]
        sheet.append(headers)
        logger.debug("Header row appended to the Excel sheet.")

        if missing_keys := [
            h for h in headers if h not in analyzed_comments[0]
        ]:
            logger.error(f"Missing data keys detected: {missing_keys}")
            raise ValueError("Some comment data entries are missing expected keys.")

        # 5. Append each comment dictionary to the sheet
        for comment_dict in tqdm(analyzed_comments, desc="Writing Excel rows", unit="comment"):
            row = [comment_dict.get(h, "") for h in headers]
            sheet.append(row)
#            logger.debug(f"Appended row for comment {comment_dict.get('Comment ID', '')}: {row}")
#            logger.info(f"Appened {len(analyzed_comments)} comments to the Excel sheet.")

        # 6. Save the workbook
        workbook.save(EXCEL_FILE_PATH)
        logger.info(f"Comment analysis results saved to {EXCEL_FILE_PATH}")

    except Exception as e:
        logger.exception(f"Error during comment Excel generation: {e}")

if __name__ == "__main__":
    asyncio.run(generate_comment_analysis_excel())
    init_logger()
    logger.info("Comment analysis Excel generation completed.")