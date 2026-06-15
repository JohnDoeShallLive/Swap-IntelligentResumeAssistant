from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.session_store import store
from backend.agent.orchestrator import process_query
from backend.models.response import AgentResponse

router = APIRouter()

class SkillMatchRequest(BaseModel):
    session_id: str
    job_description: str

@router.post("", response_model=AgentResponse)
async def skill_match(request: SkillMatchRequest):
    session = store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    try:
        # We craft a query to trigger the skill match logic in the orchestrator
        query = "Evaluate the candidate's skill match against this job description."
        response = process_query(session, query, jd_text=request.job_description)
        store.update_session(session)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
