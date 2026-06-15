"""
Hardened LLM Client.

Handles interaction with the Groq API.
- Removes hallucination-prone LLM resume parsing.
- Delimits user queries to prevent injection.
- Delegates business logic validation to response_validator.py.
"""

import os
import json
from groq import Groq
from backend.models.response import AgentResponse

class LLMClient:
    def __init__(self):
        # Fallback to empty string if not provided; handled properly in production
        api_key = os.getenv("GROQ_API_KEY", "dummy_key_for_tests")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    def generate_response(self, system_prompt: str, query: str, max_retries: int = 2) -> AgentResponse:
        """
        Generate a response from the LLM, enforcing JSON schema.
        User query is delimited with tags to help prevent prompt injection.
        """
        # Secure delimiting of user input
        delimited_query = f"<USER_QUERY>\n{query}\n</USER_QUERY>"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": delimited_query}
        ]
        
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,  # Low temperature for analytical consistency
                    max_tokens=1000,
                    response_format={"type": "json_object"}
                )
                raw_content = completion.choices[0].message.content
                
                # Validation: Pydantic will enforce the schema and confidence bounds (0.0 to 1.0)
                # Complex business logic validation (confidence clamping, grounding) is deferred
                # to the response_validator.py layer.
                response = AgentResponse.model_validate_json(raw_content)
                return response
                
            except Exception as e:
                print(f"Validation error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    print("Max retries reached. Returning fallback response.")
                    return AgentResponse(
                        chain_of_thought="Max retries reached due to validation errors.",
                        answer="Error generating response. Please check API key and rate limits, or try again.",
                        confidence=0.0,
                        source="inference",
                        missing_data=[]
                    )
                # Append the failure to messages so the LLM can self-correct format issues
                messages.append({"role": "assistant", "content": raw_content if 'raw_content' in locals() else "{}"})
                messages.append({"role": "user", "content": f"Your previous response failed JSON validation: {str(e)}. Please correct it and output valid JSON matching the exact schema."})

    # Note: extract_resume_data has been completely removed.
    # Resume parsing is now handled deterministically by backend.tools.resume_parser

llm_client = LLMClient()
