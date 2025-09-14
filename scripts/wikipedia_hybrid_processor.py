#!/usr/bin/env python3
# python wikipedia_hybrid_processor.py ../data/hybrid_approach/_revisions.json
import os
import json
import bz2
import mwxml
import logging
import argparse
from tqdm import tqdm
from typing import List, Set, Dict

from modules.reference_list_parser_processor import find_names_in_wikitext
from modules.page_extractor import get_wikipedia_plaintext_by_revision
from modules.reference_list_spacy_processor import SpacyReferenceListProcessor

TOKENS_TO_REMOVE: Set[str] = {
    "and", "the", "of", "for", "in", "not", "on", "an", "a", "at", "with",
    "And", "The", "Of", "For", "In", "Not", "On", "An", "At", "With", "Cas", "Some", "Insulin",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_reference_list_from_last_revision(last_revision_id: int) -> Set[str]:
    """Builds a reference list using only the unfiltered wikitext from the last revision."""
    reference_list: Set[str] = set()
    try:
        last_revision = get_wikipedia_plaintext_by_revision(last_revision_id)
        spacy_processor = SpacyReferenceListProcessor(use_gpu=False)
        names_set = spacy_processor.extract_names(last_revision)
        reference_list.update(names_set)
    except Exception as e:
        logger.error(f"Error extracting names from last revision {last_revision_id}: {e}")

    reference_list -= TOKENS_TO_REMOVE
    return reference_list


def _extract_names_with_reference_list(text: str, reference_list: Set[str]) -> List[str]:
    """Finds names in the given text using the provided reference list."""
    try:
        matches = find_names_in_wikitext(text, reference_list)
    except Exception as e:
        logger.error(f"Error finding names in wikitext: {e}")
        return []
    return [m.get("word", "") for m in matches if "word" in m]


def _process_wikipedia_pages_with_reference_list(input_path: str, revision_mapping: Dict[int, str]) -> None:
    """Processes a Wikipedia dump file using reference list extraction."""
    open_method = bz2.open if input_path.endswith(".bz2") else open
    try:
        with open_method(input_path, "rb") as dump_file:
            dump = mwxml.Dump.from_file(dump_file)
            for page in tqdm(dump, desc=f"Processing {input_path}"):
                page_list = list(page)
                if not page_list:
                    continue

                last_revision_id = page_list[-1].id
                reference_list = _build_reference_list_from_last_revision(last_revision_id)
                if not reference_list:
                    continue

                for revision in tqdm(page_list, desc="Processing Revisions", leave=False):
                    if not getattr(revision, "text", None):
                        continue
                    if revision.id in revision_mapping:
                        names = _extract_names_with_reference_list(revision.text, reference_list)
                        result = {"revision_id": str(revision.id), "names": names}
                        output_path = revision_mapping[revision.id]
                        try:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "w", encoding="utf-8") as out_f:
                                json.dump(result, out_f, indent=4, ensure_ascii=False)
                        except Exception as e:
                            logger.error(f"Error writing output for revision {revision.id}: {e}")
    except Exception as e:
        logger.error(f"Error processing dump file {input_path}: {e}")


def process_dumps_with_spacy_reference_list(json_path: str) -> None:
    """Reads JSON configuration and processes dumps."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON config from {json_path}: {e}")
        return

    for item in data:
        input_path = item.get("input_file_name")
        revision_mapping = {rev["id"]: rev["output_file_name"] for rev in item.get("revisions", [])}
        logger.info(f"Processing {input_path}...")
        _process_wikipedia_pages_with_reference_list(input_path, revision_mapping)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process Wikipedia dumps using a spaCy-derived reference list from the last revision."
    )
    parser.add_argument(
        "json_config",
        help="Path to the JSON configuration file."
    )
    args = parser.parse_args()

    process_dumps_with_spacy_reference_list(args.json_config)


if __name__ == "__main__":
    main()
