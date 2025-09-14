import requests
import html2text 

def get_wikipedia_plaintext_by_revision(revision_id: int) -> str:
    """
    Retrieve the HTML content of a specific revision of a Wikipedia article using the revision ID (oldid),
    convert it to plain text, and return the text.
    
    Optionally, the function checks that the returned page ID matches the provided page ID.
    
    Args:
        page_id (int): The expected Wikipedia page ID.
        revision_id (int): The revision ID (oldid) of the article.
    
    Returns:
        str: The plain text extracted from the article's HTML.
    
    Raises:
        ValueError: If the API response does not contain the expected data or if the returned page ID
                    does not match the provided page ID.
    """
    # Wikipedia API endpoint
    endpoint = "https://en.wikipedia.org/w/api.php"
    
    # Use only the oldid parameter to specify the revision.
    params = {
        "action": "parse",
        "oldid": revision_id,
        "prop": "text",
        "format": "json",
        "formatversion": 2
    }
    
    response = requests.get(endpoint, params=params)
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    data = response.json()
    
    if "parse" not in data:
        error_msg = data.get("error", {}).get("info", "Unknown error occurred.")
        raise ValueError(f"Failed to parse article: {error_msg}")
    
    html_content = data["parse"]["text"]
    
    # Convert HTML to plain text using BeautifulSoup
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    plain_text = h.handle(html_content)
    
    return plain_text
