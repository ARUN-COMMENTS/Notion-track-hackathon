import logging
from flask import Flask, jsonify, request
from ai_logic import AIProcessor
from config import FLASK_PORT, GMAIL_ADDRESS, GMAIL_PASSWORD, NOTION_DATABASE_ID, NOTION_TOKEN
from email_sender import EmailSender

# UPDATED: Importing from the correct renamed module file
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

if __name__ == "__main__":
    logger.info("Starting Internship Tracker Server...")
    app.run(debug=True, port=FLASK_PORT)
