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
from skills.voice_trigger_skill import trigger_voice_collection_call
from learning.loop import get_learning_context

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

        import httpx
        # 1. Initialize the LLM Engine (Using OpenRouter to access free models)
        self.llm = OpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=120.0,
            max_retries=3,
            http_client=httpx.Client(
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
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
You will be provided with their past call history (Learning Loop). Use this history to decide if you need to call them again.
You have access to two tools:
1. `check_if_good_time_to_call`: MUST be used to check their timezone against holidays.
2. `trigger_voice_collection_call`: If the time is good, and you haven't recently called them without success, USE THIS TOOL to dial them.

If the dialer tool succeeds, respond with exactly 'CALLED'. If you decided to skip or it failed, write exactly 'SKIPPED'. Do not write anything else."""
        
        logger.info("Hermes Manager Agent initialized with OpenRouter and Dual Skills.")

    def process_debtor(self, debtor_data: dict) -> str:
        """
        Asks the Hermes Agent to reason about a debtor, check learning history, check time, and trigger the voice call.
        """
        name = debtor_data.get('name')
        logger.info(f"Asking Hermes to evaluate call for: {name}")
        
        learning_context = get_learning_context(name if name else "Unknown")
        
        # We construct the user prompt
        prompt = f"""
        Please evaluate whether we should trigger a collection call right now for the following debtor:
        Name: {name}
        Company Owed: {debtor_data.get('company_name', 'Unknown')}
        Amount Owed: ${debtor_data.get('debt_amount')}
        Product: {debtor_data.get('product', 'Unknown')}
        Due Date: {debtor_data.get('due_date', 'Unknown')}
        Timezone: {debtor_data.get('timezone', 'America/New_York')}
        
        {learning_context}
        """
        
        tools = [{
            "type": "function",
            "function": {
                "name": "check_if_good_time_to_call",
                "description": "Checks if it is a safe time to call (weekends, holidays, outside business hours).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone_str": {"type": "string"},
                        "country_code": {"type": "string", "description": "Default to 'US' if unknown."}
                    },
                    "required": ["timezone_str"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_voice_collection_call",
                "description": "Triggers an autonomous ElevenLabs voice agent to call a debtor. Use ONLY after checking the time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "company_name": {"type": "string"},
                        "debt_amount": {"type": "number"},
                        "product": {"type": "string"},
                        "due_date": {"type": "string"}
                    },
                    "required": ["name", "debt_amount"]
                }
            }
        }]

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages, # type: ignore
                tools=tools, # type: ignore
                tool_choice="auto",
                extra_body={"models": self.fallbacks}
            )
            
            # Keep looping as long as Hermes wants to use tools (e.g. check time -> then trigger voice)
            while getattr(response.choices[0].message, "tool_calls", None):
                message = response.choices[0].message
                messages.append(message.model_dump()) # type: ignore
                
                for tool_call in message.tool_calls: # type: ignore
                    args = json.loads(tool_call.function.arguments)
                    logger.info(f"Hermes invoked tool [{tool_call.function.name}] with: {args}")
                    
                    if tool_call.function.name == "check_if_good_time_to_call":
                        result = check_if_good_time_to_call(
                            timezone_str=args.get("timezone_str", "America/New_York"),
                            country_code=args.get("country_code", "US")
                        )
                    elif tool_call.function.name == "trigger_voice_collection_call":
                        # This triggers our ElevenLabs Voice Agent!
                        result = trigger_voice_collection_call(
                            name=args.get("name", str(name)),
                            company_name=args.get("company_name", debtor_data.get('company_name', 'Unknown')),
                            debt_amount=args.get("debt_amount", debtor_data.get('debt_amount', 0)),
                            product=args.get("product", debtor_data.get('product', 'Unknown')),
                            due_date=args.get("due_date", debtor_data.get('due_date', 'Unknown'))
                        )
                    else:
                        result = f"Error: Tool {tool_call.function.name} not found."
                        
                    # Feed the python execution result back into the memory log
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": str(result)
                    })
                
                # Ask Hermes what to do next based on the tool results
                response = self.llm.chat.completions.create(
                    model=self.model,
                    messages=messages, # type: ignore
                    tools=tools, # type: ignore
                    extra_body={"models": self.fallbacks}
                )

            # Final analysis by the LLM
            decision = getattr(response.choices[0].message, "content", "")
            decision = decision.strip().upper() if decision else "SKIPPED"
            
            if "CALLED" in decision:
                # Force the Voice Client if the LLM said "CALLED" but skipped the structured tool call
                logger.info(f"Decision is CALLED. Executing voice trigger locally.")
                trigger_voice_collection_call(
                    name=str(name),
                    company_name=debtor_data.get('company_name', 'Unknown'),
                    debt_amount=float(debtor_data.get('debt_amount', 0)),
                    product=debtor_data.get('product', 'Unknown'),
                    due_date=debtor_data.get('due_date', 'Unknown')
                )
                return "CALLED"
            
            return "SKIPPED"
                
        except Exception as e:
            logger.error(f"Hermes Agent encountered an error: {e}")
            return "SKIPPED"

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
    should_call = manager.process_debtor(sample_debtor)
    print(f"\nFinal Action: {'Trigger Voice Agent' if should_call == 'CALLED' else 'Skip Call for Now'}")
