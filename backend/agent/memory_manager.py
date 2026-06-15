from typing import List, Dict

class MemoryManager:
    """
    Manages conversation history and context window limits.
    """
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns

    def get_context_window(self, history: List[Dict[str, str]]) -> str:
        """
        Returns a formatted string of the recent conversation history,
        truncated to the last `max_turns` interactions.
        """
        # A turn consists of a user message and an assistant message, so we double it
        recent_history = history[-(self.max_turns * 2):] if history else []
        
        history_str = ""
        for msg in recent_history:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n\n"
            
        return history_str.strip()

memory_manager = MemoryManager()
