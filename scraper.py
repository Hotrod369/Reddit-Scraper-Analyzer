'''
Scrapes top 100 users per karma in the last 3 months
'''
import json
import datetime as dt
import main

# Function to fetch user details from Reddit's API
def fetch_user_info(reddit, username):
    try:
        user = reddit.redditor(username)
        user_data = {
            'created_utc': user.created_utc
            # Add other user details if needed
        }
        print(user.created_utc)
        return user_data
    except Exception as e:
        print(f"Error fetching user info for {username}: {e}")
        return None
    
if __name__ == "__main__":
    config = main.load_config()  # Load the configuration from main module
    reddit = main.login(config)  # Login using the config data
    subreddit_name = config["subreddit"]
    subreddit = reddit.subreddit(subreddit_name)

    # Create dictionaries to store user data and submission data
    user_data = {}
    post_data = {}
    comments_data = []

    # Get the list of moderators
    moderators = [mod.name for mod in subreddit.moderator()]
    user = user_data

    # Check the post sorting method from the config
    post_sort = config.get("post_sort", "top")  # Default to "top" if not specified

    # List of valid post sorting methods
    valid_sort_methods = ["top", "hot", "new", "rising", "controversial"]

    # Check if the specified sort method is valid
    if post_sort not in valid_sort_methods:
        raise ValueError(f"Invalid post_sort value in config.json. Available options: {', '.join(valid_sort_methods)}")

    # Print the note from the config, if available
    notes = config.get("notes", "")
    if notes:
        print("Note:", notes)

    # Iterate through the posts based on the selected sort method
    if post_sort == "top":
        posts = subreddit.top(limit=10000)
    elif post_sort == "hot":
        posts = subreddit.hot(limit=2500)
    elif post_sort == "new":
        posts = subreddit.new(limit=500)
    elif post_sort == "rising":
        posts = subreddit.rising(limit=10000)
    elif post_sort == "controversial":
        posts = subreddit.controversial(limit=10000)

    # Print a message to indicate scraping has started
    print(f'Starting scraping with sort order: {post_sort}')

# Initialize comments_data list outside the loop
comments_data = []

try:
    # Iterate through the posts based on the selected sort method
    for submission in posts:
        author = submission.author.name if submission.author else 'Deleted'
                
        # Skip posts made by moderators or deleted authors
        if author in moderators or author == 'Deleted':
            continue

        # Fetch the user's information separately
        user_info = fetch_user_info(reddit, author)
        if user_info:
            # Calculate the account age using the retrieved creation date
            if 'created_utc' in user_info:
                creation_date = dt.datetime.utcfromtimestamp(user_info['created_utc'])
                account_age_years = (dt.datetime.utcnow() - creation_date).days / 365.25
                # Add the user's information to the user_data dictionary
                user_data[author] = {
                    'User': author,
                    'Posts': 1,  # Update the number of posts for this user
                    'Comments': 0,  # Initialize comments count
                    'Karma': submission.score,  # Update the karma for this user
                    'created_utc': user_info['created_utc']  # Add the account creation date
                    # Add other user details if needed
                }
        else:
            # Handle the case where user_info is None (error fetching user info)
            account_age_years = None
            
        # Initialize user data if not already present
        if author not in user_data:
            user_data[author] = {
                'User': author,
                'Posts': 0,
                'Comments': 0,
                'Karma': 0,
                # Add other user-related fields here
            }

        # Update user data for the current author
        user_data[author]['Posts'] += 1
        user_data[author]['Karma'] += submission.score
        
        # Initialize comments_data list for the current submission
        comments_data = []

        # Fetch comments for the current submission
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            # Skip comments made by Automoderator
            if comment.author and comment.author.name.lower() == "automoderator":
                continue
            
            # Process each comment and extract relevant information
            comment_author = comment.author.name if comment.author else 'Deleted'
            comment_body = comment.body
            comment_score = comment.score
            comment_id = comment.id
            # Add other relevant comment attributes here

            # Create a dictionary to store the comment data
            comment_data = {
                'author': comment_author,
                'body': comment_body,
                'score': comment_score,
                'id': comment_id,
                # Add other relevant comment attributes here
            }
            # Append the comment data to the list
            comments_data.append(comment_data)
            
        # Add submission data to post_data dictionary, including comments
        post_data[submission.id] = {
            'User': author,
            'title': submission.title,
            'score': submission.score,
            'id': submission.id,
            'url': submission.url,
            'created_utc': submission.author.created_utc,
            'comments': comments_data,  # Add the comments data here
            'user_is_contributor': submission.author.user_is_contributor if submission.author and hasattr(submission.author, 'user_is_contributor') else False,
            'awardee_karma': submission.author.awardee_karma if submission.author else 0,
            'awarder_karma': submission.author.awarder_karma if submission.author else 0,
            'total_karma': submission.author.total_karma if submission.author else 0,
            'has_verified_email': submission.author.has_verified_email if submission.author and hasattr(submission.author, 'has_verified_email') else False,
            'link_karma': submission.author.link_karma if submission.author and hasattr(submission.author, 'link_karma') else 0,
            'comment_karma': submission.author.comment_karma if submission.author and hasattr(submission.author, 'comment_karma') else 0,
            'accept_followers': submission.author.accept_followers if submission.author and hasattr(submission.author, 'accept_followers') else False,
        }

except Exception as e:
    print(f"An error occurred: {e}")

# Write user_data to user_data.json
with open('user_data.json', 'w', encoding='utf-8') as user_file:
    json.dump(user_data, user_file, ensure_ascii=False, indent=4)
print("User data written to user_data.json")

# Write submission_data to submission_data.json
with open('submission_data.json', 'w', encoding='utf-8') as submission_file:
    json.dump(post_data, submission_file, ensure_ascii=False, indent=4)
print("Submission data written to submission_data.json")

# Print a message to indicate scraping is complete
print('Scraping complete.')