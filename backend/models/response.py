from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class AgentResponse(BaseModel):
    chain_of_thought: Optional[str] = Field(default=None, exclude=True)
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["resume", "inference"]
    missing_data: List[str] = Field(default_factory=list)
