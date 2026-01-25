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
    font = _get_japanese_font(size=font_size)

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
    Wrap text to fit within max_width.
    Returns list of lines.
    """
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


def _get_japanese_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a Japanese-compatible font, with fallbacks for different environments."""
    font_paths = [
        # Primary: Pacifico (playful cursive for note.com aesthetic)
        os.path.join(ASSETS_DIR, "Pacifico.ttf"),
        # User-provided Japanese fonts (in assets folder)
        os.path.join(ASSETS_DIR, "NotoSansJP-Bold.ttf"),
        os.path.join(ASSETS_DIR, "NotoSansJP-Regular.ttf"),
        os.path.join(ASSETS_DIR, "NotoSansCJKjp-Bold.otf"),
        # macOS Japanese fonts
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
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
        "これは少し長めのタイトルです",
        "これはとても長いタイトルで、複数行に分割されることを確認するためのテストです",
    ]

    for i, title in enumerate(test_titles):
        output_file = os.path.join(ASSETS_DIR, f"test_header_{i + 1}.png")
        create_header_image(title, output_file)
        print(f"Generated: {output_file}")
