import logging
import time
from airtable_client import AirtableClient
from agent.manager import DebtCollectionManager
from learning.feedback_store import FeedbackStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("====================================")
    logger.info("Automated Debt Collection System AI")
    logger.info("====================================")
    
    airtable = AirtableClient()
    manager = DebtCollectionManager()
    feedback = FeedbackStore()

    debtors = airtable.get_pending_debtors()
    if not debtors:
        logger.info("No pending debtors found in Airtable.")
        return

    logger.info(f"Loaded {len(debtors)} debtors to process.")
    
    for record in debtors:
        record_id = record['id']
        data = record['fields']
        name = data.get('name', 'Unknown')
        
        logger.info(f"\n--- Processing Profile: {name} ---")
        
        # 1. Provide Context & Run LLM Orchestration
        # Here we pass the debtor data to Hermes. Hermes will check the time, assess previous 
        # learning feedback, and potentially trigger the Voice Bot entirely on its own! 
        decision = manager.process_debtor(data)
        
        # 2. Closed Learning Loop Storage
        if decision == "CALLED":
            logger.info(f"[main] The Hermes LLM successfully called {name}.")
            # Save the positive interaction back to our JSON memory so Hermes remembers next time
            feedback.add_feedback(name, "Call Connected Successfully")
            
            # Update Airtable so we don't call them again today
            airtable.update_call_status(record_id, "Called")
            
        elif decision == "SKIPPED":
            logger.info(f"[main] Hermes decided to SKIP calling {name}.")
            
            # If for example it skipped because it was nighttime, log it
            feedback.add_feedback(name, "Call skipped (Outside Hours or Holiday)")
            
        # Give the API a brief rest
        time.sleep(2)

if __name__ == "__main__":
    main()