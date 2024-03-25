# Reddit Scraper & Analyzer

## Overview

The **Reddit Scraper & Analyzer** is an advanced tool designed to navigate through the complexities of Reddit's vast data landscape, extracting and processing data to uncover insightful patterns and behaviors. It is particularly adept at identifying anomalous activities indicative of bots, trolls, or other potentially malicious entities.

Utilizing the **Python Reddit API Wrapper (PRAW)** for robust data extraction, the tool gathers comprehensive information from specified subreddits, including posts, comments, and user metrics. This data then undergoes detailed analysis, leveraging the **Natural Language Toolkit (NLTK)** for sophisticated text processing and sentiment analysis. This analysis assesses various parameters such as karma scores, account ages, and activity patterns to detect irregularities and understand the sentiment behind user comments.

Additionally, the system integrates **PostgreSQL**, a powerful open-source relational database, to manage and store the large volumes of data efficiently. This allows for advanced querying capabilities and secure storage of the scraped data, facilitating complex data analysis tasks.

The **Reddit Scraper & Analyzer** is built with flexibility in mind, enabling users to customize the scraping and analysis processes according to specific research needs or investigative criteria. It encapsulates the complexity of its operations behind a user-friendly interface, making advanced data analysis accessible to those with limited technical backgrounds.

Serving as a critical resource for digital researchers, social media analysts, and cybersecurity professionals, the **Reddit Scraper & Analyzer** provides the necessary data and insights to understand and act upon the dynamic and often opaque world of Reddit.

## Features

**Data Scraping:** Utilize the scraper.py module to collect posts, comments, and user information from specified subreddits.

**JSON File Generation:** The scraper will output two JSON files containing user data (user_data.json) and submission data (submission_data.json). Here are examples of the expected JSON structures:

user_data.json:

```json
{
    "username": "example_user",
    "Karma": 12345,
    "created_utc": 1532312506.0,
    ...
}
```

submission_data.json:

```json
{
    "id": "submission_id",
    "User": "example_user",
    "title": "Interesting post title",
    ...
}
```

**Data Extraction:** Extract user and submission data including usernames, karma, account creation dates, post titles, scores, etc.
**Analysis:** Analyze user behavior, account characteristics, and other attributes to identify potential bots or trolls.
**Reporting:** Generate reports summarizing the findings of the analysis, including statistics, insights, and visualizations.
**Customization:** Configure scraping parameters, analysis criteria, and reporting formats to suit specific needs.
**Integration:** Easily integrate with other Python libraries and tools for additional analysis or processing.
**Requirements:**

- Python 3.12.1

**Required Python packages** (specified in requirements.txt)

- PRAW 7.7.1
- Pandas 2.2.1
- Openpyxl 3.1.2
- Requests 2.31.0
- NLTK 3.8.1
- psycopg2-binary> 2.9.9

## Installation

### 1. Clone this repository to your local machine

`git clone https://github.com/Hotrod369/Reddit-Scraper-Analyzer.git`

### 2. Navigate to the project directory

`cd Reddit-Scraper-Analyzer`

### 3. Install the required Python packages using the requirements.txt by running the following command file

`pip install -r requirements.txt`

## Database Setup

### Installing PostgreSQL

