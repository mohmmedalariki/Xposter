import requests

prompt = "A mysterious bug bounty hunter looking at a glowing laptop screen in a dark room with neon lights, realistic, cinematic lighting"
url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
res = requests.get(url)
if res.status_code == 200:
    with open("test_pollinations.jpg", "wb") as f:
        f.write(res.content)
    print("Success! Image saved.")
else:
    print(f"Error: {res.status_code} - {res.text}")
