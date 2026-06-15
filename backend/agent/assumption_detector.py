import re
from typing import Optional
from backend.models.response import AgentResponse

def detect_assumption(query: str) -> Optional[AgentResponse]:
    """
    Detect queries attempting to inject unsupported facts/assumptions.
    """
    if not query or not query.strip():
        return None

    query_lower = " ".join(query.lower().split())

    # Detect assumption keywords
    assumption_keywords = [
        r"assume", r"pretend", r"suppose", r"imagine", 
        r"forgot to mention", r"let'?s say", r"consider that", 
        r"treat as if", r"ignore the resume", r"invent", r"fabricate"
    ]
    
    keyword_pattern = r"(?i)\b(?:{})\b".format("|".join(assumption_keywords))
    
    if re.search(keyword_pattern, query_lower):
        # Extract the assumed fact
        extract_patterns = [
            r"(?i)(?:candidate|applicant|they|he|she)\s+(?:knows?|has|had|have|worked\s+with|is\s+proficient\s+in|is\s+skilled\s+in)\s+(.+)",
            r"(?i)(?:candidate|applicant|they|he|she)\s+(?:is|are)\s+(?:a|an)\s+(.+)",
            r"(?i)(?:invent|fabricate|create)\s+(.+)"
        ]
        
        extracted_fact = "unsupported assumption"
        for p in extract_patterns:
            match = re.search(p, query)
            if match:
                extracted_fact = match.group(1).strip().strip(".!?,")
                break
                
        if extracted_fact.lower().startswith("that "):
            extracted_fact = extracted_fact[5:]
            
        return AgentResponse(
            answer="Not mentioned in resume",
            confidence=1.0,
            source="resume",
            missing_data=[extracted_fact]
        )
        
    return None