1. **Download PostgreSQL:** Go to the official [PostgreSQL download page](https://www.postgresql.org/download/) and select the appropriate version for your operating system. Follow the instructions to download and install PostgreSQL.

2. **Install PostgreSQL:** Run the installer and follow the prompts to set up PostgreSQL on your machine. During installation you will be prompted to enter a password for the superuser profile don't lose it, as you will need it to access the PostgreSQL database server.

### Creating the Database

**Access the PostgreSQL command line tool:**

1. On Windows, you can use the SQL Shell (psql) that comes with the

- PostgreSQL installation.
- On macOS and Linux, you can open a terminal and enter psql to access the PostgreSQL command line tool.

2. **Log in to PostgreSQL:**

`psql -U postgres`

Enter the password for the postgres user when prompted.

3. **Create a new database for your project:**

`CREATE DATABASE reddit_analysis;`

4. **Connect to the newly created database:**

`\c reddit_analysis`

### Creating the Database Tables

1. **Execute the SQL script** to create the tables needed for your application. You can copy and paste the commands from your database_setup.sql.txt file into the psql command line tool or use a PostgreSQL GUI like pgAdmin.

2. **Verify the tables creation by running:**

`\dt`

This command will list all tables in the current database, and you should see users, submissions, and comments listed.

Automating Table Clearing (Optional)
If you wish to clear the tables automatically when running json_to_db.py, include the provided try block in your Python script as indicated in the database_setup.sql.txt file. This is useful for development or testing purposes but should be used with caution in a production environment.

## Usage

**To effectively use the Universal Reddit Scraper & Analyzer, follow these steps:**

### 1. Setting Up config.json

**Configuration Details**
Ensure your config.json file is set up correctly to define scraping parameters and database connection details. The config.json should be located in the tools/config directory.

First, configure your config.json file in tools/config directory with your Reddit API credentials and desired scraping parameters. You will also need to enter your PostgreSQL credentials.

```json
{
    "database": {
        "dbname": "reddit_analysis",
        "user": "postgres",
        "password": "password used during installation",
        "host": "localhost"
    },
    "subreddit": "SUBREDDIT_NAME",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "username": "YOUR_REDDIT_USERNAME",
    "password": "YOUR_REDDIT_PASSWORD",
    "user_agent": "Reddit Scraper (by u/YOUR_USERNAME)",
    "post_sort": {
        "method": "new",
        "limit": 500
    },
    "notes": [
        "You can choose from 'top', 'hot', 'new', 'rising', or 'controversial' for post sorting.",
        "Account Age Threshold is set in years; it can be a decimal."
    ],
    "karma_threshold": 2000,
    "account_age_threshold": 0.5
}
```

**subreddit:** Specify the subreddit from which you want to scrape data. Multiple subreddits can be scraped by separating with a `+` like this `"subreddit1+subreddit2+subreddit3"`
**client_id & client_secret:** Your Reddit application's credentials.
**username & password:** Your Reddit account credentials for authentication.
**user_agent:** A descriptive user agent to help Reddit identify your script.
**post_sort, method and limit:** Defines how you want to sort the posts and the number of posts to scrape.
**notes:** Additional notes or parameters for reference.
**karma_threshold & account_age_threshold:** Criteria for analyzing and identifying potential bots.

### 2. Running the app

**Execute the main.py script to start scraping Reddit based on the parameters set in your config.json:**

`python -m main`

This step will collect posts and comments from the specified subreddit and save them into JSON files (user_data.json and submission_data.json).

Then performs sentiment analysis on comments, evaluates user data, and identifies potential bots or suspicious accounts based on the karma and account age thresholds specified in your config. It generates an Excel report (potential_bot_accounts.xlsx) summarizing the findings.

### 4. Reviewing the Analysis

Open the Excel files generated after the analysis to view detailed results, including karma, account age, sentiment scores, and more.

**Example Excel Outputs**
Below are example outputs generated by the Reddit Scraper & Analyzer, which can be found in the [example_outputs](./example_outputs) directory:

- **User Analysis**: [users_analysis.xlsx](example-outputs/users_analysis.xlsx)
- **Comment Analysis**: [comment_analysis.xlsx](example-outputs/comment_analysis.xlsx)
- **Submission Analysis**: [submission_analysis.xlsx](example-outputs/submission_analysis.xlsx)

Please download the files to view the detailed analysis results.

These Excel sheets offer a clear visualization of the data with various metrics important for identifying suspicious account activities.

## Troubleshooting

If you encounter any issues with file creation or other aspects of the workflow:

1. Verify the paths in the configuration are correctly set relative to your current working directory.
2. Check the database connections to ensure they are active and the credentials are accurate.
3. Ensure each individual module operates correctly by running them separately and reviewing the logs for errors.
4. Confirm that all required Python packages listed in `requirements.txt` are installed.

### Creating an Issue

If the problem persists, please create an **issue** (<https://github.com/YourGitHubUsername/Reddit-Scraper-Analyzer/issues/new>) on GitHub with the following information:

- A clear and descriptive title.
- A detailed description of the issue, including the step at which the issue arises.
- The output, logs, or error messages that you receive (if any).
- Steps to reproduce the issue (if applicable).
- Any relevant screenshots or example files (please make sure there's no sensitive data).
- The version of the software or tools you are using, including Python version.

Our team will review the issue and get back to you with a resolution or further questions.

## Contributing

**Contributions are welcome! If you'd like to contribute to the development of this project, please follow these guidelines:**

Fork the repository
Create a new branch (git checkout -b feature-branch)
Make your changes
Commit your changes (git commit -am 'Add new feature')
Push to the branch (git push origin feature-branch)
Create a new Pull Request
License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [**PRAW:**](https://praw.readthedocs.io/en/stable/index.html) Python Reddit API Wrapper
- [**NLTK:**](https://www.nltk.org) Natural Language Toolkit for text processing and analysis
- [**PostgreSQL:**](https://www.postgresql.org) The World's Most Advanced Open Source Relational Database
