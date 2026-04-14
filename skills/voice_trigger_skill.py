import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from elevenlabs_client import VoiceAgentClient

logger = logging.getLogger(__name__)

def trigger_voice_collection_call(name: str, company_name: str, debt_amount: float, product: str, due_date: str) -> str:
    """
    Hermes Skill: Triggers an autonomous ElevenLabs voice agent to call a debtor.
    Use this tool ONLY AFTER checking if it is a good time to call using the scheduling tool.
    
    Args:
        name: The name of the debtor (e.g. 'John Smith')
        company_name: The company owed the debt (e.g. 'Acme Corp')
        debt_amount: The amount owed in dollars (e.g. 500.00)
        product: The product or service the debt is for
        due_date: The date the debt was due (YYYY-MM-DD)
        
    Returns:
        A string indicating if the call was successfully completed.
    """
    logger.info(f"Hermes triggered the Voice Dialer Tool for {name}!")
    
    debtor_data = {
        "name": name,
        "company_name": company_name,
        "debt_amount": debt_amount,
        "product": product,
        "due_date": due_date
    }
    
    try:
        # VERCEL SAFEGUARD: Serverless functions do not have microphones/speakers!
        if os.getenv("VERCEL") == "1":
            logger.info(f"[Vercel Mock] Simulated Voice Agent dial for {name}.")
            return "SUCCESS: The call was simulated in the cloud. Awaiting call outcome data."
            
        voice_client = VoiceAgentClient()
        success = voice_client.start_collection_call(debtor_data)
        
        if success:
            logger.info(f"Voice collection call for {name} finished successfully.")
            return "SUCCESS: The call was completed. Awaiting call outcome data."
        else:
            return "FAILED: The voice agent could not connect."
            
    except Exception as e:
        logger.error(f"Error in Voice Dialer Tool: {e}")
        return f"FAILED: Error occurred -> {e}"
