import os
import json
import requests
from summarizer import generate_image_for_tweet
from linkedin_api import post_linkedin_via_api
from dotenv import load_dotenv

load_dotenv()

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), "playbook_chunks")
STATE_FILE = os.path.join(os.path.dirname(__file__), "linkedin_state.json")
SKILL_FILE = os.path.join(os.path.dirname(__file__), "writing-linkedin-posts-1.0.0", "SKILL.md")

def get_next_playbook():
    """Reads the state file and returns the next unposted playbook dictionary."""
    if not os.path.exists(PLAYBOOKS_DIR):
        print(f"Error: Directory {PLAYBOOKS_DIR} does not exist.")
        return None
        
    all_files = sorted([f for f in os.listdir(PLAYBOOKS_DIR) if f.endswith('.json')])
    if not all_files:
        print("Error: No JSON playbook files found.")
        return None
        
    state = {"current_file": all_files[0], "current_index": 0}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as sf:
                state = json.load(sf)
        except Exception:
            pass

    current_file = state["current_file"]
    current_index = state["current_index"]

    # In case the file from state was deleted or doesn't exist
    if current_file not in all_files:
        current_file = all_files[0]
        current_index = 0

    file_path = os.path.join(PLAYBOOKS_DIR, current_file)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        playbooks = data.get("playbooks", [])
        
    if current_index >= len(playbooks):
        # Move to next file
        file_idx = all_files.index(current_file)
        if file_idx + 1 < len(all_files):
            next_file = all_files[file_idx + 1]
            state["current_file"] = next_file
            state["current_index"] = 0
            
            # Save new state and recurse
            with open(STATE_FILE, "w", encoding="utf-8") as sf:
                json.dump(state, sf, indent=2)
            return get_next_playbook()
        else:
            print("All playbooks have been exhausted!")
            return None
            
    return playbooks[current_index], state

def advance_linkedin_state(state):
    """Increments the playbook index after a successful post."""
    state["current_index"] += 1
    with open(STATE_FILE, "w", encoding="utf-8") as sf:
        json.dump(state, sf, indent=2)
    print(f"Advanced LinkedIn state to file: {state['current_file']}, index: {state['current_index']}")

def generate_linkedin_text(playbook_data):
    """Uses the Big Pickle API to generate a LinkedIn post based on the playbook data."""
    # Load the LinkedIn writing skill
    skill_content = ""
    if os.path.exists(SKILL_FILE):
        with open(SKILL_FILE, "r", encoding="utf-8") as f:
            skill_content = f.read()

    playbook_json = json.dumps(playbook_data, indent=2)
    writeup_url = playbook_data.get("meta", {}).get("url", "")
    
    prompt = f"""
Imagine you're teaching a bug hunter.
You are an expert cybersecurity thought leader and top-tier LinkedIn creator.
I will give you a detailed bug bounty / cybersecurity playbook.
Your task is to write a highly engaging, high-quality LinkedIn post summarizing this playbook.

Strict Rules & Tone Guidelines:
{skill_content}

At the very end of your post, you MUST include this exact link to the original writeup:
{writeup_url}

Also, make sure to include 3-5 highly relevant hashtags (#s) after the URL.

The Playbook Data:
{playbook_json}

Please output ONLY the final text of the LinkedIn post. Do not include any introductory remarks.
"""

    url = "https://opencode.ai/zen/v1/chat/completions"
    api_key = os.getenv("OPENCODE_API_KEY", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "big-pickle",
        "max_tokens": 1500,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system", 
                "content": "You are an elite, professional LinkedIn ghostwriter for cybersecurity experts. You write detailed, high-value, and comprehensive posts with bullet points, actionable advice, and deep insights. Never output short or cut-off responses."
            },
            {"role": "user", "content": prompt}
        ]
    }
    
    print("Generating LinkedIn text via Big Pickle...")
    for attempt in range(3):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        elif response.status_code == 429:
            print(f"Rate limited (429). Attempt {attempt+1} of 3. Waiting 60s...")
            import time
            time.sleep(60)
        else:
            print(f"Failed to generate text. API responded with {response.status_code}")
            break
    return None

def process_next_linkedin_post():
    print("\n--- Executing Job: Preparing next LinkedIn Post ---")
    result = get_next_playbook()
    if not result:
        print("No playbooks left to process.")
        return
        
    playbook_data, state = result
    title = playbook_data.get("meta", {}).get("title", "Unknown Playbook")
    print(f"Processing playbook: '{title}' from {state['current_file']} (Index: {state['current_index']})")
    
    # 1. Generate text
    post_text = generate_linkedin_text(playbook_data)
    if not post_text:
        raise RuntimeError("LinkedIn text generation failed (likely 429 Rate Limit from OpenCode API).")
        
    print(f"Generated LinkedIn Post:\n---\n{post_text}\n---")
    
    # 2. Generate image using Gemini
    print("Generating engaging image for LinkedIn...")
    image_path = generate_image_for_tweet(post_text, output_path="current_linkedin_image.jpg")
    
    # 3. Publish to LinkedIn via API
    print("Publishing to LinkedIn...")
    success = post_linkedin_via_api(post_text, image_path=image_path)
    
    if success:
        advance_linkedin_state(state)
        print("Done processing this playbook chunk.")
    else:
        print("Failed to post to LinkedIn.")
        raise RuntimeError("LinkedIn posting failed (returned False)")

if __name__ == "__main__":
    process_next_linkedin_post()
