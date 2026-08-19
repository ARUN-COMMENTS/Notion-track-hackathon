import os
import requests
from dotenv import load_dotenv
from google import genai

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    ai_client = None

def ask_gemini(prompt):
    if not ai_client: return "Gemini client not initialized."
    try:
        response = ai_client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"Gemini Error: {e}"

def test_notion_connection():
    print("📋 Contacting Notion API (with proxy bypass)...")
    url = "https://notion.com"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
    }
    
    # Force requests to bypass any system proxies that might be blocking the connection
    session = requests.Session()
    session.trust_env = False 
    
    try:
        response = session.get(url, headers=headers, timeout=10)
        print(f"📡 Debug Info - HTTP Status Code: {response.status_code}")
        print(f"📡 Debug Info - Raw Server Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Success! Connected to Notion integration: '{response.json().get('name')}'")
            return True
        else:
            print("❌ Notion API returned an error.")
            return False
    except Exception as e:
        print(f"❌ Network or connection error: {e}")
        return False

if __name__ == "__main__":
    print("\n--- Starting Notion & Gemini Project ---")
    ai_response = ask_gemini("Give me a short 1-sentence motivation quote.")
    print(f"Gemini says: {ai_response}\n")
    test_notion_connection()
