import requests
import json

def test_big_pickle():
    url = "https://opencode.ai/zen/v1/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "big-pickle",
        "messages": [
            {"role": "user", "content": "Hello! Please reply with a short greeting."}
        ]
    }

    print(f"Testing endpoint: {url}")
    print(f"Payload: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Response Text:")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_big_pickle()
