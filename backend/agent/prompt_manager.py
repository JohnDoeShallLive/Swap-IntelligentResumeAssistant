from backend.agent.prompts import SYSTEM_PROMPT

class PromptManager:
    """
    Manages the construction of the system prompt.
    """
    def __init__(self, base_prompt: str = SYSTEM_PROMPT):
        self.base_prompt = base_prompt

    def build_system_prompt(self, resume_data: str, history: str, tool_context: str = "") -> str:
        """
        Injects the context into the base prompt.
        Separates tool_context from resume_data to maintain resume data purity.
        """
        # Format tool context securely
        formatted_tool_context = ""
        if tool_context:
            formatted_tool_context = f"═══ TOOL CONTEXT ═══\n{tool_context}"
            
        return self.base_prompt.format(
            resume_data=resume_data,
            history=history,
            tool_context=formatted_tool_context
        )

prompt_manager = PromptManager()
