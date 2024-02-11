# Reddit Scraper & Analyzer

The **Reddit Scraper & Analyzer** is a Python application designed to scrape data from Reddit and analyze user and submission information to help identify potential bots, trolls, or suspicious accounts. It provides functionalities for scraping posts and comments from Reddit, extracting relevant user and submission data, performing analysis, and generating reports.

## Features

Scraping: Retrieve posts and comments from Reddit using specified parameters such as subreddit, post sorting method, etc.
Data Extraction: Extract user and submission data including usernames, karma, account creation dates, post titles, scores, etc.
Analysis: Analyze user behavior, account characteristics, and other attributes to identify potential bots or trolls.
Reporting: Generate reports summarizing the findings of the analysis, including statistics, insights, and visualizations.
Customization: Configure scraping parameters, analysis criteria, and reporting formats to suit specific needs.
Integration: Easily integrate with other Python libraries and tools for additional analysis or processing.
Requirements
Python 3.x
Required Python packages (specified in requirements.txt)

## Installation

### 1. Clone this repository to your local machine

```bash
git clone https://github.com/Hotrod369/Reddit-Bot-Finder.git
```

### 2. Navigate to the project directory

```bash
cd Reddit-Bot-Finder
```

### 3. Install the required Python packages using pip

```bash
pip install -r requirements.txt
```

### 4. Set up NLTK (Natural Language Toolkit)

The project uses NLTK for sentiment analysis. To download the necessary NLTK data, run the setup script provided:

```bash
python setup_nltk.py
```

This script will download the vader_lexicon dataset, which is required for sentiment analysis.

## Usage

**To effectively use the Universal Reddit Scraper & Analyzer, follow these steps:**

### 1. Setting Up config.json

First, configure your config.json file in the project directory with your Reddit API credentials and desired scraping parameters:

```json
{
    "subreddit": "SUBREDDIT_NAME",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "username": "YOUR_REDDIT_USERNAME",
    "password": "YOUR_REDDIT_PASSWORD",
    "user_agent": "Reddit Scraper (by u/YOUR_USERNAME)",
    "post_sort": {
        "method": "new",
        "limit": 10000
    },
    "notes": [
        "You can choose from 'top', 'hot', 'new', 'rising', or 'controversial' for post sorting.",
        "Account Age Threshold is set in years; it can be a decimal."
    ],
    "karma_threshold": 5000,
    "account_age_threshold": 2
}
```

**subreddit:** Specify the subreddit from which you want to scrape data.
**client_id & client_secret:** Your Reddit application's credentials.
**username & password:** Your Reddit account credentials for authentication.
**user_agent:** A descriptive user agent to help Reddit identify your script.
**post_sort:** Defines how you want to sort the posts and the number of posts to scrape.
**notes:** Additional notes or parameters for reference.
**karma_threshold & account_age_threshold:** Criteria for analyzing and identifying potential bots.

### 2. Running the Scraper

**Execute the scraper.py script to start scraping Reddit based on the parameters set in your config.json:**

```bash
python scraper.py
```

This step will collect posts and comments from the specified subreddit and save them into JSON files (user_data.json and submission_data.json).

### 3. Analyzing the Data

**After data collection, proceed with the analyzer.py script to analyze the scraped data:**

```bash
python analyzer.py
```

This script performs sentiment analysis on comments, evaluates user data, and identifies potential bots or suspicious accounts based on the karma and account age thresholds specified in your config. It generates an Excel report (potential_bot_accounts.xlsx) summarizing the findings.

### 4. Reviewing the Analysis

Open the generated Excel report to review detailed analysis results. The report will highlight users flagged as potential bots, showing their karma, account age, and average sentiment scores, along with other relevant information.

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

PRAW: Python Reddit API Wrapper
NLTK: Natural Language Toolkit for text processing and analysis
