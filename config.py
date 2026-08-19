import os
from dotenv import load_dotenv

# Load environmental variables from the local .env file
load_dotenv()

# Notion Configuration Layout
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Updated API Keys (Switched from Anthropic to Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Automated Email Configuration
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # Remember: Must be a 16-character App Password

# Flask Server Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

# Diagnostics check to make sure keys load correctly in memory
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY is not loaded. Check your .env file.")
if not NOTION_TOKEN:
    print("⚠️ Warning: NOTION_TOKEN is not loaded. Check your .env file.")
