import nltk
import os
from tools.config.logger_config import init_logger, logging

logger = logging.getLogger(__name__)
logger.info("load_nltk_data Module Logging Set")
init_logger()

def load_nltk_data():
    """
    Downloads the required NLTK resources only when necessary.
    """
    nltk.download('maxent_ne_chunker')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt_tab')
    nltk.download('wordnet')  
    nltk.download('averaged_perceptron_tagger')  
    nltk.download('vader_lexicon')  
    nltk.download('stopwords')  
    nltk.download('punkt')  
    nltk.download('maxent_ne_chunker')  
    nltk.data.path.append('./nltk_data')
    nltk_data_path = './nltk_data'  
#    logger.info("NLTK data path: %s", nltk.data.path)
    if not os.path.exists(nltk_data_path):
        os.makedirs(nltk_data_path)

    # Ensure NLTK knows where to find the local data
    nltk.data.path.append(nltk_data_path)

    # Load specific resources manually if they are not already downloaded
    if not os.path.exists(os.path.join(nltk_data_path, 'vader_lexicon')):
        nltk.download('vader_lexicon', download_dir=nltk_data_path)

    if not os.path.exists(os.path.join(nltk_data_path, 'tokenizers/punkt')):
        nltk.download('punkt', download_dir=nltk_data_path)
        
    if not os.path.exists(os.path.join(nltk_data_path, 'maxent_ne_chunker_tab')):
        nltk.download('maxent_ne_chunker', download_dir=nltk_data_path)
        
    if not os.path.exists(os.path.join(nltk_data_path, 'averaged_perceptron_tagger')):
        nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_path)
        
    if not os.path.exists(os.path.join(nltk_data_path, 'stopwords')):
        nltk.download('stopwords', download_dir=nltk_data_path)
        
    if not os.path.exists(os.path.join(nltk_data_path, 'wordnet')):
        nltk.download('wordnet', download_dir=nltk_data_path)

if __name__ == "__main__":
    load_nltk_data()
    logger.info("NLTK data downloaded.")
