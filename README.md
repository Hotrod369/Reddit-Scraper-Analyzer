# Reddit Scraper & Analyzer

## Overview

The **Reddit Scraper & Analyzer** is an advanced tool designed to navigate Reddit’s vast data landscape—extracting and processing data to uncover insightful patterns and behaviors. It is especially useful for detecting anomalous activities such as bot spamming, trolling, or other potentially malicious behavior.

The tool leverages:

- **PRAW (Python Reddit API Wrapper):** For robust data extraction from Reddit.
- **NLTK (Natural Language Toolkit):** For detailed text processing, including sentiment analysis, named entity recognition, lexical diversity, and n‑gram extraction.
- **PostgreSQL:** For efficient storage and querying of the scraped data.
- **Openpyxl & Tqdm:** To generate detailed Excel reports with progress feedback.

Designed with flexibility in mind, the tool allows you to customize scraping and analysis parameters via a configuration file. Whether you're a digital researcher, social media analyst, or cybersecurity professional, the Reddit Scraper & Analyzer delivers the insights you need to understand and act upon Reddit’s dynamic environment.

---

## Features

- **Data Scraping:**  
  Collect posts, comments, and user information from specified subreddits using the `scraper.py` module.

- **JSON File Generation:**  
  The scraper outputs two JSON files:
  - **redditor_data.json:** Contains user data (e.g., username, karma, account creation timestamp, etc.).
  - **submission_data.json:** Contains submission data (e.g., submission ID, title, URL, etc.).

- **Database Integration:**  
  The tool inserts the scraped data into a PostgreSQL database for advanced querying and analysis.

- **Data Analysis:**  
  - **Comment Analysis:** Performs sentiment analysis, named entity recognition, and more on comment text.  
  - **Submission Analysis:** Analyzes submission titles using sentiment analysis and additional NLTK-based metrics (named entities, lexical diversity, common bigrams).  
  - **User Analysis:** Evaluates user behavior and characteristics (e.g., karma, account age, burst activity) to help identify suspicious accounts.

- **Excel Reporting:**  
  Generate comprehensive Excel reports for:
  - **User Analysis:** `user_analysis.xlsx`  
  - **Comment Analysis:** `comment_analysis.xlsx`  
  - **Submission Analysis:** `submission_analysis.xlsx`

- **Customization:**  
  Adjust scraping parameters, analysis thresholds, and reporting formats via a centralized `config.json` file.

---

## Requirements

- **Python Version:** 3.12.1 (or compatible)
- **Required Python Packages:** (see `requirements.txt`)
  - PRAW 7.7.1  
  - Pandas 2.2.1  
  - Openpyxl 3.1.2  
  - Requests 2.31.0  
  - NLTK 3.8.1  
  - psycopg2-binary > 2.9.9  
  - tqdm 4.66.2  
  - *(and others as specified in requirements.txt)*

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Hotrod369/Reddit-Scraper-Analyzer.git
```

### 2. Navigate to the Project Directory

```bash
cd Reddit-Scraper-Analyzer
```

### 3. Install the Required Packages

```bash
pip install -r requirements.txt
```

---

## Database Setup

### Installing PostgreSQL

1. **Download PostgreSQL:**  
   Visit the [PostgreSQL download page](https://www.postgresql.org/download/) and follow the instructions for your operating system.

2. **Install PostgreSQL:**  
   Run the installer and set a password for the superuser (postgres). Keep this password handy for database configuration.

---

### Creating / Updating the Database

> **Important:** If you have used this tool previously, please **drop your old database tables** and recreate them using the **new** schema. The schema has changed (table columns and keys), and older tables are incompatible.

1. **Access the PostgreSQL Command Line Tool (psql):**  
   - On Windows: Use the SQL Shell (psql) provided with PostgreSQL.  
   - On macOS/Linux: Open a terminal and run `psql -U postgres`.

2. **Create a New Database (if you haven’t already):**

```sql
CREATE DATABASE reddit_analysis;
```

3. **Connect to the Database:**

```sql
\c reddit_analysis
```

3a. **Drop Existing Tables (if upgrading from an older version):**

```sql
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS users;
```

4. **Create the New Tables:**

```sql
CREATE TABLE users (
  redditor_id VARCHAR(255) PRIMARY KEY,
  redditor VARCHAR(255) UNIQUE,
  created_utc BIGINT,
  link_karma INTEGER,
  comment_karma INTEGER,
  total_karma INTEGER,
  is_employee BOOLEAN,
  is_mod BOOLEAN,
  is_gold BOOLEAN,
  dormant_days INTEGER,
  has_verified_email BOOLEAN,
  accepts_followers BOOLEAN,
  redditor_is_subscriber BOOLEAN
);

