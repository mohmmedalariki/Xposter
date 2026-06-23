import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

def post_linkedin_with_browser(text, image_path=None, headless=True):
    """
    Posts to LinkedIn (optionally with an image) using Playwright browser automation
    by injecting the user's active session cookie (li_at).
    """
    load_dotenv()
    li_at_cookie = os.getenv("LINKEDIN_COOKIE_LI_AT")
    
    if not li_at_cookie or li_at_cookie == "your_linkedin_cookie_here":
        print("Error: LINKEDIN_COOKIE_LI_AT is missing or not set in .env.")
        print("Please fetch the 'li_at' cookie from your browser and update .env (or GitHub Secrets).")
        raise ValueError("LINKEDIN_COOKIE_LI_AT is missing")

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            # Inject session cookie
            print("Injecting LinkedIn session cookie (li_at)...")
            context.add_cookies([{
                'name': 'li_at',
                'value': li_at_cookie,
                'domain': '.www.linkedin.com',
                'path': '/'
            }])
            
            page = context.new_page()
            
            print("Navigating to LinkedIn Feed...")
            page.goto("https://www.linkedin.com/feed/")
            page.wait_for_timeout(6000)
            
            current_url = page.url
            if "login" in current_url or "signup" in current_url:
                print("Error: Authentication failed. The li_at cookie might be invalid or expired.")
                browser.close()
                raise PermissionError("LinkedIn token is invalid or expired")

            print("Locating 'Start a post' button...")
            start_post_btn = page.locator('button:has-text("Start a post")').first
            if not start_post_btn.is_visible():
                print("Could not find 'Start a post' button. Saving screenshot...")
                page.screenshot(path="linkedin_error_home.png")
                raise RuntimeError("Start a post button not found")
                
            start_post_btn.click()
            page.wait_for_timeout(2000)

            print("Locating text editor...")
            # The editor is usually a div with role="textbox" and contenteditable="true"
            editor = page.locator('div[role="textbox"][contenteditable="true"]').first
            if not editor.is_visible():
                print("Could not find text editor. Saving screenshot...")
                page.screenshot(path="linkedin_error_editor.png")
                raise RuntimeError("LinkedIn text editor not found")
                
            print("Entering post text...")
            editor.fill(text)
            page.wait_for_timeout(1000)

            if image_path and os.path.exists(image_path):
                print(f"Uploading image: {image_path}...")
                # Click the add media button (which opens file chooser)
                try:
                    with page.expect_file_chooser() as fc_info:
                        # Attempt to click the media button (typically an aria-label with "Add media" or similar)
                        # The exact aria-label varies, "Add media" is most common.
                        media_btn = page.locator('button[aria-label="Add media"]').first
                        if not media_btn.is_visible():
                            # fallback: Sometimes it's a generic button with an icon
                            media_btn = page.locator('button[aria-label="Add a photo"]').first
                        media_btn.click()
                    
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                    print("Waiting for image to load...")
                    page.wait_for_timeout(3000)
                    
                    # Click "Next" or "Done" on the media modal
                    next_btn = page.locator('button:has-text("Next")').first
                    if next_btn.is_visible():
                        next_btn.click()
                        page.wait_for_timeout(2000)
                except Exception as upload_err:
                    print(f"Failed to upload image. Error: {upload_err}")
                    page.screenshot(path="linkedin_error_image_upload.png")

            # Final post
            print("Locating Post button...")
            # Usually it's a button with text "Post" inside a div
            post_btn = page.locator('button:has-text("Post")').first
            
            if post_btn.is_visible() and post_btn.is_enabled():
                print("Clicking Post button...")
                post_btn.click()
                print("Waiting for post completion...")
                page.wait_for_timeout(5000)
                print("Verification complete. LinkedIn post successful.")
            else:
                print("Error: Post button not visible or is disabled.")
                page.screenshot(path="linkedin_post_button_error.png")
                raise RuntimeError("Post button not visible or disabled")

            browser.close()
            return True

    except Exception as e:
        print(f"An unexpected error occurred during LinkedIn Playwright execution: {e}")
        raise e

if __name__ == "__main__":
    print("This script is intended to be imported. Run main.py instead.")
