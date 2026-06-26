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

CRITICAL FORMATTING RULES FOR LINKEDIN:
1. NO MARKDOWN: LinkedIn does NOT render markdown. Do NOT use asterisks (**) for bold, underscores (_) for italics, or hashes (#) for headers.
2. EMPHASIS: If you must emphasize a word, use UPPERCASE instead of bold/italics.
3. LISTS: Use simple unicode bullet points (•, -, or 1.) instead of markdown asterisks. 
4. COMPLETENESS: The post MUST have a definitive, natural ending. Do NOT cut off mid-sentence. Do NOT leave placeholders.

At the very end of your post, you MUST include this exact link to the original writeup:
{writeup_url}

Also, make sure to include 3-5 highly relevant hashtags (#s) AFTER the URL.

The Playbook Data:
{playbook_json}

Please output ONLY the final text of the LinkedIn post in pure plain text format. Do not include any introductory remarks.
"""

    url = "https://opencode.ai/zen/v1/chat/completions"
    api_key = os.getenv("OPENCODE_API_KEY", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "big-pickle",
        "max_tokens": 4000,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system", 
                "content": "You are an elite, professional LinkedIn ghostwriter for cybersecurity experts. You write detailed, high-value, and comprehensive posts. You NEVER use markdown formatting (no **, no _, no # for headers). You output clean, beautifully spaced plain text that is ready to copy-paste into LinkedIn."
            },
            {"role": "user", "content": prompt}
        ]
    }
    
    print("Generating LinkedIn text via Big Pickle...")
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()
                if not content:
                    print(f"API returned 200 OK but empty content! Attempt {attempt+1}/3. Retrying in 10s...", flush=True)
                    import time
                    time.sleep(10)
                    continue
                return content
            elif response.status_code == 429:
                print(f"Rate limited (429). Attempt {attempt+1} of 3. Waiting 60s...", flush=True)
                import time
                time.sleep(60)
            else:
                raise RuntimeError(f"OpenCode API failed with {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Network error on attempt {attempt+1}: {e}", flush=True)
            import time
            time.sleep(10)
            
    raise RuntimeError("OpenCode API exhausted all retries or hit a hard rate limit.")

def generate_image_for_linkedin(post_content, output_path="current_linkedin_image.jpg"):
    """
    Uses a dedicated Gemini API key to generate a visual prompt,
    then fetches the generated image from pollinations.ai.
    """
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY_LINKEDIN")
    if not api_key:
        print("Error: GEMINI_API_KEY_LINKEDIN not set. Using fallback image generation.")
        from summarizer import generate_image_for_tweet
        return generate_image_for_tweet(post_content, output_path)
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are an expert AI image prompt engineer. I will give you a LinkedIn post about cybersecurity.
    Your task is to write a highly detailed and visually hooking image generation prompt that perfectly captures the specific technical core of the post.
    
    CRITICAL INSTRUCTION: To avoid all images looking the same, you MUST pick a distinct and creative artistic style for this prompt. 
    Examples of styles you can randomly use: 3D Blender Render, Synthwave, minimalist vector art, hyper-realistic macro photography, 90s anime, glitch art, isometric 3D, neon noir, pencil sketch, or pixel art.
    Do NOT always rely on standard "cyberpunk hacker in a dark room" stereotypes. Make it conceptually abstract, creative, and strictly tailored to the specific concept in the post.
    
    Rules:
    1. Output ONLY the image prompt. Do not include any quotes, intro, or outro text.
    2. Keep it under 50 words.
    
    Post:
    {post_content}
    """
    
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            image_prompt = response.text.strip()
            print(f"Generated Image Prompt for LinkedIn: {image_prompt}")
            
            url = f"https://image.pollinations.ai/prompt/{image_prompt.replace(' ', '%20')}"
            res = requests.get(url)
            if res.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                print(f"Successfully generated and saved LinkedIn image to {output_path}")
                return output_path
            else:
                print(f"Error fetching image from pollinations.ai: {res.status_code}")
                return None
        except Exception as e:
            print(f"Error generating LinkedIn image (Attempt {attempt+1}/3): {e}")
            if attempt < 2:
                import time
                time.sleep(60)
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
    
    # 2. Generate image using dedicated Gemini key
    print("Generating engaging image for LinkedIn...")
    image_path = generate_image_for_linkedin(post_text, output_path="current_linkedin_image.jpg")
    
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