CREATE TABLE submissions (
  submission_id VARCHAR(255) PRIMARY KEY,
  author VARCHAR(255),
  title TEXT,
  submission_score INTEGER,
  url TEXT,
  submission_created_utc BIGINT,
  over_18 BOOLEAN
);

CREATE TABLE comments (
  comment_id VARCHAR(255) PRIMARY KEY,
  comment_author VARCHAR(255),
  comment_created_utc BIGINT,
  body TEXT,
  comment_score INTEGER,
  is_submitter BOOLEAN,
  edited BOOLEAN,
  link_id VARCHAR(255)
);
```

You can verify table creation by running `\dt` in psql.

---

## Configuration

This project requires a **`config.json`** file containing your Reddit API credentials, database connection parameters, and various scraper/analysis settings. A template file named **`Rename-to-config.json`** is provided in `tools/config`.

1. **Locate the Template File**  
   Go to `tools/config/Rename-to-config.json` and open it in a text editor.

2. **Rename & Update**  
   - Rename the file to **`config.json`**.  
   - Replace the placeholder values (`xxxxxx`) with your **actual** credentials and desired parameter values. For example:
     ```json
     {
       "database": {
         "dbname": "reddit_analysis",
         "user": "postgres",
         "password": "MySecretPassword",
         "host": "localhost"
       },
       "subreddit": "mySubreddit+myOtherSubreddit",
       "client_id": "myRedditAppClientID",
       "client_secret": "myRedditAppSecret",
       "username": "myRedditUsername",
       "password": "myRedditPassword",
       "user_agent": "Reddit Scraper & Analyzer (by u/YourUsername)",
       "max_concurrent_requests": 4,
       "submission_sort": {
         "method": "new",
         "limit": 25
       },
       "comments_limit": 250,
       "submissions_limit": 250,
       "karma_threshold": 500,
       "account_age_threshold": 0.5,
       "inactivity_period": 3,
       "burst_period": 1,
       "notes": [
          "Configure how submissions are fetched: ‘method’ controls sorting (`new`, `hot`, etc.) and `limit` balances depth vs speed (e.g., lower limits for quick scans, higher for thorough research).",

          "Fine-tune `comments_limit` and `submissions_limit` here to adjust the number of comments/submissions per post or user—lower values shorten runtime, higher values yield richer context.",

          "Use `karma_threshold` and `account_age_threshold` to flag potentially suspicious accounts: lower values catch new or low-engagement users, higher values focus on matured profiles.",

          "Adjust `inactivity_period` and `burst_period` to detect bursty activity patterns—short gaps highlight rapid reposting, longer gaps reduce false positives from normal behavior cycles.",

          "Use `max_concurrent_requests` to control how many API calls run in parallel—lower values help avoid rate‑limit errors, higher values speed up scraping on faster connections."
       ]
     }
     ```

3. **Parameter Descriptions:**
Below is an in‑depth guide to every setting in the example above:

 - **database**
Holds your PostgreSQL connection info.

    * dbname, user, password, host: must all match your local or remote database setup.

- **subreddit**
A single string of subreddit names separated by + (e.g. "python+learnprogramming"). The scraper will iterate through each.

- **client_id, client_secret, username, password,user_agent**
Your Reddit API app credentials and login.

    * user_agent should be unique and descriptive per Reddit’s API rules (e.g. including your Reddit username).

- **max_concurrent_requests**  
Maximum number of simultaneous requests the scraper will fire off.

    * Lower values (e.g. 1–2) reduce the chance of hitting Reddit’s rate limits but slow throughput.

    * Higher values speed up scraping on powerful machines/network connections but risk more “429” responses.

- **submission_sort.method**
One of "new", "hot", "top", "rising", or "controversial".

    * Use new for purely chronological scraping.

    * hot/top surfaces the most popular content but may miss fresh posts.

    * rising is great for catching early viral threads.
- **submission_sort.limit**
How many posts to fetch per subreddit.

    * Lower values (10–50) give a quick snapshot; higher values (250+) dig deeper but increase runtime and API calls.

 - **comments_limit**
Maximum number of comments to fetch per submission.

    * If you’re hunting bot networks or spam threads, you may need hundreds; for a light survey, 10–50 suffices.

 - **submissions_limit**
When fetching each user’s history (link and comment karma analysis), how many of their own submissions to pull.

    * Controls the depth of user profiling; high values slow things down but yield richer “burst activity” signals.

 - **karma_threshold**
A floor for “total karma” below which accounts may be flagged.

    * Useful for spotting throwaway or drive‑by accounts; raising this makes detection stricter.

 - **account_age_threshold**
Age in years (can be fractional) below which accounts are considered “young.”

    * Combines with inactivity/burst metrics to pinpoint newly created spam bots.

 - **inactivity_period & burst_period**
Used to detect “burst” posting behavior:

    * Inactivity period (days): minimum gap of no posts before a suspicious burst.

    * Burst period (days): subsequent rapid‑fire posting window.

    * For example, inactivity_period: 3 and burst_period: 1 flags accounts silent for 3+ days then posting multiple times in a day.

**notes**
A free‑form array to document any custom tweaks, reminders, or special instructions for your own reference.

4. **Save & Verify**  
   Ensure your final file is named **`config.json`** and placed in the `tools/config` directory.  
   When you run the scraper or `main.py`, it will load these parameters to log into Reddit and connect to your database.

That’s it! You now have a properly configured **`config.json`**. Once your credentials and parameters are in place, you can proceed with [running the tool](#usage) to scrape data, insert it into the database, and generate Excel reports.

---

## Usage

To run the complete application (scraping, JSON→DB insertion, analyses, and Excel generation), execute the `main.py` script from the root directory:

```bash
python main.py
```

**What Happens**:

1. **Scraper:**  
   - The `scraper.py` module logs into Reddit and fetches posts, comments, and user data from the specified subreddits.  
   - It writes two JSON files to the `analysis_results/` directory: `redditor_data.json` and `submission_data.json`.

2. **Database Insertion:**  
   - The `json_to_db.py` script reads those JSON files and inserts them into your PostgreSQL database using asyncpg.

3. **Analyses & Excel Generation:**  
   - **Comment Analysis**: Performs sentiment and text analysis on comments.  
   - **Submission Analysis**: Additional metrics for each submission (sentiment, lexical diversity, etc.).  
   - **User Analysis**: Karma, account creation, burst activity, etc.  
   - Each analysis is written to an Excel file in the `analysis_results/` folder.

### Command-Line Arguments

`main.py` supports optional flags for partial runs:

- `--excel-only`  
  Runs only the Excel generation modules (no scraping, no JSON→DB).
- `--scraper-only`  
  Runs only the scraper to produce JSON files (no DB insertion or Excel generation).
- `--json-to-db-only`  
  Runs only the JSON→DB insertion step (assumes JSON files exist).
- `--comment-analysis-excel-only`  
  Generates only the **comment analysis** Excel file.
- `--submission-excel-only`  
  Generates only the **submission analysis** Excel file.
- `--user-analysis-excel-only`  
  Generates only the **user analysis** Excel file.

For example:

```bash
# Only run scraper to produce the JSON files
python main.py --scraper-only

