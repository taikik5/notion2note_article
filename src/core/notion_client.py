"""
Notion API client for fetching and updating articles.
"""

import os
import sys
import httpx

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NOTION_API_BASE, DEFAULT_MODE


def get_notion_headers() -> dict:
    """Get headers for Notion API requests."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN environment variable is not set")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def fetch_ready_articles(database_id: str) -> list[dict]:
    """
    Fetch articles with Status = 'Ready' from the Notion database.

    Returns:
        List of article records with id, title, mode, and content.
    """
    articles = []
    has_more = True
    start_cursor = None
    headers = get_notion_headers()

    while has_more:
        payload = {
            "filter": {
                "property": "Status",
                "status": {
                    "equals": "Ready"
                }
            }
        }

        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = httpx.post(
            f"{NOTION_API_BASE}/databases/{database_id}/query",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        response.raise_for_status()
        data = response.json()

        for page in data.get("results", []):
            article = {
                "id": page["id"],
                "title": _extract_title(page),
                "mode": _extract_mode(page),
                "content": _extract_content(page),
            }
            articles.append(article)

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return articles


def _extract_title(page: dict) -> str:
    """Extract title (ID column) from page properties."""
    id_prop = page.get("properties", {}).get("ID", {})

    # Try unique_id type (Notion's auto-increment ID)
    unique_id = id_prop.get("unique_id")
    if unique_id:
        number = unique_id.get("number")
        if number is not None:
            return str(number)

    # Try number type
    id_number = id_prop.get("number")
    if id_number is not None:
        return str(id_number)

    # Fallback: Try other title properties
    for prop_name in ["タイトル", "Title", "name"]:
        title_prop = page.get("properties", {}).get(prop_name, {})
        title_list = title_prop.get("title", [])
        if title_list:
            return title_list[0].get("plain_text", "")

    return ""


def _extract_mode(page: dict) -> str:
    """
    Extract mode (モード) from page properties.

    Returns:
        One of: "共感・エッセイ型", "ノウハウ・ビジネス型", "推敲・リライト型"
        Defaults to "共感・エッセイ型" if not set.
    """
    mode_prop = page.get("properties", {}).get("モード", {})

    # Try select type
    select_obj = mode_prop.get("select")
    if select_obj:
        return select_obj.get("name", DEFAULT_MODE)

    # Try multi_select type (use first selection)
    multi_select = mode_prop.get("multi_select", [])
    if multi_select:
        return multi_select[0].get("name", DEFAULT_MODE)

    return DEFAULT_MODE


def _extract_content(page: dict) -> str:
    """
    Extract content from page properties.

    Returns:
        The plain text content from the text field.
    """
    # Try multiple possible property names
    for prop_name in ["文章のネタ", "テキスト", "Content", "content"]:
        content_prop = page.get("properties", {}).get(prop_name, {})

        # Try rich_text (if it's a Text or RichText property)
        rich_text_list = content_prop.get("rich_text", [])
        if rich_text_list:
            return "".join([rt.get("plain_text", "") for rt in rich_text_list])

    return ""


def mark_as_done(page_id: str) -> None:
    """Update the Status property to 'Done' for the specified page."""
    headers = get_notion_headers()
    payload = {
        "properties": {
            "Status": {
                "status": {
                    "name": "Done"
                }
            }
        }
    }
    response = httpx.patch(
        f"{NOTION_API_BASE}/pages/{page_id}",
        headers=headers,
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()


if __name__ == "__main__":
    # Test execution
    from dotenv import load_dotenv
    load_dotenv()

    database_id = os.environ.get("NOTION_DATABASE_ID", "")
    articles = fetch_ready_articles(database_id)
    print(f"Found {len(articles)} ready articles:")
    for article in articles:
        print(f"  - {article['title']}")
        print(f"    Mode: {article['mode']}")
        print(f"    Content: {article['content'][:100]}...")
