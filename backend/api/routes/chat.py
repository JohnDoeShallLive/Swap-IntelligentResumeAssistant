from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.session_store import store
from backend.agent.orchestrator import process_query
from backend.models.response import AgentResponse

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    query: str

@router.post("", response_model=AgentResponse)
async def chat(request: ChatRequest):
    session = store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    try:
        response = process_query(session, request.query)
        store.update_session(session)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
