import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

def post_tweet(content):
    """
    Posts the given content to X (Twitter) using the API v2.
    """
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_SECRET")
    
    if not all([api_key, api_secret, access_token, access_secret]):
        print("Error: Missing X API credentials.")
        return False

    try:
        # Authenticate with X API v2 using Tweepy Client
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # Post the tweet
        response = client.create_tweet(text=content)
        print(f"Successfully posted tweet! Tweet ID: {response.data['id']}")
        return True
        
    except Exception as e:
        print(f"Error posting to X: {e}")
        return False

if __name__ == "__main__":
    # Be careful running this directly as it WILL post to your connected account if credentials are valid
    print("Testing mode: Not actually posting unless you uncomment the code.")
    # post_tweet("This is an automated test tweet from my new bot!")
