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
    
    try:
        response = model.generate_content(prompt)
        tweet = response.text.strip()
        
        # Strip surrounding quotes if the model added them accidentally
        if tweet.startswith('"') and tweet.endswith('"'):
            tweet = tweet[1:-1]
            
        return tweet
    except Exception as e:
        print(f"Error generating summary with Gemini: {e}")
        return None

def generate_image_for_tweet(tweet_content, output_path="tip_image.jpg"):
    """
    Uses Gemini to generate a highly visual prompt based on the tweet,
    and then fetches a generated image from pollinations.ai.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set.")
        return None
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are an expert AI image prompt engineer. I will give you a tweet about bug bounty hunting.
    Your task is to write a highly detailed and visually hooking image generation prompt that perfectly captures the specific technical core of the tweet.
    
    CRITICAL INSTRUCTION: To avoid all images looking the same, you MUST pick a distinct and creative artistic style for this prompt. 
    Examples of styles you can randomly use: 3D Blender Render, Synthwave, minimalist vector art, hyper-realistic macro photography, 90s anime, glitch art, isometric 3D, neon noir, pencil sketch, or pixel art.
    Do NOT always rely on standard "cyberpunk hacker in a dark room" stereotypes. Make it conceptually abstract, creative, and strictly tailored to the specific concept in the tweet.
    
    Rules:
    1. Output ONLY the image prompt. Do not include any quotes, intro, or outro text.
    2. Keep it under 50 words.
    
    Tweet:
    {tweet_content}
    """
    
    try:
        response = model.generate_content(prompt)
        image_prompt = response.text.strip()
        print(f"Generated Image Prompt: {image_prompt}")
        
        # Call pollinations.ai
        url = f"https://image.pollinations.ai/prompt/{image_prompt.replace(' ', '%20')}"
        res = requests.get(url)
        if res.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(res.content)
            print(f"Successfully generated and saved image to {output_path}")
            return output_path
        else:
            print(f"Error fetching image from pollinations.ai: {res.status_code}")
            return None
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

if __name__ == "__main__":
    # For testing the summarizer independently
    test_email = "Hi team, we just launched the new version 2.0 of our software. It includes a brand new UI, faster performance, and bug fixes for the login screen. Please share this with the community!"
    print("Summarizing...")
    summary = summarize_for_twitter(test_email)
    print(f"Tweet ({len(summary)} chars):\n{summary}")
