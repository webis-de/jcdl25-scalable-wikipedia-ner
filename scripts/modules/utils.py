import re

COMBINED_PATTERN = re.compile(
    r"(?:"
        r"\{\{cite[^}]*?\}\}|"                    # Matches {{cite ...}}
        r"\{\{citation[^}]*?\}\}|"                # Matches {{citation ...}}
        r"\{\{harvard citation[^}]*?\}\}|"        # Matches {{citation ...}}
        r"\{\{rvnb[^}]*?\}\}|"                    # Matches {{rvnb ...}}
        r"\{\{harv[^}]*?\}\}|"                    # Matches {{harv ...}}
        r"\{\{harvtxt[^}]*?\}\}|"                 # Matches {{harvtxt ...}}
        r"\{\{harvcoltxt[^}]*?\}\}|"              # Matches {{harvcoltxt ...}}
        r"\{\{harvcol[^}]*?\}\}|"                 # Matches {{harvcol ...}}
        r"\{\{harvcolnb[^}]*?\}\}|"               # Matches {{harvcolnb ...}}
        r"\{\{harvs[^}]*?\}\}|"                   # Matches {{harvs ...}}
        r"\{\{harvp[^}]*?\}\}|"                   # Matches {{harvp ...}}
        r"\{\{harvc[^}]*?\}\}|"                   # Matches {{harvc ...}}
        r"\{\{citec[^}]*?\}\}|"                   # Matches {{citec ...}}
        r"\{\{sfn[^}]*?\}\}|"                     # Matches {{sfn ...}}
        r"\{\{sfnp[^}]*?\}\}|"                    # Matches {{sfnp ...}}
        r"\{\{sfnm[^}]*?\}\}|"                    # Matches {{sfnm ...}}
        r"\{\{sfnmp[^}]*?\}\}|"                   # Matches {{sfnmp ...}}
        r"\{\{efn[^}]*?\}\}|"                     # Matches {{efn ...}}
        r"<ref[^>]*?\/>|"                         # Matches self-closing <ref .../>
        r"<ref[^>]*?>.*?<\/ref>|"                 # Matches <ref ...>...</ref>
        r"<!--.*?-->|"                            # Matches HTML comments
        r"==\s*(?:External links|See also|Further reading)\s*==[\s\S]*"  # Matches headings and everything after
    r")",
    re.DOTALL | re.IGNORECASE
)

PIPE_PATTERN = re.compile(r"\[\[[^|\]]+\|([^|\]]+)\]\]")  # Matches [[...|...]] pattern

LETTER_FILTER_PATTERN = re.compile(r"[^\w\s.,!?;:'-]", re.UNICODE)

def filter_wikitext(wikitext):
    """
    Cleans and filters wikitext by removing or replacing certain patterns while preserving
    the original length of the text for specific matches.

    This function performs the following steps:
    1. Replaces all matches of a precompiled combined pattern (e.g., citations, references, 
       comments, and headings) with spaces of the same length as the match.
    2. Replaces matches of the pipe pattern `[[...|...]]` with spaces in the segment before 
       the pipe, preserving the structure of the text.
    3. Removes all non-alphanumeric characters except for punctuation marks by replacing 
       them with spaces.
    """
    if wikitext is None:
        return ""
    
    processed_text = re.sub(
        COMBINED_PATTERN, 
        lambda m: ' ' * (m.end() - m.start()), 
        wikitext
    )

    processed_text = re.sub(
        PIPE_PATTERN,
        lambda m: m.group(0)[:2] + ' ' * (m.start(1) - m.start(0) - 2) + m.group(0)[m.start(1) - m.start(0):],
        processed_text
    )

    processed_text = re.sub(LETTER_FILTER_PATTERN, " ", processed_text)
    
    return processed_text

def merge_adjacent_tokens_in_result_list(results):
    """
    Processes a list of tokenized results to merge adjacent or closely positioned tokens 
    based on specific rules.

    Rules:
    1. Merge two tokens if the gap between the end position of the current token 
       and the start position of the next token is exactly 2.
    2. Merge two tokens if the gap is exactly 3 and the last word in the current token 
       is a single uppercase character.
    """
    i = 0
    while i < len(results) - 1:
        current = results[i]
        next_token = results[i + 1]

        if current["positionEnd"] + 2 == next_token["positionStart"]:
            current["word"] += " " + next_token["word"]
            current["positionEnd"] = next_token["positionEnd"]
            results.pop(i + 1)
            continue

        current_words = current["word"].split()
        if (
            len(current_words[-1]) == 1 and
            current_words[-1].isupper() and
            current["positionEnd"] + 3 == next_token["positionStart"]
        ):
            current["word"] += " " + next_token["word"]
            current["positionEnd"] = next_token["positionEnd"]
            results.pop(i + 1)
            continue
        i += 1

    return results

def exclude_uniform_case_tokens(results):
    """
    Filters a list of results to exclude items where all tokens in the "word" field 
    are either entirely lowercase or entirely uppercase.
    """
    filtered_results = []
    for item in results:
        tokens = item["word"].split()
        if not (all(token.islower() for token in tokens) or all(token.isupper() for token in tokens)):
            filtered_results.append(item)
    return filtered_results

def create_reference_set_from_file(file_path='dumps/person_name_list.txt'):
    """
    Reads a file line by line, splits each line by whitespace, 
    and creates a set containing all parts from the file.
    Defaults to 'dumps/person_name_list.txt'.

    Args:
        file_path (str): The path to the file. Defaults to 'dumps/person_name_list.txt'.

    Returns:
        set: A set containing each part from the file split by whitespace.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            entries_set = {part for line in file for part in line.strip().split() if part}
        return entries_set
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return set()
    except Exception as e:
        print(f"An error occurred: {e}")
        return set()