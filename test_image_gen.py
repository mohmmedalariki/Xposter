import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    result = genai.generate_images(
        prompt="A cute robot",
        number_of_images=1,
        model="models/imagen-3.0-generate-001"
    )
    for img in result.generated_images:
        print("Success, got image.")
except Exception as e:
    print(f"Error: {e}")
