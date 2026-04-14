from learning.feedback_store import FeedbackStore

def get_learning_context(name: str) -> str:
    """
    Retrieves the call history for a specific debtor to feed back to Hermes.
    This creates the closed learning loop so Hermes can adapt.
    """
    store = FeedbackStore()
    history = store.get_history(name)
    
    if not history:
        return "No previous call history for this debtor."
    
    context = "Previous call history for this debtor:\n"
    for record in history:
        context += f"- At {record['timestamp']}, outcome was: {record['outcome']}\n"
    
    return context