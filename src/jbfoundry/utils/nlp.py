"""
NLP utilities for text processing.
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from typing import List, Set


def get_stopwords() -> Set[str]:
    """
    Get a set of English stopwords.
    
    Returns:
        Set of stopwords
    """
    try:
        return set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords')
        return set(stopwords.words('english'))


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into words.
    
    Args:
        text: Input text
        
    Returns:
        List of tokens
    """
    try:
        return word_tokenize(text)
    except LookupError:
        nltk.download('punkt')
        return word_tokenize(text)


def remove_non_dict_words(text: str, min_word_length: int = 3) -> str:
    """
    Remove words that are not in the dictionary.
    
    Args:
        text: Input text
        min_word_length: Minimum length of words to check
        
    Returns:
        Text with non-dictionary words removed
    """
    # This is a placeholder. In a real implementation, we would use
    # a dictionary check like PyEnchant or similar.
    words = tokenize_text(text)
    result = []
    
    for word in words:
        # Keep short words, punctuation, and words that pass a dictionary check
        if len(word) < min_word_length or not word.isalpha():
            result.append(word)
        # Here we would check if word is in dictionary
        else:
            result.append(word)
    
    return ' '.join(result)


def clean_text(text: str) -> str:
    """
    Clean text by removing redundant whitespace and special characters.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Remove redundant whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters except those that are meaningful in text
    text = re.sub(r'[^\w\s.,!?;:\'"-]', '', text)
    
    return text.strip()


def extract_key_phrases(text: str, num_phrases: int = 5) -> List[str]:
    """
    Extract key phrases from text.
    
    Args:
        text: Input text
        num_phrases: Number of phrases to extract
        
    Returns:
        List of key phrases
    """
    # This is a simplified implementation
    words = tokenize_text(text)
    stopword_set = get_stopwords()
    
    # Filter out stopwords and short words
    content_words = [
        word.lower() for word in words 
        if word.lower() not in stopword_set 
        and len(word) > 3
        and word.isalpha()
    ]
    
    # Count word frequencies
    word_freq = {}
    for word in content_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get most frequent words
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    key_words = [word for word, _ in sorted_words[:num_phrases]]
    
    return key_words


def find_sentence_boundaries(text: str) -> List[tuple]:
    """
    Find the start and end indices of sentences in text.
    
    Args:
        text: Input text
        
    Returns:
        List of (start, end) tuples for each sentence
    """
    sentences = nltk.sent_tokenize(text)
    boundaries = []
    start = 0
    
    for sentence in sentences:
        # Find the actual index where this sentence starts
        sent_start = text.find(sentence, start)
        if sent_start == -1:
            continue
        
        sent_end = sent_start + len(sentence)
        boundaries.append((sent_start, sent_end))
        start = sent_end
    
    return boundaries


def replace_with_synonyms(text: str, rate: float = 0.2) -> str:
    """
    Replace words with synonyms.
    
    Args:
        text: Input text
        rate: Rate of words to replace
        
    Returns:
        Text with some words replaced by synonyms
    """
    # This is a placeholder. In a real implementation, we would use
    # a synonym dictionary or a library like WordNet.
    return text  # No actual replacement in this placeholder 