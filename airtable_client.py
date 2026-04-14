import os
import logging
from dotenv import load_dotenv
from pyairtable import Api

# setting up loggingto log th eerrros
logging.basicConfig(level=logging.INFO,format='%(asctime)s- %(levelname)s- %(message)s')
logger=logging.getLogger(__name__)

class AirtableClient:
    def __init__(self):
        load_dotenv()
        
        self.api_key=os.getenv('AIRTABLE_API_KEY')
        self.base_id=os.getenv('AIRTABLE_BASE_ID')
        self.table_name=os.getenv('AIRTABLE_TABLE_NAME','Debtors')
        
        if not self.api_key or not self.base_id:
            raise ValueError("Airtable API key and Base ID must be set in the .env file.")
        
        self.api=Api(self.api_key)
        self.table=self.api.table(self.base_id,self.table_name)
        logger.info("Airtable client initialized successfully.")
        
    def get_pending_debtors(self) -> list:
        # we will fetch all debtors whose call status pending or empty
        try:
            formula="OR({Call-Status} = 'Pending', {Call-Status} = '')"
            records=self.table.all(formula=formula)
            logger.info(f"Fetched {len(records)} pending debtors from Airtable.")
            return records
        except Exception as e:
            logger.error(f"Error fetching pending debtors: {e}")
            return []
        
        
    def update_call_status(self,record_id:str,status:str) -> bool:
        try:
            self.table.update(record_id,{'Call-Status':status})
            logger.info(f"Updated call status for record {record_id} to {status}.")
            return True
        except Exception as e:
            logger.error(f"Error updating call status for record {record_id}: {e}")
            return False
        
        
if __name__=="__main__":
    client=AirtableClient()
    debtors=client.get_pending_debtors()
    print("\n-- Pending Debtors --")
    for debtor in debtors:
        print(f"Record ID: {debtor['id']} | Data: {debtor['fields']}")