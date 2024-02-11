import nltk

def download_nltk_data():
    # List of NLTK resources to download
    resources = [
        'vader_lexicon',  # For sentiment analysis
        # Add any other NLTK resources needed for your application
    ]

    for resource in resources:
        print(f"Downloading NLTK resource: {resource}...")
        nltk.download(resource)
    
    print("NLTK resources have been downloaded.")

if __name__ == "__main__":
    download_nltk_data()
