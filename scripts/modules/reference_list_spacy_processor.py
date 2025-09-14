import spacy
import re
from modules.utils import filter_wikitext

class SpacyReferenceListProcessor:
    def __init__(self, use_gpu=True):
        """
        Initialize the SpaCy model with optional GPU support.

        Args:
            use_gpu (bool): Whether to require or prefer using a GPU. Defaults to True.
                            If False, forces CPU usage.
        """
        if use_gpu:
            try:
                spacy.require_gpu()
                print("GPU is enabled for SpaCy.")
            except Exception as e:
                print(f"GPU is not available. Falling back to CPU. Error: {e}")
        
        self.nlp = spacy.load("en_core_web_trf")
        self.nlp.disable_pipes("tagger", "parser", "lemmatizer")

    def extract_names(self, wikitext):
        """
        Extract PERSON entities from the given text and return a set of name parts.
        Before adding, each entity is cleaned by replacing non-letter characters with whitespace.
        This ensures names like "Virginijus Šikšnys" retain their valid letters.
        
        Args:
            wikitext (str): The input text to process.
        
        Returns:
            set: A set of name parts (words) extracted from PERSON entities.
        """
        wikitext = filter_wikitext(wikitext)
        doc = self.nlp(wikitext)
        names_set = set()
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                cleaned = re.sub(r'[^\w\s]', ' ', ent.text, flags=re.UNICODE)
                cleaned = re.sub(r'[\d_]', ' ', cleaned, flags=re.UNICODE)
                parts = cleaned.strip().split()
                for part in parts:
                    if not (len(part) == 1 and part.islower()):
                        names_set.add(part)
                        
        return names_set
