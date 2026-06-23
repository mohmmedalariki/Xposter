import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def summarize_for_twitter(email_content):
    """
    Takes email content and uses Gemini to summarize it into a tweet.
    Ensures the output follows SKILL.md rules and is under 280 characters.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set.")
        return None

    # Load SKILL.md guidelines
    skill_content = ""
    try:
        skill_path = os.path.join(os.path.dirname(__file__), "SKILL.md")
        if os.path.exists(skill_path):
            with open(skill_path, "r", encoding="utf-8") as f:
                skill_content = f.read()
    except Exception as e:
        print(f"Warning: Could not load SKILL.md: {e}")

    genai.configure(api_key=api_key)

    # Use the fast, modern flash model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are an expert social media manager. I will give you the content of an email.
    Your task is to summarize this email into an engaging, single X (Twitter) post following the style guidelines and rules provided below.
    
    Style Guidelines:
    {skill_content}
    
    Strict Constraint Rules:
    1. The output MUST be strictly under 280 characters per post (this is a hard limit).
    2. Do NOT use hashtags unless absolutely necessary (maximum 1-2).
    3. Emojis should be used very sparingly.
    4. Only output the text of the tweet itself. Do not include quotes or intro/outro text.
    
    Email Content:
    {email_content}
    """
    
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            tweet = response.text.strip()
            
            # Strip surrounding quotes if the model added them accidentally
            if tweet.startswith('"') and tweet.endswith('"'):
                tweet = tweet[1:-1]
                
            return tweet
        except Exception as e:
            print(f"Error generating summary with Gemini (Attempt {attempt+1}/3): {e}")
            if attempt < 2:
                import time
                # Google Gemini 429 often requests ~45s of wait time
                time.sleep(60)
    return None

def generate_image_for_tweet(tweet_content, output_path="tip_image.jpg"):
    """
    Uses OpenCode API to generate a highly visual prompt based on the text,
    and then fetches a generated image from AI Horde async API.
    """
    opencode_api_key = os.getenv("OPENCODE_API_KEY", "")
    horde_api_key = os.getenv("HORDE_API_KEY", "0000000000")
    
    # 1. Generate visual prompt using OpenCode
    prompt_instruction = f"""
    You are an expert AI image prompt engineer. I will give you a social media post about cybersecurity.
    Your task is to write a highly detailed and visually hooking image generation prompt that perfectly captures the specific technical core of the post.
    
    CRITICAL INSTRUCTION: To avoid all images looking the same, you MUST pick a distinct and creative artistic style for this prompt. 
    Examples of styles you can randomly use: 3D Blender Render, Synthwave, minimalist vector art, hyper-realistic macro photography, 90s anime, glitch art, isometric 3D, neon noir, pencil sketch, or pixel art.
    Do NOT always rely on standard "cyberpunk hacker in a dark room" stereotypes. Make it conceptually abstract, creative, and strictly tailored to the specific concept in the tweet.
    
    Rules:
    1. Output ONLY the image prompt. Do not include any quotes, intro, or outro text.
    2. Keep it under 50 words.
    
    Post:
    {tweet_content}
    """
    
    opencode_url = "https://opencode.ai/zen/v1/chat/completions"
    opencode_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {opencode_api_key}"
    }
    opencode_data = {
        "model": "big-pickle",
        "max_tokens": 1000,
        "temperature": 0.8,
        "messages": [
            {"role": "user", "content": prompt_instruction}
        ]
    }
    
    image_prompt = "A glowing neon lock on a digital circuit board, cyberpunk style" # fallback
    try:
        response = requests.post(opencode_url, headers=opencode_headers, json=opencode_data, timeout=60)
        if response.status_code == 200:
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if content:
                image_prompt = content
                print(f"Generated Image Prompt via OpenCode: {image_prompt}")
            else:
                print("OpenCode returned empty prompt, using fallback.")
        else:
            print(f"OpenCode failed ({response.status_code}), using fallback.")
    except Exception as e:
        print(f"OpenCode error ({e}), using fallback.")

    # 2. Generate image using AI Horde
    horde_url = "https://stablehorde.net/api/v2/generate/async"
    horde_headers = {
        "apikey": horde_api_key,
        "Content-Type": "application/json"
    }
    horde_payload = {
        "prompt": image_prompt,
        "params": {
            "width": 512,
            "height": 512,
            "sampler_name": "k_dpmpp_2m",
            "steps": 20,
            "cfg_scale": 7.5,
            "n": 1
        },
        "models": ["Deliberate"],
        "censor_nsfw": True,
        "nsfw": False
    }

    print("Sending generation request to AI Horde...")
    try:
        response = requests.post(horde_url, headers=horde_headers, json=horde_payload, timeout=60)
        if response.status_code != 202:
            print(f"Error starting AI Horde job: {response.status_code} - {response.text}")
            return None
            
        job_id = response.json().get("id")
        print(f"AI Horde job submitted successfully. Job ID: {job_id}")
        
        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"
        
        print("Waiting for AI Horde image to generate...")
        import time
        for _ in range(60): # wait up to 5 minutes (60 * 5s)
            check_resp = requests.get(check_url, timeout=30)
            if check_resp.status_code != 200:
                print(f"Error checking Horde status: {check_resp.status_code}")
                time.sleep(5)
                continue
                
            check_data = check_resp.json()
            if check_data.get("done"):
                print("Generation complete! Fetching image...")
                status_resp = requests.get(status_url, timeout=30)
                generations = status_resp.json().get("generations", [])
                if generations:
                    img_url = generations[0].get("img")
                    img_data = requests.get(img_url, timeout=60).content
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    print(f"Success! Image saved to {output_path}")
                    return output_path
                else:
                    print("No generations found in AI Horde response.")
                break
            elif check_data.get("faulted"):
                print("AI Horde job faulted (failed to generate).")
                break
            else:
                time.sleep(5)
                
    except Exception as e:
        print(f"AI Horde error: {e}")
        
    return None

if __name__ == "__main__":
    # For testing the summarizer independently
    test_email = "Hi team, we just launched the new version 2.0 of our software. It includes a brand new UI, faster performance, and bug fixes for the login screen. Please share this with the community!"
    print("Summarizing...")
    summary = summarize_for_twitter(test_email)
    print(f"Tweet ({len(summary)} chars):\n{summary}")
