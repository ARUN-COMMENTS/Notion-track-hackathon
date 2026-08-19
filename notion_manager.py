from notion_client import Client
from datetime import datetime
import logging

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
        try:
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Company": {
                        "title": [{"text": {"content": opportunity_data["company"]}}]
                    },
                    "Role": {
                        "rich_text": [{"text": {"content": opportunity_data["role"]}}]
                    },
                    "Link": {
                        "url": opportunity_data["job_url"]
                    },
                    "Deadline": {
                        "date": {"start": opportunity_data.get("deadline", "")}
                    },
                    "Location": {
                        "rich_text": [{"text": {"content": opportunity_data.get("location", "Not Specified")}}]
                    },
                    "Priority": {
                        "select": {"name": opportunity_data.get("priority", "Medium")}
                    },
                    "AI Analysis": {
                        "rich_text": [{"text": {"content": opportunity_data.get("ai_analysis", "")}}]
                    },
                    "Match Score": {
                        "rich_text": [{"text": {"content": opportunity_data.get("match_score", "")}}]
                    },
                    "Status": {
                        "select": {"name": "Pending Review"}
                    },
                    "Timestamp": {
                        "date": {"start": datetime.now().isoformat()}
                    }
                }
            )
            logger.info(f"Created Notion page: {opportunity_data['company']}")
            return response["id"]
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return None
    
    def update_status(self, page_id, status):
        """Update the status of an opportunity (Pending/Approved/Rejected/Sent)"""
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"select": {"name": status}}
                }
            )
            logger.info(f"Updated page {page_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def add_to_run_log(self, action, status, details):
        """
        Write to Run Log table.
        action: "opportunity_found" / "email_sent" / "rejected"
        """
        try:
            self.client.pages.create(
                parent={"database_id": self.database_id},  # Should point to RUN_LOG database
                properties={
                    "Action": {
                        "title": [{"text": {"content": action}}]
                    },
                    "Status": {
                        "select": {"name": status}
                    },
                    "Details": {
                        "rich_text": [{"text": {"content": details}}]
                    },
                    "Timestamp": {
                        "date": {"start": datetime.now().isoformat()}
                    }
                }
            )
            logger.info(f"Added to Run Log: {action}")
        except Exception as e:
            logger.error(f"Error adding to run log: {e}")
    
    def get_pending_opportunities(self):
        """Get all opportunities pending approval"""
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Status",
                    "select": {"equals": "Pending Review"}
                }
            )
            return response["results"]
        except Exception as e:
            logger.error(f"Error fetching pending opportunities: {e}")
            return []
# Add this at the very bottom of your file for easy project usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    print("--- Testing Notion Manager Initialization ---")
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DATABASE_ID")
    
    if token and db_id:
        manager = NotionManager(token, db_id)
        print("✅ NotionManager instance created successfully and ready for actions.")
    else:
        print("⚠️ Missing tokens in .env. Cannot complete baseline test.")

