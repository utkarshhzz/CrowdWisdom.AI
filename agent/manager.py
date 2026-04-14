import os
import json
import logging
from dotenv import load_dotenv

# We are using the standard OpenAI client because it natively supports the standard 
# "tool calling" protocol that Mistral and Hermes models expect via OpenRouter.
from openai import OpenAI

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from skills.scheduling_skill import check_if_good_time_to_call

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DebtCollectionManager:
    """
    The main Hermes Agent that coordinates the debt collection process.
    """
    def __init__(self):
        load_dotenv(override=True)
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            raise ValueError("OPENROUTER_API_KEY is missing in .env file.")

        # 1. Initialize the LLM Engine (Using OpenRouter to access free models)
        self.llm = OpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # We will use the models you provided that are currently active!
        self.model = "nvidia/nemotron-3-super-120b-a12b:free"
        
        # We tell OpenRouter to automatically fall back to other available models if the first is busy
        self.fallbacks = [
            "minimax/minimax-m2.5:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "google/gemma-4-26b-a4b-it:free"
        ]

        # 3. Create the System Prompt
        self.system_prompt = """You are the AI Manager for a debt collection agency. 
Your primary job is to look at a debtor's record and decide if it is a legally and logically acceptable time to call them.
You have access to a scheduling tool. You MUST use this tool to check the debtor's timezone against weekends, business hours, and public holidays.
Do not guess the time. Use the tool. If the tool returns True, respond with exactly 'YES'. If False, 'NO'."""
        
        logger.info("Hermes Manager Agent initialized with OpenRouter and Scheduling Skill.")

    def decide_if_should_call(self, debtor_data: dict) -> bool:
        """
        Asks the Hermes Agent to reason about scheduling a call for a specific debtor via tool calling (Function Calling).
        """
        logger.info(f"Asking Hermes to evaluate call time for: {debtor_data.get('name')} in {debtor_data.get('timezone')}")
        
        # We construct the user prompt
        prompt = f"""
        Please evaluate whether we should trigger a collection call right now for the following debtor:
        Name: {debtor_data.get('name')}
        Amount Owed: ${debtor_data.get('debt_amount')}
        Timezone: {debtor_data.get('timezone')}
        """
        
        # We manually register our Python function as a JSON schema tool for the LLM
        tools = [{
            "type": "function",
            "function": {
                "name": "check_if_good_time_to_call",
                "description": "Checks if it is a legally and logically acceptable time to call a debtor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone_str": {
                            "type": "string",
                            "description": "The IANA timezone string of the debtor (e.g., 'America/New_York')."
                        },
                        "country_code": {
                            "type": "string",
                            "description": "The 2-letter country code for holiday checking (e.g., 'US')."
                        }
                    },
                    "required": ["timezone_str"]
                }
            }
        }]

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Step 1: Send the prompt and the tool to the LLM
            # We use OpenRouter's native "models" array in extra_body so it automatically falls back!
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                extra_body={
                    "models": self.fallbacks
                }
            )
            
            message = response.choices[0].message
            
            # Step 2: Did the LLM decide to call our tool?
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "check_if_good_time_to_call":
                        # The LLM extracted the timezone for us!
                        args = json.loads(tool_call.function.arguments)
                        logger.info(f"Hermes decided to use tool with arguments: {args}")
                        
                        # We execute our actual Python function right here
                        tool_result = check_if_good_time_to_call(
                            timezone_str=args.get("timezone_str"),
                            country_code=args.get("country_code", "US")
                        )
                        
                        # Step 3: Pass the result of our Python function back to Hermes
                        messages.append(message)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": str(tool_result)
                        })
                        
                        # Hermes looks at the True/False and gives us the final YES or NO
                        second_response = self.llm.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            extra_body={ "models": self.fallbacks }
                        )
                        decision = second_response.choices[0].message.content.strip().upper()
            else:
                decision = message.content.strip().upper()
                
            if "YES" in decision:
                logger.info(f"Hermes Decision: YES. It is a good time to call {debtor_data.get('name')}.")
                return True
            else:
                logger.info(f"Hermes Decision: NO. Do not call {debtor_data.get('name')} right now. (Or Hermes did not use the tool)")
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
