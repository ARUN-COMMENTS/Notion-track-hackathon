import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, gmail_address, gmail_password):
        self.gmail_address = gmail_address
        self.gmail_password = gmail_password
    
    def send_opportunity_email(self, recipient_email, opportunity_data, email_body):
        """
        Send internship opportunity to student via email
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.gmail_address
            msg["To"] = recipient_email
            msg["Subject"] = f"🎯 New Opportunity: {opportunity_data['role']} at {opportunity_data['company']}"
            
            # Build email body
            full_body = f"""
Hi there!

We found a new internship opportunity for you:

**Company:** {opportunity_data['company']}
**Role:** {opportunity_data['role']}
**Location:** {opportunity_data.get('location', 'Not Specified')}
**Deadline:** {opportunity_data.get('deadline', 'Not Specified')}
**Priority:** {opportunity_data.get('priority', 'Medium')}

**Match Score:** {opportunity_data.get('match_score', 'N/A')}

**AI Analysis:**
{opportunity_data.get('ai_analysis', 'No analysis available')}

**Apply Here:** {opportunity_data['job_url']}

{email_body}

---
This opportunity was found and analyzed by our Internship Tracker system.
            """
            
            msg.attach(MIMEText(full_body, "plain"))
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.gmail_address, self.gmail_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {recipient_email}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    print("--- Running Local Outbound Email Handshake Test ---")
    my_email = os.getenv("GMAIL_ADDRESS")
    my_pass = os.getenv("GMAIL_PASSWORD")
    
    if my_email and my_pass and "gmail.com" in my_email:
        sender = EmailSender(my_email, my_pass)
        dummy_job = {"company": "Test Comp", "role": "Test Intern", "job_url": "https://example.com"}
        # Tests the connection by attempting to shoot an email back to yourself
        sender.send_opportunity_email(my_email, dummy_job, "This is a baseline server text test.")
    else:
        print("⚠️ Missing true Gmail App Passwords inside your .env configuration file.")
