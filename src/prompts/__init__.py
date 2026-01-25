"""
Prompt definitions for different article modes.
"""

from .base import NOTE_MARKDOWN_RULES
from .empathy_essay import EMPATHY_ESSAY_PROMPT
from .knowhow_business import KNOWHOW_BUSINESS_PROMPT
from .rewrite import REWRITE_PROMPT

# Mode name to prompt mapping
MODE_PROMPTS = {
    "共感・エッセイ型": EMPATHY_ESSAY_PROMPT,
    "ノウハウ・ビジネス型": KNOWHOW_BUSINESS_PROMPT,
    "推敲・リライト型": REWRITE_PROMPT,
}

__all__ = [
    "NOTE_MARKDOWN_RULES",
    "EMPATHY_ESSAY_PROMPT",
    "KNOWHOW_BUSINESS_PROMPT",
    "REWRITE_PROMPT",
    "MODE_PROMPTS",
]
