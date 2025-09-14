#!/usr/bin/env python3
# python wikipedia_spacy_processor.py ../data/spacy_pipeline/_revisions.json
import os
import json
import bz2
import mwxml
import logging
import argparse
from tqdm import tqdm
from typing import List, Dict, Any

from modules.spacy_processor import SpacyNameEntityRecognizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _extract_names_with_ner(text: str, name_entity_recognizer: Any) -> List[str]:
    """Extracts names from the given text using a NER processor."""
    try:
        matches = name_entity_recognizer.extract_names(text)
    except Exception as e:
        logger.error(f"Error during NER extraction: {e}")
        return []
    return [match.get("word", "") for match in matches if "word" in match]


def _process_wikipedia_pages_with_spacy(
    input_path: str,
    revision_mapping: Dict[int, str],
    spacy_ner: SpacyNameEntityRecognizer,
) -> None:
    """Processes a Wikipedia dump file using Spacy NER extraction."""
    open_method = bz2.open if input_path.endswith(".bz2") else open
    try:
        with open_method(input_path, "rb") as dump_file:
            dump = mwxml.Dump.from_file(dump_file)
            for page in tqdm(dump, desc=f"Processing {input_path}"):
                for revision in tqdm(list(page), desc="Processing Revisions", leave=False):
                    if not getattr(revision, "text", None):
                        continue
                    if revision.id in revision_mapping:
                        spacy_names = _extract_names_with_ner(revision.text, spacy_ner)
                        result = {"revision_id": str(revision.id), "names": spacy_names}
                        output_path = revision_mapping[revision.id]
                        try:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "w", encoding="utf-8") as out_f:
                                json.dump(result, out_f, indent=4, ensure_ascii=False)
                        except Exception as e:
                            logger.error(f"Error writing output for revision {revision.id}: {e}")
    except Exception as e:
        logger.error(f"Error processing dump file {input_path}: {e}")


def process_dumps_with_spacy(json_path: str) -> None:
    """Processes Wikipedia dumps using Spacy NER extraction based on a JSON configuration file."""
    try:
        spacy_ner = SpacyNameEntityRecognizer(use_gpu=False)
    except Exception as e:
        logger.error(f"Failed to initialize SpacyNameEntityRecognizer: {e}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON config from {json_path}: {e}")
        return

    for item in data:
        input_path = item.get("input_file_name")
        revision_mapping = {rev["id"]: rev["output_file_name"] for rev in item.get("revisions", [])}
        logger.info(f"Processing {input_path} with NER extraction...")
        _process_wikipedia_pages_with_spacy(input_path, revision_mapping, spacy_ner)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process Wikipedia dumps using spaCy-based Named Entity Recognition (NER)."
    )
    parser.add_argument(
        "json_config",
        help="Path to the JSON configuration file."
    )
    args = parser.parse_args()

    process_dumps_with_spacy(args.json_config)


if __name__ == "__main__":
    main()
