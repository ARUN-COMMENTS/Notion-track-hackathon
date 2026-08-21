import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# CRITICAL: Force environment loading immediately before modules load
load_dotenv()

from ai_logic import AIProcessor
from config import FLASK_PORT, GMAIL_ADDRESS, GMAIL_PASSWORD, NOTION_DATABASE_ID, NOTION_TOKEN
from email_sender import EmailSender
from notion_manager import NotionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize managers with corrected engine variables
notion_manager = NotionManager(NOTION_TOKEN, NOTION_DATABASE_ID)
ai_processor = AIProcessor()  # Automatically picks up GEMINI_API_KEY globally
email_sender = EmailSender(GMAIL_ADDRESS, GMAIL_PASSWORD)

# ==================== ROUTES ====================

@app.route("/", methods=["GET"])
def health_check():
    """Health check - server is running"""
    return jsonify({"status": "Server is running"}), 200

@app.route("/add-opportunity", methods=["POST"])
def add_opportunity():
    """
    Receive a job posting, process it with AI, add to Notion
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400
            
        job_url = data.get("job_url")
        job_text = data.get("job_text")
        student_email = data.get("student_email", "student@college.edu")
        
        if not job_url or not job_text:
            return jsonify({"error": "Missing job_url or job_text"}), 400
        
        # Step 1: Process with AI
        logger.info(f"Processing job: {job_url}")
        ai_result = ai_processor.process_job_posting(job_url, job_text)
        
        if "error" in ai_result:
            return jsonify({"error": ai_result["error"]}), 500
            
        # Ensure job_url is passed down for database structure compatibility
        ai_result["job_url"] = job_url
        
        # Step 2: Add to Notion
        page_id = notion_manager.create_opportunity(ai_result)
        
        # Step 3: Log action
        notion_manager.add_to_run_log(
            "opportunity_found",
            "success",
            f"Found {ai_result.get('company', 'Unknown')} - {ai_result.get('role', 'Unknown')}"
        )
        
        return jsonify({
            "status": "Opportunity added to Notion for review",
            "page_id": page_id,
            "company": ai_result.get("company"),
            "role": ai_result.get("role"),
            "priority": ai_result.get("priority"),
            "message": "Waiting for human approval in Notion"
        }), 201
    
    except Exception as e:
        logger.error(f"Error in add_opportunity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/approve-and-send", methods=["POST"])
def approve_and_send():
    """
    When human approves in Notion, call this to send email
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        page_id = data.get("page_id")
        student_email = data.get("student_email")
        company = data.get("company")
        role = data.get("role")
        job_url = data.get("job_url", "")
        
        if not all([page_id, student_email, company, role]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Step 1: Draft email using AI
        opportunity_data = {
            "company": company,
            "role": role,
            "location": data.get("location", ""),
            "deadline": data.get("deadline", ""),
            "key_requirements": data.get("key_requirements", []),
            "job_url": job_url
        }
        
        email_body = ai_processor.draft_email(opportunity_data)
        
        # Step 2: Send email
        success = email_sender.send_opportunity_email(
            student_email,
            opportunity_data,
            email_body
        )
        
        if success:
            # Step 3: Update Notion status
            notion_manager.update_status(page_id, "Sent")
            notion_manager.add_to_run_log(
                "email_sent",
                "success",
                f"Email sent to {student_email} for {company} - {role}"
            )
            
            return jsonify({
                "status": "Email sent successfully",
                "student": student_email
            }), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500
    
    except Exception as e:
        logger.error(f"Error in approve_and_send: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/reject", methods=["POST"])
def reject_opportunity():
    """Reject an opportunity"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400
            
        page_id = data.get("page_id")
        reason = data.get("reason", "Not a fit")
        
        notion_manager.update_status(page_id, "Rejected")
        notion_manager.add_to_run_log(
            "opportunity_rejected",
            "rejected",
            f"Reason: {reason}"
        )
        
        return jsonify({"status": "Opportunity rejected"}), 200
    except Exception as e:
        logger.error(f"Error rejecting: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== RUN SERVER ====================

# OLD LINE:
# app.run(debug=True, port=FLASK_PORT)
@app.route("/check-approvals", methods=["GET"])
def check_approvals():
    """
    Periodically checks for human-approved opportunities in Notion,
    drafts custom outreach emails with Gemini, and fires them via SMTP.
    """
    try:
        # Fetch pages currently matching the 'Pending Review' filter layer
        pending = notion_manager.get_pending_opportunities()
        checked_count = 0
        sent_count = 0
        
        for page in pending:
            properties = page.get("properties", {})
            
            # Safely navigate to the current status choice tag name string
            status_obj = properties.get("Status", {}).get("select", {})
            status = status_obj.get("name") if status_obj else "Pending Review"
            
            # If a human has manually toggled the tag inside the Notion dashboard grid
            if status == "Approved":
                checked_count += 1
                
                # Extract structural property parameters defensively
                company_list = properties.get("Company", {}).get("title", [])
                company = company_list[0]["text"]["content"] if company_list else "Unknown Company"
                
                role_list = properties.get("Role", {}).get("rich_text", [])
                role = role_list[0]["text"]["content"] if role_list else "Internship Position"
                
                job_url = properties.get("Link", {}).get("url", "https://linkedin.com")
                
                # UPDATED: Direct notifications back to your actual target email account variables
                student_email = GMAIL_ADDRESS  
                
                opportunity_data = {
                    "company": company,
                    "role": role,
                    "job_url": job_url,
                    "location": "See posting listing details",
                    "deadline": "Review timeline on page layout",
                    "key_requirements": ["Python development scripting", "API routing infrastructure"]
                }
                
                # Leverage Gemini 3.6 to compile a professional outreach email body layout
                email_body = ai_processor.draft_email(opportunity_data)
                
                # Route the generated package out through Gmail secure SMTP servers
                success = email_sender.send_opportunity_email(student_email, opportunity_data, email_body)
                
                if success:
                    # Update status tag to 'Sent' and update background diagnostic steps logs
                    notion_manager.update_status(page["id"], "Sent")
                    notion_manager.add_to_run_log(
                        "email_sent",
                        "success",
                        f"Automated approval notification message pushed directly to {student_email}"
                    )
                    sent_count += 1
        
        return jsonify({
            "status": "Check approval pipeline process executed successfully",
            "opportunities_checked": checked_count,
            "emails_dispatched": sent_count
        }), 200
    
    except Exception as e:
        logger.error(f"Error checking approvals layout configurations: {e}")
        return jsonify({"error": str(e)}), 500

# NEW REPLACEMENT LINES:
if __name__ == "__main__":
    logger.info("Starting Internship Tracker Server...")
    # Force the app to listen externally to all cloud gateway routes
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
