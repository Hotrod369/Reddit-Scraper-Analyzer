'''
Analyzes data from scraper.py and finds potential bot accounts
'''
import json
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import datetime as dt  # Add this line to import the datetime module


# Load data from JSON files
with open("user_data.json", "r", encoding="utf-8") as user_file:
    user_data = json.load(user_file)

with open("submission_data.json", "r", encoding="utf-8") as submission_file:
    submission_data = json.load(submission_file)

# Create a DataFrame from the user data
data = pd.DataFrame.from_dict(user_data, orient="index")

# Define thresholds for bot characteristics
KARMA_THRESHOLD = 5000
ACCOUNT_AGE_THRESHOLD = 2  # years
POSTING_FREQUENCY_THRESHOLD = 30  # Example threshold for unusual posting frequency

# Create a DataFrame to store potential bot accounts and their criteria
bot_df = pd.DataFrame(columns=["User", "Criteria", "Account Age", "Awardee Karma",
                                "Link Karma", "Comment Karma", "Total Karma",
                                "Number of Posts", "Number of Comments",
                                "User is Contributor", "Has Verified Email", "Accepts Followers"])

# Create a set to keep track of users already added to the DataFrame
added_users = set()

try:
    # Iterate through the submissions in submission_data and update user_data
    for submission_id, submission_info in submission_data.items():
        username = submission_info["User"]
        awardee_karma = submission_info.get("awardee_karma", 0)
        link_karma = submission_info.get("link_karma", 0)
        comment_karma = submission_info.get("comment_karma", 0)
        total_karma = submission_info.get("total_karma", 0)
        user_is_contributor = submission_info.get("user_is_contributor", False)
        has_verified_email = submission_info.get("has_verified_email", False)
        accept_followers = submission_info.get("accept_followers", False)
        
        # Calculate the account age using created_utc
        current_time = dt.datetime.utcnow()
        account_creation_time = dt.datetime.utcfromtimestamp(submission_info["created_utc"])
        account_age = (current_time - account_creation_time).days / 365.25

        # Check if the user exists in user_data
        if username in user_data:
            # Access the "Posts" and "Comments" fields from user_data
            number_of_posts = user_data[username].get("Posts", 0)
            number_of_comments = user_data[username].get("Comments", 0)

            # Initialize the criteria list
            criteria_met = []

            # Check for characteristics of potential bot accounts
            if total_karma <= KARMA_THRESHOLD:
                criteria_met.append("Low Karma")
            if account_age <= ACCOUNT_AGE_THRESHOLD:
                criteria_met.append("Young Account Age")
            if number_of_posts >= POSTING_FREQUENCY_THRESHOLD:
                criteria_met.append("Unusual Posting Frequency")

            # Check if the user has already been added to the DataFrame
            if username not in added_users:
                # Add the user to the DataFrame
                bot_df = bot_df.append({
                    "User": username,
                    "Criteria": ", ".join(criteria_met) if criteria_met else "None",
                    "Link Karma": link_karma,
                    "Comment Karma": comment_karma,
                    "Total Karma": total_karma,
                    "Account Age": account_age,
                    "Awardee Karma": awardee_karma,
                    "Number of Posts": number_of_posts,
                    "Number of Comments": number_of_comments,
                    "User is Contributor": user_is_contributor,
                    "Has Verified Email": has_verified_email,
                    "Accepts Followers": accept_followers
                }, ignore_index=True)

                # Add the user to the set of added users
                added_users.add(username)

except Exception as e:
    print(f"An error occurred: {e}")

# Specify the Excel file path
EXCEL_FILE_PATH = 'potential_bot_accounts.xlsx'

# Export the DataFrame to an Excel file
bot_df.to_excel(EXCEL_FILE_PATH, index=False)

print("Excel file created successfully.")

# Load the Excel file using openpyxl
workbook = load_workbook(EXCEL_FILE_PATH)

# Select the active sheet
sheet = workbook.active

# Iterate through the columns and set the column width to the maximum length of data in each column
for i, column_cells in enumerate(sheet.iter_cols(), 1):
    MAX_LENGTH = max(len(str(cell.value)) for cell in column_cells)
    ADJUSTED_WIDTH = MAX_LENGTH + 2  # Add some padding
    sheet.column_dimensions[get_column_letter(i)].width = ADJUSTED_WIDTH

# Save the modified Excel file
workbook.save(EXCEL_FILE_PATH)

print("Potential Bot Accounts:")
print(bot_df)
