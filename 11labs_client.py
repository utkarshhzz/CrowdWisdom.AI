import os
import logging
from dotenv import load_dotenv

# We use the official ElevenLabs SDK for conversational AI 
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceAgentClient:
    """
    Client to trigger live ElevenLabs Voice Agent sessions with dynamic debtor data.
    """
    def __init__(self):
        load_dotenv(override=True)
        
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("ELEVENLABS_AGENT_ID")
        
        if not self.api_key or not self.agent_id:
            raise ValueError("ELEVENLABS_API_KEY or ELEVENLABS_AGENT_ID is missing in .env")

        # 1. Initialize the ElevenLabs Client
        self.client = ElevenLabs(api_key=self.api_key)
        logger.info("ElevenLabs Voice Client initialized.")

    def start_collection_call(self, debtor_data: dict):
        """
        Starts a live conversation using your computer's mic/speaker, simulating a phone call.
        We inject the specific debtor's data directly into the agent's system prompt!
        """
        logger.info(f"Preparing to call {debtor_data.get('name')} for an outstanding debt of ${debtor_data.get('debt_amount')}...")

        # 2. Prepare the dynamic variables
        # These keys MUST match the {{braces}} we put in the ElevenLabs dashboard prompt!
        dynamic_vars = {
            "company_name": debtor_data.get("company_name", "Tech Solutions"),
            "debtor_name": debtor_data.get("name", "Unknown Debtor"),
            "debt_amount": str(debtor_data.get("debt_amount", "0")),
            "product": debtor_data.get("product", "Outstanding Invoice"),
            "due_date": debtor_data.get("due_date", "Recently")
        }

        try:
            # 3. Create the Conversation Session
            conversation = Conversation(
                client=self.client,
                agent_id=self.agent_id,
                requires_auth=True,
                audio_interface=DefaultAudioInterface(),
                callback_agent_response=lambda response: logger.info(f"Agent says: {response}"),
                callback_user_transcript=lambda transcript: logger.info(f"User says: {transcript}")
            )

            # 4. Start the session and immediately pass our dynamic data
            logger.info("Starting live call session... (Speak into your microphone!)")
            logger.info("Press Ctrl+C in the terminal to hang up the call.")

            # Connects to the ElevenLabs websocket server
            conversation.start_session(
                conversation_config_override={"agent": {"prompt": {"prompt_variables": dynamic_vars}}}
            )
            
            # Keeps the Python script running while you chat
            conversation.wait_for_session_end()
            logger.info("Call disconnected successfully.")

            # In Step 9, we will return call data (like call_duration) to save back to Airtable.
            return True

        except Exception as e:
            logger.error(f"Failed to start ElevenLabs voice session: {e}")
            return False

# --- UNIT TESTS ---
if __name__ == "__main__":
    # Create fake debtor data matching our Airtable structure
    sample_debtor = {
        "name": "John Smith",
        "company_name": "Acme Corp",
        "debt_amount": 500.00,
        "product": "Premium Subscription",
        "due_date": "2025-05-01"
    }

    voice_client = VoiceAgentClient()
    
    print("\n--- Starting Live Voice Agent Test ---")
    voice_client.start_collection_call(sample_debtor)