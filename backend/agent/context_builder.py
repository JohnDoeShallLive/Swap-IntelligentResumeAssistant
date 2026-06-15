from backend.models.session import SessionState
from typing import List, Dict

from backend.agent.memory_manager import memory_manager

def build_context(session: SessionState) -> Dict[str, str]:
    """
    Builds the context for the prompt from the session state.
    """
    history_str = memory_manager.get_context_window(session.conversation_history)
        
    resume_data_str = session.resume_data.model_dump_json(indent=2)
    
    return {
        "resume_data": resume_data_str,
        "history": history_str
    }
