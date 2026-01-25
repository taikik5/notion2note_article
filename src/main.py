"""
Main orchestrator for Notion-to-Note Article AutoDrafter.

This script:
1. Fetches articles with Status='Ready' from Notion
2. Formats each article using OpenAI API (with mode-specific prompts)
3. Generates header image with article title
4. Posts articles as drafts to note.com
5. Updates Notion status to 'Done'
"""

import os
import sys
import tempfile
import shutil

# Add the src directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from notion_client_module import (
    fetch_ready_articles,
    mark_as_done,
)
from openai_formatter import format_article
from note_automation import post_draft_to_note
from image_generator import create_header_image

# Load environment variables from .env file
load_dotenv()


def main() -> int:
    """Main entry point."""
    print("=" * 50)
    print("Notion-to-Note Article AutoDrafter")
    print("=" * 50)

    # Validate environment variables
    required_vars = [
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID",
        "OPENAI_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {missing_vars}")
        return 1

    database_id = os.environ["NOTION_DATABASE_ID"]

    # Step 1: Fetch ready articles from Notion
    print("\n[Step 1] Fetching ready articles from Notion...")
    articles = fetch_ready_articles(database_id)

    if not articles:
        print("No articles with Status='Ready' found. Exiting.")
        return 0

    print(f"Found {len(articles)} article(s) to process.")

    # Process each article
    success_count = 0
    error_count = 0

    for i, article in enumerate(articles, 1):
        print(f"\n{'=' * 50}")
        print(f"Processing article {i}/{len(articles)}")
        print(f"ID: {article['title']}")
        print(f"Mode: {article['mode']}")
        print("=" * 50)

        # Create temp directory for header image
        temp_dir = tempfile.mkdtemp(prefix="note_header_")

        try:
            # Step 2: Format article with OpenAI (mode-specific)
            print("\n[Step 2] Formatting article with OpenAI...")
            content = article["content"]

            if not content.strip():
                print("Warning: Empty content (文章のネタ), skipping.")
                error_count += 1
                continue

            print(f"Content preview: {content[:100]}...")

            title, body = format_article(content, article["mode"])
            print(f"Generated title: {title}")
            print(f"Body length: {len(body)} characters")

            # Step 3: Generate header image with title
            print("\n[Step 3] Generating header image...")
            image_path = os.path.join(temp_dir, f"header_{article['id'][:8]}.png")
            create_header_image(title, image_path)
            print(f"Header image generated: {image_path}")

            # Step 4: Post to note.com as draft (with header image)
            print("\n[Step 4] Posting to note.com as draft...")
            post_draft_to_note(title, body, header_image_path=image_path)
            print("Successfully posted draft to note.com!")

            # Step 5: Mark as Done in Notion
            print("\n[Step 5] Updating Notion status to 'Done'...")
            mark_as_done(article["id"])
            print("Notion status updated.")

            success_count += 1

        except Exception as e:
            print(f"\nError processing article: {e}")
            error_count += 1
            # Continue with next article instead of failing completely
            continue

        finally:
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                print("Temp files cleaned up")

    # Summary
    print("\n" + "=" * 50)
    print("Processing complete!")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print("=" * 50)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
