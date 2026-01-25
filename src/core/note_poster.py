"""
Playwright-based automation for note.com article posting.
"""

import os
import time
import json
import platform
from playwright.sync_api import sync_playwright, Page


NOTE_NEW_ARTICLE_URL = "https://note.com/notes/new"


def post_draft_to_note(
    title: str,
    body: str,
    state_file: str | None = None,
    header_image_path: str | None = None
) -> bool:
    """
    Post an article as a draft to note.com using saved session state.

    Args:
        title: Article title
        body: Article body (Markdown)
        state_file: Path to note-state.json file (defaults to ./note-state.json)
        header_image_path: Path to header image file (optional)

    Returns:
        True if successful, False otherwise
    """
    state_file = state_file or os.environ.get("NOTE_STATE_FILE", "./note-state.json")

    if not os.path.exists(state_file):
        raise FileNotFoundError(
            f"Session state file not found: {state_file}\n"
            f"Please run 'node login-note.js' first to generate the session state."
        )

    with sync_playwright() as p:
        # Use headed mode with xvfb for proper JavaScript execution
        # GitHub Actions uses xvfb-run to provide virtual display
        browser = p.chromium.launch(headless=False)

        # Create context with session state
        context_options = {
            "viewport": {"width": 1280, "height": 800},
            "locale": "ja-JP",
            "storage_state": state_file,
        }

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                cookies_count = len(state.get('cookies', []))
                print(f"✓ Loaded {cookies_count} cookies from session state")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load session state: {e}")

        context = browser.new_context(**context_options)
        page = context.new_page()

        try:
            # Navigate to new article page directly (session already authenticated)
            _navigate_to_new_article(page)

            # Upload header image if provided
            if header_image_path and os.path.exists(header_image_path):
                try:
                    _upload_header_image(page, header_image_path)
                except Exception as e:
                    print(f"Warning: Header image upload failed: {e}")
                    # Continue without header image

            # Input title and body
            _input_article_content(page, title, body)

            # Save as draft
            _save_draft(page)

            return True

        except Exception as e:
            print(f"Error during note automation: {e}")
            # Take screenshot for debugging
            page.screenshot(path="error_screenshot.png")
            raise

        finally:
            context.close()
            browser.close()


