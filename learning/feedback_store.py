import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FeedbackStore:
    """
    Stores call outcomes to create a closed learning loop.
    """
    def __init__(self, filename="call_history.json"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)

    def add_feedback(self, name: str, outcome: str):
        record = {
            "name": name, 
            "outcome": outcome, 
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        with open(self.filename, 'r') as f:
            data = json.load(f)
            
        data.append(record)
        
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)
            
        logger.info(f"Saved learning loop feedback for {name}: {outcome}")

    def get_history(self, name: str) -> list:
        with open(self.filename, 'r') as f:
            data = json.load(f)
        return [r for r in data if r['name'] == name]