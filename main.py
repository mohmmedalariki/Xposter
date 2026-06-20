import os
import json
import time
import schedule
from summarizer import summarize_for_twitter, generate_image_for_tweet
from twitter_playwright import post_tweet_with_browser

# Directory paths
TIPS_DIR = os.path.join(os.path.dirname(__file__), "tips")
STATE_FILE = os.path.join(os.path.dirname(__file__), "tips_state.json")

def get_next_tip_file():
    """
    Finds the next unposted bug bounty tip file from the tips directory.
    Returns: (filename, content)
    """
    if not os.path.exists(TIPS_DIR):
        print(f"Error: Tips directory {TIPS_DIR} does not exist.")
        return None, None
        
    # Get all markdown files in alphabetical order
    all_files = sorted([f for f in os.listdir(TIPS_DIR) if f.lower().endswith('.md')])
    if not all_files:
        print("Error: No markdown files found in the tips directory.")
        return None, None
        
    # Load posting state
    state = {"last_posted_file": "", "posted_files": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as sf:
                state = json.load(sf)
        except Exception as e:
            print(f"Warning: Could not read state file, starting fresh: {e}")
            
    posted_set = set(state.get("posted_files", []))
    
    # Find the first file that hasn't been posted yet
    next_file = None
    for f in all_files:
        if f not in posted_set:
            next_file = f
            break
            
    # If all files are posted, start over (cycle the queue)
    if not next_file:
        print("All tips have been posted. Resetting queue state to start over...")
        state["posted_files"] = []
        next_file = all_files[0]
        
    file_path = os.path.join(TIPS_DIR, next_file)
    try:
        with open(file_path, "r", encoding="utf-8") as tf:
            content = tf.read()
        return next_file, content
    except Exception as e:
        print(f"Error reading tip file {next_file}: {e}")
        return None, None

def mark_tip_as_posted(filename):
    """
    Saves the file to state as posted.
    """
    state = {"last_posted_file": "", "posted_files": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as sf:
                state = json.load(sf)
        except Exception:
            pass
            
    if filename not in state["posted_files"]:
        state["posted_files"].append(filename)
    state["last_posted_file"] = filename
    
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as sf:
            json.dump(state, sf, indent=2)
        print(f"Updated queue state: marked '{filename}' as posted.")
    except Exception as e:
        print(f"Error saving queue state: {e}")

def job():
    print("\n--- Executing Job: Posting next Bug Bounty Tip ---")
    
    # 1. Fetch next tip file
    filename, tip_content = get_next_tip_file()
    
    if not filename or not tip_content:
        print("No tip available to process.")
        return
        
    print(f"Processing tip file: '{filename}'")
    
    # 2. Summarize with Gemini (uses SKILL.md instructions and 280-char limit)
    print("Generating post content with Gemini...")
    tweet_content = summarize_for_twitter(tip_content)
    
    if not tweet_content:
        print("Failed to generate post. Skipping...")
        return
        
    print(f"Generated Tweet:\n---\n{tweet_content}\n---")
    
    # Final length check
    if len(tweet_content) > 280:
        print("Warning: Tweet is over 280 characters. Truncating...")
        tweet_content = tweet_content[:277] + "..."
        
    # 3. Generate an engaging image for the tweet
    print("Generating engaging image for the post...")
    image_path = generate_image_for_tweet(tweet_content, output_path="current_tip_image.jpg")
    
    # 4. Post to X via Playwright Browser (headless)
    print("Posting to X...")
    success = post_tweet_with_browser(tweet_content, image_path=image_path, headless=True)
    
    if success:
        mark_tip_as_posted(filename)
        print("Done processing this tip.")
    else:
        print("Failed to post tweet.")
        raise RuntimeError("Tweet posting failed (returned False)")

def run_continuously():
    """
    Runs the job periodically using the schedule library.
    """
    # Schedule to run every day at 8:00 AM, 2:00 PM, and 8:00 PM
    schedule.every().day.at("08:00").do(job)
    schedule.every().day.at("14:00").do(job)
    schedule.every().day.at("20:00").do(job)
    
    print("Started Automated X Poster (Bug Bounty Tips). Press Ctrl+C to exit.")
    print("Scheduled to post to X daily at 08:00, 14:00, and 20:00.")
    
    # Run once immediately for diagnostic check
    print("\nPerforming initial run to verify everything is operational...")
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_continuously()
