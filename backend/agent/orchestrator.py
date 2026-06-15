"""
Hardened Orchestrator — Central routing logic.

Implements the deterministic-first routing pipeline:
1. Injection Detection
2. Missing Data Check
3. Intent Classification
4. Deterministic Factual Routing OR LLM Evaluation
5. Post-Response Validation (if LLM used)
"""

import json
from backend.models.session import SessionState
from backend.models.response import AgentResponse
from backend.agent.prompt_manager import prompt_manager
from backend.agent.context_builder import build_context
from backend.agent.intent_classifier import classify_intent
from backend.services.llm_client import llm_client
from backend.tools.skill_matcher import match_skills
from backend.tools.keyword_extractor import extract_keywords

# New hardened components
from backend.agent.injection_detector import is_injection, get_rejection_agent_response
from backend.agent.assumption_detector import detect_assumption
from backend.tools.missing_data_engine import check_missing_data
from backend.tools.resume_data_tool import answer_factual_query
from backend.agent.response_validator import validate_response

def process_query(session: SessionState, query: str, jd_text: str = None) -> AgentResponse:
    """
    Process a user query through the hardened pipeline.
    """
    # Step 1: Injection Detection (Security Layer)
    if is_injection(query):
        response = get_rejection_agent_response()
        _update_history(session, query, response)
        return response

    # Step 2: Assumption Detection Layer
    assumption_response = detect_assumption(query)
    if assumption_response:
        _update_history(session, query, assumption_response)
        return assumption_response

    # Step 3: Missing Data Engine (Fast Fail Layer)
    missing_response = check_missing_data(query, session.resume_data)
    if missing_response:
        _update_history(session, query, missing_response)
        return missing_response

    # Step 4: Intent Classification (Rule-based)
    intent = classify_intent(query)
    
    # Step 5: Routing
    # Route A: Factual queries (Deterministic Tool, NO LLM)
    if intent.startswith("factual_"):
        response = answer_factual_query(intent, query, session.resume_data)
        _update_history(session, query, response)
        return response
        
    # Route B: Tools that output context for LLM evaluation
    tool_context = ""
    if intent == "skill_match" and jd_text:
        match_result = match_skills(session.resume_data.skills, jd_text)
        tool_context = f"\nSkill Match Result:\n{json.dumps(match_result, indent=2)}"
    elif intent == "keyword":
        keywords = extract_keywords(session.resume_data.raw_text)
        tool_context = f"\nExtracted Keywords:\n{json.dumps(keywords, indent=2)}"
        
    # Route C: LLM Evaluation (for intent == "evaluation", "summary", or tools)
    ctx = build_context(session)
    system_prompt = prompt_manager.build_system_prompt(
        resume_data=ctx["resume_data"],
        history=ctx["history"],
        tool_context=tool_context
    )
    
    # 4.1 LLM Call
    raw_response = llm_client.generate_response(system_prompt, query)
    
    # Step 5: Post-Response Validation (Hallucination Defense)
    validated_response = validate_response(raw_response, session.resume_data)
    
    # Step 6: Update history and return
    _update_history(session, query, validated_response)
    
    return validated_response

def _update_history(session: SessionState, query: str, response: AgentResponse) -> None:
    """Helper to update conversation history safely."""
    session.conversation_history.append({"role": "user", "content": query})
    session.conversation_history.append({"role": "assistant", "content": response.model_dump_json()})
