import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    result = client.models.generate_images(
        model='imagen-3.0-generate-001',
        prompt='A cute robot hacker, cyberpunk style, neon lights',
        config=dict(
            number_of_images=1,
            output_mime_type="image/png",
        )
    )
    for idx, generated_image in enumerate(result.generated_images):
        generated_image.image.save(f"test_genai_output.png")
        print("Success! Image saved to test_genai_output.png")
except Exception as e:
    print(f"Error: {e}")
