import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Standardizes raw supplier text strings.
    Handles: lowercase, trimming, HTML removal, unicode, and punctuation spaces.
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove HTML tags using Regex
    clean_html = re.sub(r'<[^>]*>', ' ', text)
    
    # Normalize Unicode (handles German umlauts like ä, ö, ü properly)
    clean_unicode = unicodedata.normalize('NFKC', clean_html)
    
    # Normalize Punctuation Spaces (replace multiple punctuation/spaces with single space)
    clean_punc = re.sub(r'\s+', ' ', clean_unicode)
    
    # Lowercase and Trim Whitespace
    return clean_punc.strip().lower()