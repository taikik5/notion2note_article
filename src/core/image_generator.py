"""
Pillow-based image generator for note.com header images.
Generates header images with article title overlay.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import IMAGE_WIDTH, IMAGE_HEIGHT

# Assets directory
ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets"
)

# Background image path
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "header_background.png")

# Fallback gradient colors (purple to blue)
GRADIENT_START = (102, 126, 234)  # #667eea
GRADIENT_END = (118, 75, 162)     # #764ba2

# Text settings
TEXT_COLOR = (0, 0, 0)  # Black
TEXT_SHADOW_COLOR = (255, 255, 255)  # White shadow for readability


def create_header_image(title: str, output_path: str) -> str:
    """
    Create a header image with background and title text overlay.

    Uses a user-provided background image if available,
    otherwise falls back to a gradient background.

    Args:
        title: Article title to display on the image
        output_path: Path to save the generated image

    Returns:
        Path to the generated image
    """
    # Load background (user image or gradient fallback)
    image = _load_background_image()

    # Add title text
    _add_title_text(image, title)

    # Save image
    image.save(output_path, "PNG", quality=95)
    return output_path


def _load_background_image() -> Image.Image:
    """
    Load the user-provided background image.
    Falls back to gradient if no image is found.
    """
    # Try multiple extensions
    for ext in [".png", ".jpg", ".jpeg"]:
        path = BACKGROUND_IMAGE_PATH.replace(".png", ext)
        if os.path.exists(path):
            print(f"Loading background image: {path}")
            img = Image.open(path).convert("RGB")
            # Resize to fit note.com's recommended size
            return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)

    # Fallback to gradient
    print("No background image found, using gradient fallback")
    return _create_gradient_background()


def _create_gradient_background() -> Image.Image:
    """Create a gradient background image."""
    image = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT))
    draw = ImageDraw.Draw(image)

    for y in range(IMAGE_HEIGHT):
        # Calculate gradient ratio
        ratio = y / IMAGE_HEIGHT

        # Interpolate colors
        r = int(GRADIENT_START[0] + (GRADIENT_END[0] - GRADIENT_START[0]) * ratio)
        g = int(GRADIENT_START[1] + (GRADIENT_END[1] - GRADIENT_START[1]) * ratio)
        b = int(GRADIENT_START[2] + (GRADIENT_END[2] - GRADIENT_START[2]) * ratio)

        draw.line([(0, y), (IMAGE_WIDTH, y)], fill=(r, g, b))

    return image


def _add_title_text(image: Image.Image, title: str) -> None:
    """Add title text to the center of the image with word wrapping."""
    draw = ImageDraw.Draw(image)

    # Calculate appropriate font size based on title length
    font_size = _calculate_font_size(title)

    # Select font based on content language
    font = _get_font_for_title(title, size=font_size)

    # Maximum text width (80% of image width)
    max_width = int(IMAGE_WIDTH * 0.8)

    # Wrap text into multiple lines
    wrapped_lines = _wrap_text(title, font, max_width, draw)

    # Calculate total text block height
    line_heights = []
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])

    total_height = sum(line_heights) + (len(wrapped_lines) - 1) * 20  # 20px line spacing

    # Starting Y position (vertically centered)
    start_y = (IMAGE_HEIGHT - total_height) // 2

    # Draw each line centered
    current_y = start_y
    for i, line in enumerate(wrapped_lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (IMAGE_WIDTH - text_width) // 2

        # Draw shadow for better readability (optional)
        # draw.text((x + 2, current_y + 2), line, font=font, fill=TEXT_SHADOW_COLOR)

        # Draw main text
        draw.text((x, current_y), line, font=font, fill=TEXT_COLOR)

        current_y += line_heights[i] + 20


def _calculate_font_size(title: str) -> int:
    """Calculate appropriate font size based on title length."""
    length = len(title)
    if length <= 10:
        return 120
    elif length <= 15:
        return 100
    elif length <= 20:
        return 85
    elif length <= 25:
        return 70
    elif length <= 30:
        return 60
    else:
        return 50


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """
    Wrap text to fit within max_width with Japanese line-breaking rules (禁則処理).
    Returns list of lines.
    """
    lines = []
    current_line = ""
    i = 0

    while i < len(text):
        char = text[i]
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
            i += 1
        else:
            # Need to break - apply 禁則処理
            if current_line:
                # Find the best break point
                break_pos = _find_best_break_point(current_line, text, i)
                if break_pos > 0 and break_pos < len(current_line):
                    # Break at better position
                    lines.append(current_line[:break_pos])
                    # Remaining chars go to next line
                    current_line = current_line[break_pos:] + char
                    i += 1
                else:
                    lines.append(current_line)
                    current_line = char
                    i += 1
            else:
                current_line = char
                i += 1

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


# Characters that should not start a line (行頭禁則文字)
LINE_START_PROHIBITED = set(
    # Particles (助詞)
    "がをはにでともへやのかなよねわ"
    # Small hiragana
    "ぁぃぅぇぉっゃゅょゎ"
    # Small katakana
    "ァィゥェォッャュョヮヵヶ"
    # Punctuation and closing brackets
    "。、．，！？）」』】〉》）]｝・：；ー～"
)

# Characters that should not end a line (行末禁則文字)
LINE_END_PROHIBITED = set(
    # Opening brackets
    "（「『【〈《([｛"
)


def _is_kanji(char: str) -> bool:
    """Check if a character is kanji."""
    code = ord(char)
    # CJK Unified Ideographs: U+4E00-U+9FFF
    # CJK Unified Ideographs Extension A: U+3400-U+4DBF
    return (0x4E00 <= code <= 0x9FFF) or (0x3400 <= code <= 0x4DBF)


def _is_hiragana(char: str) -> bool:
    """Check if a character is hiragana."""
    code = ord(char)
    return 0x3040 <= code <= 0x309F


def _is_katakana(char: str) -> bool:
    """Check if a character is katakana."""
    code = ord(char)
    return 0x30A0 <= code <= 0x30FF


def _get_char_type(char: str) -> str:
    """Get the character type for break point detection."""
    if _is_kanji(char):
        return "kanji"
    elif _is_hiragana(char):
        return "hiragana"
    elif _is_katakana(char):
        return "katakana"
    elif char.isascii() and char.isalpha():
        return "alpha"
    elif char.isdigit():
        return "digit"
    else:
        return "other"


def _find_best_break_point(current_line: str, full_text: str, next_char_idx: int) -> int:
    """
    Find the best position to break the line according to Japanese typographic rules.
    Returns the position in current_line where we should break.

    Priority:
    1. Avoid breaking kanji compounds (熟語)
    2. Avoid prohibited characters at line start/end
    3. Prefer breaking at character type boundaries
    """
    if not current_line:
        return 0

    next_char = full_text[next_char_idx] if next_char_idx < len(full_text) else ""

    # Find all valid break points with scores
    break_candidates = []

    for pos in range(len(current_line), 0, -1):
        # Character that would start the new line
        if pos < len(current_line):
            new_line_start = current_line[pos]
        else:
            new_line_start = next_char

        # Character that would end the current line
        line_end = current_line[pos - 1] if pos > 0 else ""

        # Skip if prohibited at line start
        if new_line_start in LINE_START_PROHIBITED:
            continue

        # Skip if prohibited at line end
        if line_end in LINE_END_PROHIBITED:
            continue

        # Calculate score (higher is better)
        score = 0

        # Get character types
        end_type = _get_char_type(line_end) if line_end else "other"
        start_type = _get_char_type(new_line_start) if new_line_start else "other"

        # Penalize breaking in the middle of kanji sequence (熟語)
        if end_type == "kanji" and start_type == "kanji":
            score -= 100  # Strong penalty for breaking kanji compounds

        # Penalize breaking in the middle of katakana sequence
        if end_type == "katakana" and start_type == "katakana":
            score -= 50

        # Penalize breaking in the middle of alphabetic words
        if end_type == "alpha" and start_type == "alpha":
            score -= 50

        # Bonus for breaking after hiragana (often particles or word endings)
        if end_type == "hiragana" and start_type == "kanji":
            score += 30  # Good break point: hiragana → kanji

        # Bonus for breaking at character type transitions
        if end_type != start_type:
            score += 10

        # Prefer breaking closer to the end (less text to reflow)
        score += pos

        break_candidates.append((pos, score))

    # If no valid candidates, return end of line
    if not break_candidates:
        return len(current_line)

    # Return the position with highest score
    best_pos, _ = max(break_candidates, key=lambda x: x[1])
    return best_pos


def _has_japanese(text: str) -> bool:
    """Check if text contains Japanese characters (hiragana, katakana, kanji)."""
    for char in text:
        code = ord(char)
        # Hiragana: U+3040-U+309F
        # Katakana: U+30A0-U+30FF
        # Kanji (CJK Unified Ideographs): U+4E00-U+9FFF
        if (0x3040 <= code <= 0x309F or
            0x30A0 <= code <= 0x30FF or
            0x4E00 <= code <= 0x9FFF):
            return True
    return False


def _get_font_for_title(title: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get the best available font for the title."""
    return _get_font(size=size)


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get font with fallback chain. RocknRoll One is primary (supports Japanese)."""
    font_paths = [
        # Primary: RocknRoll One (supports Japanese and English)
        os.path.join(ASSETS_DIR, "RocknRollOne.ttf"),
        # Secondary: Other custom fonts
        os.path.join(ASSETS_DIR, "DelaGothicOne.ttf"),
        os.path.join(ASSETS_DIR, "Pacifico.ttf"),
        # Tertiary: macOS system fonts
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        # Tertiary: Other macOS fonts
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Linux (GitHub Actions) - CJK fonts
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        # Windows
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothB.ttc",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size)
                print(f"✓ Loaded font: {font_path}")
                return font
            except (OSError, IOError) as e:
                print(f"✗ Failed to load {font_path}: {e}")
                continue

    # Fall back to default font
    print("⚠ Using default font (Japanese font not found)")
    return ImageFont.load_default()


if __name__ == "__main__":
    # Test execution
    output_file = os.path.join(ASSETS_DIR, "test_header.png")

    # Test with different title lengths
    test_titles = [
        "短いタイトル",
        "朝5時起きの習慣が私を変えた話",  # Test for 禁則処理
        "プログラミング初心者が最短で成長する勉強法",  # Test for 熟語 (初心者, 最短, 成長, 勉強法)
    ]

    for i, title in enumerate(test_titles):
        output_file = os.path.join(ASSETS_DIR, f"test_header_{i + 1}.png")
        create_header_image(title, output_file)
        print(f"Generated: {output_file}")
