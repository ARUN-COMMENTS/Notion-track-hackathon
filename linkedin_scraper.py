import time
import logging
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UPDATED: Pinned target destination to your active live Render application server
RENDER_URL = "https://notion-job-tracking.onrender.com/add-opportunity"

def scrape_linkedin_jobs():
    """
    Automated background routine simulating extraction and forwarding of listings.
    """
    logger.info("📡 Checking for new active internship postings...")
    
    # Payload matching the exact structural layout your live Flask engine expects
    mock_job_posting = {
        "job_url": "https://linkedin.com",
        "job_text": "Tesla is hiring a Python Intern. Must know web routing frameworks, Git version control, and API payloads.",
        "student_email": "arunkuntal757@gmail.com"
    }
    
    try:
        logger.info(f"🚀 Forwarding extracted listing payload to cloud gateway: {RENDER_URL}")
        response = requests.post(RENDER_URL, json=mock_job_posting, timeout=20)
        
        if response.status_code in [200, 201]:
            logger.info("✅ Automation Trigger Successful! Opportunity logged in Notion.")
        else:
            logger.error(f"❌ Server rejected payload. Status Code: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Failed to reach your live cloud server instance: {e}")

if __name__ == "__main__":
    print("--- Initializing Background Internship Scheduler ---")
    
    # Run a manual check immediately on script startup to verify connections
    scrape_linkedin_jobs()
    
    # Set up the internal task scheduler to run automatically every 6 hours
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_linkedin_jobs, 'interval', hours=6)
    scheduler.start()
    logger.info("⏰ Background interval sequence active. Sleeping main thread container...")
    
    # Keeps the local PowerShell command window active so the background timer stays alive
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down background scraper manager routine gracefully.")
        scheduler.shutdown()
