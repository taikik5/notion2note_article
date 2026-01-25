"""
Configuration and constants for notion2note_article.
"""

import os

# Notion API
NOTION_API_BASE = "https://api.notion.com/v1"
DEFAULT_MODE = "共感・エッセイ型"

# Image generation
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 670

# Mode definitions
MODES = {
    "共感・エッセイ型": "Empathy/Essay Mode",
    "ノウハウ・ビジネス型": "Knowhow/Business Mode",
    "推敲・リライト型": "Rewrite Mode",
}

# Environment variables (validation)
REQUIRED_ENV_VARS = [
    "NOTION_TOKEN",
    "NOTION_DATABASE_ID",
    "OPENAI_API_KEY",
]

# OpenAI
OPENAI_DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
