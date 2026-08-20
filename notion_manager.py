import logging
from datetime import datetime
from notion_client import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionManager:
    def __init__(self, token, database_id):
        self.client = Client(auth=token)
        self.database_id = database_id
    
    def create_opportunity(self, opportunity_data):
        """
        Creates a new row in Notion with opportunity details.
        Status: "Pending Review"
        """
        properties = {
            "Company": {
                "title": [{"text": {"content": opportunity_data.get("company", "Unknown")}}]
            },
            "Role": {
                "rich_text": [{"text": {"content": opportunity_data.get("role", "Not Specified")}}]
            },
            "Link": {
                "url": opportunity_data.get("job_url", "https://linkedin.com")
            },
            "Location": {
                "rich_text": [{"text": {"content": opportunity_data.get("location", "Not Specified")}}]
            },
            "Priority": {
                "select": {"name": opportunity_data.get("priority", "Medium")}
            },
            "AI Analysis": {
                "rich_text": [{"text": {"content": opportunity_data.get("ai_analysis", "No analysis")}}]
            },
            "Match Score": {
                "rich_text": [{"text": {"content": opportunity_data.get("match_score", "N/A")}}]
            },
            "Status": {
                "select": {"name": "Pending Review"}
            },
            "Timestamp": {
                "date": {"start": datetime.now().isoformat()}
            }
        }

        # FIXED: Only inject Deadline if it is a valid date string format
        deadline = opportunity_data.get("deadline", "")
        if deadline and "Not Specified" not in deadline:
            properties["Deadline"] = {"date": {"start": deadline}}

        try:
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            logger.info(f"Created Notion page: {opportunity_data.get('company')}")
            return response["id"]
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return None
    
    def update_status(self, page_id, status):
        """Update the status of an opportunity"""
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={"Status": {"select": {"name": status}}}
            )
            logger.info(f"Updated page {page_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def add_to_run_log(self, action, status, details):
        """
        Write to Run Log table safely. Drops runtime properties if headers are mismatched.
        """
        # Read the Run Log ID from your global environment configurations
        import os
        run_log_id = os.getenv("RUN_LOG_DATABASE_ID")
        if not run_log_id or "Run-log" in run_log_id:
            return

        try:
            self.client.pages.create(
                parent={"database_id": run_log_id},
                properties={
                    "Action": {"title": [{"text": {"content": action}}]},
                    "Status": {"select": {"name": status.lower()}},
                    "Details": {"rich_text": [{"text": {"content": details}}]},
                    "Timestamp": {"date": {"start": datetime.now().isoformat()}}
                }
            )
            logger.info(f"Added to Run Log: {action}")
        except Exception as e:
            logger.error(f"Error adding to run log: {e}. Check your Run Log table horizontal header names!")
