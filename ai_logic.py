import json
import logging
from google import genai
from config import GEMINI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize your Gemini AI client
try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Gemini Client: {e}")
    ai_client = None

class AIProcessor:
    def __init__(self, api_key=None):
        self.client = ai_client
    
    def process_job_posting(self, job_url, job_text, student_profile=None):
        """
        Uses Gemini 3.6 to process and extract structural parameters from postings.
        """
        if not self.client:
            logger.error("Gemini client is uninitialized.")
            return {"error": "AI Client Offline"}

        # FIXED: Doubled outer curly braces to escape Python f-string rendering syntax
        prompt = f"""
Analyze this job posting and return a JSON response with the following structure:
{{
    "company": "Company Name",
    "role": "Job Title",
    "deadline": "YYYY-MM-DD or 'Not Specified'",
    "location": "City, Country",
    "key_requirements": ["req1", "req2", "req3"],
    "priority": "High/Medium/Low",
    "match_score": "85% match",
    "red_flags": ["Any concerns or issues"],
    "ai_analysis": "2-3 sentence summary of why this is a good/bad fit",
    "draft_message": "A professional message the student can use to reach out or apply"
}}

Job URL: {job_url}

Job Description:
{job_text}

Student Profile (if available):
{student_profile or "Not provided - prioritize all relevant opportunities"}

Return ONLY valid JSON, no other text. Ensure "priority" matches exactly one of the capitalization options: High, Medium, or Low.
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )
            
            response_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(response_text)
            logger.info(f"AI processed: {result.get('company', 'Unknown')} - {result.get('role', 'Unknown')}")
            return result
        
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON")
            return {"error": "AI parsing failed"}
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            return {"error": str(e)}
    
    def draft_email(self, opportunity_data):
        """Draft an email to send to the student"""
        if not self.client:
            return "Check out this internship opportunity!"

        prompt = f"""
Write a professional email to a student about a new internship opportunity.

Company: {opportunity_data['company']}
Role: {opportunity_data['role']}
Location: {opportunity_data.get('location', 'Not Specified')}
Deadline: {opportunity_data.get('deadline', 'Not Specified')}
Key Requirements: {', '.join(opportunity_data.get('key_requirements', []))}

Make it:
- Concise (3-4 sentences)
- Friendly but professional
- Include the job link
- Encourage quick action if there's a deadline

Just the email body, no subject line.
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error drafting email: {e}")
            return "Check out this internship opportunity!"

if __name__ == "__main__":
    print("--- Running AI Processor Module Verification ---")
    processor = AIProcessor()
    test_posting = "OpenAI is hiring a Python Engineering Intern in San Francisco. Must know APIs and Git."
    res = processor.process_job_posting("https://example.com", test_posting)
    print(json.dumps(res, indent=4))
