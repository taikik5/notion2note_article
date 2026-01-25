"""
OpenAI API module for formatting articles with mode-specific prompts.
"""

import os
from openai import OpenAI

from prompts import NOTE_MARKDOWN_RULES, MODE_PROMPTS, EMPATHY_ESSAY_PROMPT


def format_article(content: str, mode: str) -> tuple[str, str]:
    """
    Format content into a structured article using OpenAI API.

    Args:
        content: Raw content (文章のネタ) from Notion
        mode: Article mode (共感・エッセイ型, ノウハウ・ビジネス型, 推敲・リライト型)

    Returns:
        Tuple of (title, formatted_body)
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Get model from environment variable, default to gpt-4o-mini
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # Get mode-specific prompt, fallback to empathy/essay if mode not found
    mode_prompt = MODE_PROMPTS.get(mode, EMPATHY_ESSAY_PROMPT)

    # Combine base markdown rules with mode-specific prompt
    system_prompt = NOTE_MARKDOWN_RULES + "\n\n" + mode_prompt

    client = OpenAI(api_key=api_key)

    user_message = f"""以下の素材をもとに記事を作成してください。

---
素材:
{content}
---

上記の素材を、指定されたフォーマットに従って記事化してください。
タイトルは1行目に見出し記号なしで出力してください。
マークダウン形式で出力してください（```markdown などのコードブロックで囲まないでください）。
"""

    print(f"Using mode: {mode}")
    print(f"Using model: {model}")

    message = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    formatted_content = message.choices[0].message.content

    # Extract title and body
    lines = formatted_content.strip().split("\n")

    # First non-empty line is the title
    title = ""
    body_start_index = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            # Remove any markdown heading prefix if present
            title = stripped.lstrip("#").strip()
            body_start_index = i + 1
            break

    body = "\n".join(lines[body_start_index:]).strip()

    # If title extraction failed, use first line as title
    if not title:
        title = "新しい記事"
        body = formatted_content

    return title, body


if __name__ == "__main__":
    # Test execution
    from dotenv import load_dotenv
    load_dotenv()

    test_content = """
    最近、朝活を始めてみた。
    最初は辛かったけど、1週間続けたら意外と慣れてきた。
    朝の時間を使って読書をしている。
    夜よりも集中できる気がする。
    """

    # Test each mode
    modes = ["共感・エッセイ型", "ノウハウ・ビジネス型", "推敲・リライト型"]

    for mode in modes:
        print(f"\n{'=' * 50}")
        print(f"Testing mode: {mode}")
        print("=" * 50)

        title, body = format_article(test_content, mode)
        print(f"Title: {title}")
        print(f"\nBody:\n{body[:500]}...")