# Only run DB insertion
python main.py --json-to-db-only

# Only generate the comment analysis Excel
python main.py --comment-analysis-excel-only
```

If **no arguments** are provided, it runs the **full pipeline** (scraping → DB insertion → analyses → Excel).

---

## Reviewing the Analysis

After the application completes, open the Excel files in the `analysis_results` directory to review the detailed reports. The reports include:

- **User Analysis:**  
  Metrics such as karma, account age, dormant days, etc.

- **Comment Analysis:**  
  Sentiment scores, named entities, lexical diversity, and duplicate detection.

- **Submission Analysis:**  
  Sentiment, named entities, lexical diversity, and n-gram data extracted from submission titles.

---

## Troubleshooting

1. **Module Errors:**  
   If you encounter module import errors (e.g., for `tqdm`), ensure that you run the application with the correct Python interpreter:

   ```bash
   python main.py
   ```

   Also, verify your environment’s `PYTHONPATH` and consider using a virtual environment.

2. **Database Issues:**  
   - Ensure that PostgreSQL is running, that the new database tables have been created with the updated schema, and that the credentials in `config.json` are correct.
   - If you previously used an older version of this tool, you may need to drop your old tables and re-run the updated create-tables script (see above).

3. **Logging:**  
   Check the log output for error messages or stack traces. If an analysis module isn’t working as expected, try running it individually via the CLI flags.

4. **Rate Limits:**  
   The scraper includes a basic rate-limit handler. If you see warnings about sleeping for a certain number of seconds, that’s normal. The script will pause until it can safely make more requests to Reddit’s API.

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-branch`.
3. Make your changes.
4. Commit your changes: `git commit -am 'Describe your changes'`.
5. Push the branch: `git push origin feature-branch`.
6. Create a pull request on GitHub.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Acknowledgements

- **PRAW:** [https://praw.readthedocs.io/en/stable/](https://praw.readthedocs.io/en/stable/)
- **NLTK:** [https://www.nltk.org/](https://www.nltk.org/)
- **PostgreSQL:** [https://www.postgresql.org/](https://www.postgresql.org/)
- **Openpyxl:** [https://openpyxl.readthedocs.io/](https://openpyxl.readthedocs.io/)
- **Tqdm:** [https://tqdm.github.io/](https://tqdm.github.io/)