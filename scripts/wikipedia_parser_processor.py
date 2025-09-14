#!/usr/bin/env python3
# python wikipedia_parser_processor.py ../data/custom_parser/_revisions.json
import os
import json
import bz2
import mwxml
import logging
import argparse
from tqdm import tqdm
from typing import List, Set, Dict, Any

from modules.reference_list_parser_processor import (
    extract_names_from_citations,
    find_names_in_wikitext
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKENS_TO_REMOVE: Set[str] = {
    "and", "the", "of", "for", "in", "not", "on", "an", "a", "at", "with", "by",
    "And", "The", "Of", "For", "In", "Not", "On", "An", "At", "With", "By",
    "Electronic", "Journal", "Research", "Center", "Information",
    "Lighting", "Inc", "United", "States", "Photo",
    "Insulin", "Medical", "Clinical", "American", "University", "Institute", "Association", "National", "Health", "Toronto", "Board",
    "Intelligence", "Study", "Computing", "Machine", "Learning", "Congress", "New", "Use", "AI", "Ai", "General", "Data", "Accountability", "Machinery", "Canada", "Global", "Council", "PhD",
    "Genetically", "Human", "Engineering", "Canadian", "Commission", "Sciences", "European", "Union", "Agriculture", "have", "Office", "Canadian", "Food", "Inspection", "Agency", "Committee", "Technology", "Science",
    "Psychological", "Schizophrenia",
    "Displays", "Display",
    "Drug",
    "Crispr",
    "Disease", "President", "Advisors", "Advisor",
    "Electric", "Aircraft", "Corporation", "Federal", "Aviation", "Administration", "Experimental", "Institut", "Flugzeugbau", "Polytechnic",
    "Diabetes", "System", "Organization", "Society", "Medicine",
    "Event", "Horizon", "Telescope", "EHT", "Collaboration",
    "Agricultural", "Mental", "health",
}


def _build_reference_list(page_list: List[Any]) -> Set[str]:
    """Builds a reference list from all revisions in the given page list."""
    reference_list: Set[str] = set()
    for revision in tqdm(page_list, desc="Building Reference List for Wikipedia Article"):
        if not getattr(revision, "text", None):
            continue
        try:
            names = extract_names_from_citations(revision.text)
            reference_list.update(names)
        except Exception as e:
            logger.error(f"Error extracting names from revision {revision.id}: {e}")

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

                reference_list = _build_reference_list(page_list)
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


def process_dumps_with_reference_list(json_path: str) -> None:
    """Processes Wikipedia dumps using reference list extraction based on a JSON configuration file."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON config from {json_path}: {e}")
        return

    for item in data:
        input_path = item.get("input_file_name")
        revision_mapping = {rev["id"]: rev["output_file_name"] for rev in item.get("revisions", [])}
        logger.info(f"Processing {input_path} with reference list extraction...")
        _process_wikipedia_pages_with_reference_list(input_path, revision_mapping)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process Wikipedia dumps using citation-based reference list extraction."
    )
    parser.add_argument(
        "json_config",
        help="Path to the JSON configuration file."
    )
    args = parser.parse_args()
    process_dumps_with_reference_list(args.json_config)


if __name__ == "__main__":
    main()
