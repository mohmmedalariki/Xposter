import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

def post_tweet_with_browser(text, image_path=None, headless=True):
    """
    Posts a tweet (optionally with an image) using Playwright browser automation
    by injecting the user's active session cookie (auth_token).
    """
    load_dotenv()
    auth_token = os.getenv("X_COOKIE_AUTH_TOKEN")
    
    if not auth_token or auth_token == "your_auth_token_here":
        print("Error: X_COOKIE_AUTH_TOKEN is missing or not set in .env.")
        print("Please fetch the auth_token cookie from your browser and update .env (or GitHub Secrets).")
        raise ValueError("X_COOKIE_AUTH_TOKEN is missing")

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            # We use a real user-agent to bypass basic bot-detection mechanisms
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            # Inject session cookie
            print("Injecting X session cookie...")
            context.add_cookies([{
                'name': 'auth_token',
                'value': auth_token,
                'domain': '.x.com',
                'path': '/'
            }])
            
            page = context.new_page()
            
            print("Navigating to X Home...")
            page.goto("https://x.com/home")
            
            # Wait for either the feed/composer to load or a login wall
            print("Waiting for page load...")
            page.wait_for_timeout(6000)
            page.screenshot(path="1_home.png")
            print("Saved screenshot: 1_home.png")
            
            current_url = page.url
            print(f"Current page URL: {current_url}")
            if "login" in current_url or "i/flow/login" in current_url:
                print("Error: Authentication failed. The auth_token cookie might be invalid or expired.")
                browser.close()
                raise PermissionError("X Auth token is invalid or expired")
                
            print("Locating tweet composer...")
            # First, check if the inline composer on home page is visible
            composer = page.locator('div[data-testid="tweetTextarea_0"]').first
            
            if not composer.is_visible():
                print("Inline composer not visible. Trying to click sidebar 'Post' button...")
                post_btn = page.locator('[data-testid="SideNav_NewTweet_Button"]').first
                if post_btn.is_visible():
                    post_btn.click()
                    page.wait_for_timeout(1500)
                    composer = page.locator('div[data-testid="tweetTextarea_0"]').first
            
            if not composer.is_visible():
                print("Error: Could not find or open the tweet composer.")
                page.screenshot(path="composer_error.png")
                print("Saved debug screenshot to composer_error.png")
                browser.close()
                raise RuntimeError("Could not open tweet composer")
                
            print("Entering tweet text...")
            composer.click()
            composer.fill(text)
            page.wait_for_timeout(1000)
            
            if image_path:
                if os.path.exists(image_path):
                    print(f"Uploading image: {image_path}...")
                    file_input = page.locator('input[data-testid="fileInput"]').first
                    file_input.set_input_files(image_path)
                    print("Waiting for upload to process...")
                    page.wait_for_timeout(5000) # Wait for processing
                else:
                    print(f"Warning: Image path not found: {image_path}")
            
            page.screenshot(path="2_composer_ready.png")
            print("Saved screenshot: 2_composer_ready.png")
            
            # Locate active tweet button
            print("Locating Post button...")
            tweet_btn = page.locator('[data-testid="tweetButtonInline"], [data-testid="tweetButton"]').first
            
            print("Focusing composer and pressing Control+Enter...")
            composer.focus()
            page.keyboard.press("Control+Enter")
            page.wait_for_timeout(5000)
            
            page.screenshot(path="3_after_shortcut.png")
            print("Saved screenshot: 3_after_shortcut.png")
            
            # Check if composer is still visible. If yes, try clicking the button
            if composer.is_visible():
                print("Composer still visible. Attempting manual click on Post button...")
                if tweet_btn.is_visible() and tweet_btn.is_enabled():
                    print("Clicking Post button with force=True...")
                    tweet_btn.click(force=True)
                    print("Waiting for post completion...")
                    page.wait_for_timeout(7000)
                    page.screenshot(path="4_after_click.png")
                    print("Saved screenshot: 4_after_click.png")
                else:
                    print("Error: Post button not visible or is disabled.")
                    page.screenshot(path="post_button_error.png")
                    print("Saved debug screenshot to post_button_error.png")
                    raise RuntimeError("Post button not visible or disabled")
            
            print("Verification complete.")
            browser.close()
            return True
                
    except Exception as e:
        print(f"An unexpected error occurred during Playwright execution: {e}")
        raise e

if __name__ == "__main__":
    import sys
    test_text = "Testing Playwright automated posting! 🤖 #Playwright #Automation"
    test_image = "/Users/mohmm/.gemini/antigravity-ide/brain/6d3d35fa-dc8f-4b16-acf6-2fb20dbb01bb/futuristic_bot_coding_1781916775010.png"
    
    print("Testing browser posting...")
    post_tweet_with_browser(test_text, image_path=test_image, headless=False)