def _navigate_to_new_article(page: Page) -> None:
    """Navigate to new article creation page."""
    print("Navigating to new article page...")
    page.goto(NOTE_NEW_ARTICLE_URL)
    page.wait_for_load_state("networkidle")

    # Check if redirected to login page
    current_url = page.url
    print(f"Current URL: {current_url}")

    if "/login" in current_url:
        page.screenshot(path="error_screenshot.png")
        raise RuntimeError(
            "Session expired or invalid. Redirected to login page.\n"
            "Please run 'npm run login' to regenerate the session state."
        )

    # Wait for the editor to be fully loaded
    # Try multiple selectors and wait longer
    print("Waiting for editor to fully load (this may take a while)...")

    selectors_to_try = [
        '[contenteditable="true"]',
        'textarea',
        '[data-testid="article-body"]',
        '.ProseMirror',
        '[role="textbox"]'
    ]

    editor_found = False
    for selector in selectors_to_try:
        try:
            page.wait_for_selector(selector, timeout=60000)  # 60 second timeout
            print(f"✓ Editor element found: {selector}")
            editor_found = True
            break
        except Exception as e:
            print(f"  Selector '{selector}' not found: {str(e)[:50]}")

    if not editor_found:
        print("Warning: No editor elements found after 60 seconds")
        # Save debug page for inspection
        with open("page_content_debug.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("Debug HTML saved to page_content_debug.html")

    time.sleep(2)  # Additional wait

    print("✓ Successfully navigated to new article page")


def _upload_header_image(page: Page, image_path: str) -> None:
    """
    Upload a header image (見出し画像) to the article.

    note.com's flow:
    1. Click on the header image icon (circular gray button at top-left)
    2. Click "画像をアップロード" from the dropdown
    3. File chooser opens, select the file
    4. Image upload dialog appears, click OK/決定

    Args:
        page: Playwright Page object
        image_path: Absolute path to the image file to upload
    """
    print(f"Uploading header image: {image_path}")

    # Wait for the page to be fully loaded
    time.sleep(2)

    # Save page HTML for debugging
    with open("page_content.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("Page HTML saved for debugging")

    # Step 1: Click on the header image icon (circular button at top-left of editor)
    # This is the gray circular icon with an image/add icon
    header_icon_selectors = [
        # SVG icon or button for adding header image
        'button[aria-label*="画像"]',
        'button[aria-label*="見出し"]',
        '[class*="eyecatch"]',
        '[class*="Eyecatch"]',
        '[class*="header-image"]',
        '[class*="HeaderImage"]',
        # The circular button element
        'div[class*="AddImage"]',
        'div[class*="addImage"]',
        # Generic selectors for the icon area
        '.note-editor-header button',
        '[class*="Editor"] > div:first-child button',
        # Try to find by the icon shape (circular element near top)
        'div[style*="border-radius: 50%"]',
    ]

    header_clicked = False
    for selector in header_icon_selectors:
        try:
            element = page.locator(selector)
            if element.count() > 0:
                if element.first.is_visible():
                    element.first.click()
                    print(f"Clicked header icon: {selector}")
                    header_clicked = True
                    time.sleep(1)
                    break
        except Exception as e:
            print(f"  Selector '{selector}' failed: {str(e)[:30]}")
            continue

    # If not found by selector, try clicking the circular icon by position
    if not header_clicked:
        print("Header icon not found by selector, trying to find by visual position...")
        try:
            # Look for any clickable element near the top-left area
            # The header image button is usually at the top of the editor content area
            title_element = page.locator('[placeholder*="タイトル"]').or_(
                page.locator('textarea').first
            )
            if title_element.count() > 0:
                box = title_element.first.bounding_box()
                if box:
                    # The header image icon is above and to the left of the title
                    # Click at approximately (box['x'], box['y'] - 80)
                    click_x = box['x'] + 30  # A bit to the right of the left edge
                    click_y = box['y'] - 80  # Above the title
                    print(f"Clicking at position ({click_x}, {click_y})")
                    page.mouse.click(click_x, click_y)
                    time.sleep(1)
                    header_clicked = True
        except Exception as e:
            print(f"Position-based click failed: {e}")

    if not header_clicked:
        print("WARNING: Could not click header image area")
        page.screenshot(path="header_upload_error.png")
        raise RuntimeError("Could not find header image area to click")

    # Wait for dropdown/menu to appear
    time.sleep(1)

    # Take screenshot after clicking header area
    page.screenshot(path="after_header_click.png")
    print("Screenshot saved: after_header_click.png")

    # Step 2: Click "画像をアップロード" from dropdown menu
    upload_option_selectors = [
        'text=画像をアップロード',
        'text=アップロード',
        'button:has-text("画像をアップロード")',
        'button:has-text("アップロード")',
        '[role="menuitem"]:has-text("アップロード")',
        '[role="option"]:has-text("アップロード")',
        'li:has-text("アップロード")',
        'div[role="menu"] >> text=アップロード',
        # Try clicking any visible menu item
        '[role="menu"] button',
        '[role="listbox"] [role="option"]',
    ]

    # Use FileChooser - click the upload option and handle file selection
    try:
        with page.expect_file_chooser(timeout=15000) as fc_info:
            # Try to click the upload option
            upload_clicked = False
            for selector in upload_option_selectors:
                try:
                    element = page.locator(selector)
                    if element.count() > 0 and element.first.is_visible():
                        element.first.click()
                        print(f"Clicked upload option: {selector}")
                        upload_clicked = True
                        break
                except Exception:
                    continue

            if not upload_clicked:
                # If dropdown didn't appear, try clicking the header area again
                # Sometimes note.com requires a direct click to trigger file chooser
                print("Upload option not found, trying direct file input...")
                file_input = page.locator('input[type="file"]')
                if file_input.count() > 0:
                    file_input.first.set_input_files(image_path)
                    print("Used direct file input")
                    return
                raise RuntimeError("Could not find upload option in dropdown")

        # Handle file chooser
        file_chooser = fc_info.value
        file_chooser.set_files(image_path)
        print("Header image file selected")

        # Wait for upload processing
        time.sleep(3)

        # Step 3: Handle the image crop/position dialog
        # Look for 保存 button in the dialog (not the header's 下書き保存)
        # Wait for dialog to fully load
        time.sleep(2)

        # Take screenshot before clicking save
        page.screenshot(path="before_image_save.png")
        print("Screenshot saved: before_image_save.png")

        save_clicked = False

        # Method 1: Find button with exact text "保存" (not "下書き保存")
        try:
            # Get all buttons with text containing "保存"
            all_save_buttons = page.locator('button:has-text("保存")')
            button_count = all_save_buttons.count()
            print(f"Found {button_count} buttons with '保存' text")

            for i in range(button_count):
                button = all_save_buttons.nth(i)
                button_text = button.inner_text()
                print(f"  Button {i}: '{button_text}'")

                # Skip if it's "下書き保存" (header button)
                if "下書き" in button_text:
                    continue

                # This should be the dialog's "保存" button
                if button.is_visible():
                    button.click()
                    print(f"Clicked dialog save button: '{button_text}'")
                    save_clicked = True
                    time.sleep(2)
                    break
        except Exception as e:
            print(f"Method 1 failed: {e}")

        # Method 2: Click by position (dialog's bottom-right area)
        if not save_clicked:
            print("Trying position-based click for save button...")
            try:
                # The dialog appears to be centered, with save button at bottom-right
                # Get viewport size and estimate dialog position
                viewport = page.viewport_size
                if viewport:
                    # Dialog save button is typically at the right side of the dialog footer
                    # Based on screenshot: dialog is centered, button is at bottom-right
                    click_x = viewport['width'] * 0.75  # Right side of center
                    click_y = viewport['height'] * 0.85  # Near bottom
                    print(f"Clicking at estimated position ({click_x}, {click_y})")
                    page.mouse.click(click_x, click_y)
                    save_clicked = True
                    time.sleep(2)
            except Exception as e:
                print(f"Method 2 failed: {e}")

        # Method 3: Try keyboard Enter
        if not save_clicked:
            print("WARNING: Could not find save button, trying keyboard Enter...")
            page.keyboard.press("Enter")
            time.sleep(2)

        print("✓ Header image upload completed")

    except Exception as e:
        print(f"Upload failed: {e}")
        # Take screenshot for debugging
        page.screenshot(path="header_upload_error.png")
        raise RuntimeError(f"Header image upload failed: {e}")


def _input_article_content(page: Page, title: str, body: str) -> None:
    """Input article title and body."""
    print("Inputting article content...")

    # Wait a bit more for elements to be interactive
    time.sleep(2)

    # Input title
    title_input = page.locator('[placeholder*="タイトル"]').or_(
        page.locator('.o-noteEditorTextarea__title')
    ).or_(
        page.locator('[data-testid="article-title"]')
    ).or_(
        page.locator('textarea').first
    )

    if title_input.count() > 0:
        print("Found title input, filling...")
        title_input.first.click()
        time.sleep(0.3)
        title_input.first.fill(title)
        time.sleep(0.5)
        print(f"Title filled: {title}")
        # Debug: Check if title was actually filled
        title_value = page.locator('input, textarea').first.input_value() if page.locator('input, textarea').count() > 0 else "N/A"
        print(f"Debug - Title input value after fill: {title_value[:50]}")
    else:
        print("Warning: Title input not found")
        print(f"Debug - Available textareas: {page.locator('textarea').count()}")
        print(f"Debug - Available inputs: {page.locator('input').count()}")

    # Input body using clipboard paste (required for markdown conversion)
    body_editor = page.locator('[data-testid="article-body"]').or_(
        page.locator('.o-noteEditorTextarea__body')
    ).or_(
        page.locator('[contenteditable="true"]')
    ).or_(
        page.locator('.ProseMirror')
    )

    if body_editor.count() > 0:
        print("Found body editor, pasting content via clipboard...")
        editor_element = body_editor.first
        editor_element.click()
        time.sleep(0.5)

        # Use clipboard paste - this is required for note.com to recognize markdown
        # note.com converts markdown to proper formatting only when pasting from clipboard
        try:
            # Set clipboard content using JavaScript
            page.evaluate(
                """async (text) => {
                    await navigator.clipboard.writeText(text);
                }""",
                body
            )
            time.sleep(0.3)

            # Paste using keyboard shortcut (Ctrl+V or Cmd+V)
            # Use Meta for Mac, Control for Linux (GitHub Actions runs on Linux)
            if platform.system() == "Darwin":
                page.keyboard.press("Meta+v")
            else:
                page.keyboard.press("Control+v")

            print("Body pasted using clipboard")
            time.sleep(1)
        except Exception as e:
            print(f"Clipboard paste failed: {e}, trying alternative method...")
            # Fallback: Use Playwright's built-in clipboard
            try:
                # Focus and select all first
                editor_element.click()
                time.sleep(0.3)

                # Type the content line by line with Enter key
                # This helps note.com recognize markdown better
                lines = body.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        page.keyboard.type(line, delay=5)
                    if i < len(lines) - 1:
                        page.keyboard.press("Enter")

                print("Body typed line by line")
            except Exception as e2:
                print(f"Line-by-line typing also failed: {e2}")
                # Last resort: direct fill
                try:
                    editor_element.fill(body)
                    print("Body filled using fill() as last resort")
                except Exception as e3:
                    print(f"All methods failed: {e3}")
    else:
        print("Warning: Body editor not found")
        print(f"Debug - contenteditable elements: {page.locator('[contenteditable=true]').count()}")
        print(f"Debug - ProseMirror elements: {page.locator('.ProseMirror').count()}")

    time.sleep(1)
    print("Article content input complete")


def _save_draft(page: Page) -> None:
    """Save the article as a draft."""
    print("Saving as draft...")

    # Take screenshot before saving
    page.screenshot(path="before_save_screenshot.png")
    print("Screenshot saved: before_save_screenshot.png")

    try:
        # Debug: List all buttons on the page
        all_buttons = page.locator('button').count()
        print(f"Debug - Total buttons on page: {all_buttons}")

        # Look for the draft save button
        draft_button = page.locator('text=下書き保存').or_(
            page.locator('button:has-text("下書き")').first
        ).or_(
            page.locator('[data-testid="save-draft"]')
        )

        print(f"Debug - Draft button count: {draft_button.count()}")

        if draft_button.count() > 0:
            print(f"Found draft button, clicking...")
            draft_button.first.click()
            time.sleep(5)  # Wait for save to complete
            print("Draft saved successfully")
        else:
            print("Draft button not found, trying keyboard shortcut...")
            # Try Cmd+S on Mac
            page.keyboard.press("Meta+s")
            time.sleep(3)
            print("Attempted keyboard shortcut save (Cmd+S)")

    except Exception as e:
        print(f"Error during save: {e}")
        page.keyboard.press("Meta+s")
        time.sleep(2)

    # Take screenshot after saving
    page.screenshot(path="after_save_screenshot.png")
    print("Screenshot saved: after_save_screenshot.png")


if __name__ == "__main__":
    # Test execution (requires note-state.json from login-note.js)
    from dotenv import load_dotenv
    load_dotenv()

    test_title = "テスト記事タイトル"
    test_body = """## はじめに
テスト投稿です。

## 本文
Playwrightの自動化テスト

---
### あとがき
テスト完了！
"""

    post_draft_to_note(test_title, test_body)
    print("Test completed successfully!")
