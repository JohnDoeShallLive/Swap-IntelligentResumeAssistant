from pydantic import BaseModel, Field
from typing import List, Literal

class AgentResponse(BaseModel):
    chain_of_thought: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["resume", "inference"]
    missing_data: List[str] = Field(default_factory=list)
