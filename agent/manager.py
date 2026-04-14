import os
import json
import logging
from dotenv import load_dotenv

# Instead of re-writing MiroShark from scratch, we import its core agents and memory system
# Note: Ensure you have installed the required libraries inside miroshark (e.g. openai)
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from miroshark.core.agent import BaseAgent
from miroshark.core.llm import OpenAILLM
from miroshark.core.memory import SimpleMemory

# Import our custom skill
from skills.scheduling_skill import check_if_good_time_to_call

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DebtCollectionManager:
    """
    The main Hermes/MiroShark Agent that coordinates the debt collection process.
    """
    def __init__(self):
        load_dotenv(override=True)
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            raise ValueError("OPENROUTER_API_KEY is missing in .env file.")

        # 1. Initialize the LLM Engine (Using OpenRouter to access free Mistral models)
        # MiroShark uses the OpenAI format under the hood, so we just point the base_url to OpenRouter
        self.llm = OpenAILLM(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            model="mistralai/mistral-7b-instruct:free"  # Free model on OpenRouter!
        )

        # 2. Set up Memory
        # This helps the agent remember the context of its current reasoning task
        self.memory = SimpleMemory()

        # 3. Create the Agent
        # We give the agent a system prompt telling it exactly what its job is.
        system_prompt = """You are the AI Manager for a debt collection agency. 
Your primary job is to look at a debtor's record and decide if it is a legally and logically acceptable time to call them.
You have access to a scheduling tool. You MUST use this tool to check the debtor's timezone against weekends, business hours, and public holidays.
Do not guess the time. Use the tool.
"""
        self.agent = BaseAgent(
            llm=self.llm,
            memory=self.memory,
            system_prompt=system_prompt
        )

        # 4. Register Our Skills (Tools)
        # We pass our Python function. The agent will read its docstring to understand how to use it.
        self.agent.register_tool(check_if_good_time_to_call)
        logger.info("Hermes Manager Agent initialized with OpenRouter and Scheduling Skill.")

    def decide_if_should_call(self, debtor_data: dict) -> bool:
        """
        Asks the Hermes Agent to reason about scheduling a call for a specific debtor.
        """
        logger.info(f"Asking Hermes to evaluate call time for: {debtor_data.get('name')} in {debtor_data.get('timezone')}")
        
        # We construct a prompt passing all the relevant data to our agent
        prompt = f"""
        Please evaluate whether we should trigger a collection call right now for the following debtor:
        Name: {debtor_data.get('name')}
        Amount Owed: ${debtor_data.get('debt_amount')}
        Timezone: {debtor_data.get('timezone')}
        
        Use the check_if_good_time_to_call tool with the debtor's timezone. 
        If the tool returns True, respond with EXACTLY the word "YES".
        If the tool returns False, respond with EXACTLY the word "NO".
        """
        
        try:
            # The agent executes the prompt, deciding if it needs to call our skill automatically
            response = self.agent.run(prompt)
            decision = response.strip().upper()
            
            if "YES" in decision:
                logger.info(f"Hermes Decision: YES. It is a good time to call {debtor_data.get('name')}.")
                return True
            else:
                logger.info(f"Hermes Decision: NO. Do not call {debtor_data.get('name')} right now.")
                return False
                
        except Exception as e:
            logger.error(f"Hermes Agent encountered an error during reasoning: {e}")
            return False

# --- UNIT TESTS ---
if __name__ == "__main__":
    # Create fake debtor data matching our Airtable structure
    sample_debtor = {
        "name": "John Doe",
        "debt_amount": 500,
        "timezone": "America/New_York"
    }

    manager = DebtCollectionManager()
    
    print("\n--- Testing Hermes Manager Reasoning ---")
    should_call = manager.decide_if_should_call(sample_debtor)
    print(f"\nFinal Action: {'Trigger Voice Agent' if should_call else 'Skip Call for Now'}")
