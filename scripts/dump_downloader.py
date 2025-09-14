#!/usr/bin/env python3
"""
Wikipedia page dump downloader & merger.

Example:
    python dump_downloader.py "Python (programming language)" output.xml --limit 500
"""

import argparse
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


class DumpDownloader:
    def __init__(self):
        self._namespace = {"mw": "http://www.mediawiki.org/xml/export-0.11/"}
        # Register namespace for writing XML
        ET.register_namespace("", self._namespace["mw"])

    def _fetch_wiki_dump(self, page: str, limit: int):
        offset = "1"
        base_url = "https://en.wikipedia.org/w/index.php?title=Special:Export"
        files_downloaded = []
        filename = f"{page}_offset_{offset}.xml"

        while True:
            curl_command = [
                "curl",
                "-sS",               # silent but show errors
                "-f",                # fail on HTTP errors
                "-d", "",            # POST request with empty body (Special:Export expects POST)
                f"{base_url}&pages={page}&limit={limit}&offset={offset}",
                "-o", filename,
            ]

            try:
                subprocess.run(curl_command, check=True)
            except FileNotFoundError:
                raise RuntimeError(
                    "The 'curl' command was not found. Please install curl or modify the script to use 'requests'."
                )
            except subprocess.CalledProcessError as e:
                print(f"curl failed: {e}.", file=sys.stderr)
                if os.path.exists(filename):
                    os.remove(filename)
                break

            # Check if the file has content
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                print(f"No data fetched. Deleting {filename}.")
                if os.path.exists(filename):
                    os.remove(filename)
                break

            # Parse the XML to get the last <timestamp>
            try:
                tree = ET.parse(filename)
                root = tree.getroot()

                # Check if the file contains a <page> element
                page_element = root.find("mw:page", namespaces=self._namespace)
                if page_element is None:
                    print(f"File {filename} does not contain a <page> element. Deleting it.")
                    os.remove(filename)
                    break

                # Add the file to the list of downloaded files
                files_downloaded.append(filename)

                # Find all <timestamp> elements
                timestamps = root.findall(".//mw:timestamp", namespaces=self._namespace)
                if timestamps:
                    last_timestamp = timestamps[-1].text
                    print(f"Last timestamp: {last_timestamp}")
                    offset = last_timestamp
                    safe_offset = offset.replace(":", "_").replace("-", "_")
                    filename = f"{page}_offset_{safe_offset}.xml"
                else:
                    print("No <timestamp> found in the file. Stopping.")
                    break
            except ET.ParseError as e:
                print(f"Error parsing XML: {e}. Deleting {filename}.")
                os.remove(filename)
                break

        return files_downloaded

    def _merge_multiple_wiki_dumps(self, xml_files, output_file):
        if not xml_files:
            raise ValueError("No XML files provided to merge.")

        # Parse the first XML file (base file)
        base_tree = ET.parse(xml_files[0])
        base_root = base_tree.getroot()

        # Find the <page> element in the base file
        base_page = base_root.find("mw:page", self._namespace)
        if base_page is None:
            raise ValueError("The first XML file must contain a <page> element.")

        # Iterate through the rest of the files and merge their <revision> elements
        for xml_file in xml_files[1:]:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            page = root.find("mw:page", self._namespace)
            if page is None:
                raise ValueError(f"File {xml_file} does not contain a <page> element.")

            revisions = page.findall("mw:revision", self._namespace)
            for revision in revisions:
                base_page.append(revision)

        # Write the merged XML to the output file
        base_tree.write(output_file, encoding="utf-8", xml_declaration=True)
        print(f"Merged XML written to {output_file}")

    def automate_wiki_dump_process(self, page: str, output_file: str, limit: int = 1000, keep_parts: bool = False):
        print(f"Fetching Wiki dumps for page: {page} (limit={limit})...")
        downloaded_files = self._fetch_wiki_dump(page, limit)

        if downloaded_files:
            print(f"Downloaded {len(downloaded_files)} files. Merging...")
            self._merge_multiple_wiki_dumps(downloaded_files, output_file)

            if not keep_parts:
                for file in downloaded_files:
                    try:
                        os.remove(file)
                    except OSError:
                        pass
                print("All temporary files have been removed.")
            else:
                print("Keeping part files as requested.")
        else:
            print("No files downloaded. Nothing to merge.")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Download and merge Wikipedia page dumps via Special:Export."
    )
    parser.add_argument(
        "page",
        help='Wiki page title exactly as on Wikipedia (e.g., "Python (programming language)")',
    )
    parser.add_argument(
        "output",
        help="Path to the merged output XML file (e.g., output.xml)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max number of revisions per request (default: 1000). Wikipedia may cap effective limits.",
    )
    parser.add_argument(
        "--keep-parts",
        action="store_true",
        help="Keep the individual downloaded XML parts instead of deleting them after merge.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Quick sanity checks
    out_dir = os.path.dirname(os.path.abspath(args.output)) or "."
    if not os.path.isdir(out_dir):
        print(f"Output directory does not exist: {out_dir}", file=sys.stderr)
        sys.exit(2)

    # Warn if curl is missing
    if shutil.which("curl") is None:
        print(
            "Warning: 'curl' not found in PATH. This script requires curl.\n"
            "Install curl or adapt the script to use the 'requests' library.",
            file=sys.stderr,
        )
        sys.exit(2)

    downloader = DumpDownloader()
    try:
        downloader.automate_wiki_dump_process(
            page=args.page,
            output_file=args.output,
            limit=args.limit,
            keep_parts=args.keep_parts,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()