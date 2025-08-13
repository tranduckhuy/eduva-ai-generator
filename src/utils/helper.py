
# General utility functions for handling language normalization
def normalize_language(language: str) -> str:
    if not language or not isinstance(language, str):
        return "vietnamese"
    
    lang_lower = language.lower().strip()
    
    english_variations = ["en", "eng", "english", "en-us", "en-gb", "en_us", "en_gb"]
    
    if lang_lower in english_variations:
        return "english"
    
    # Default to Vietnamese for all other cases
    return "vietnamese"