from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from pydantic import BaseModel
from backend.tools.resume_parser import parse_resume
from backend.services.session_store import store

router = APIRouter()

class UploadResponse(BaseModel):
    session_id: str
    resume_summary: dict

@router.post("", response_model=UploadResponse)
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    if not file and not text:
        raise HTTPException(status_code=400, detail="Must provide either file or text")
    
    try:
        if file:
            # Check size limit MVP: 5MB
            contents = await file.read()
            if len(contents) > 5 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File too large. Max 5MB")
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
            resume_data = parse_resume(file_bytes=contents)
        else:
            resume_data = parse_resume(text=text)
            
        session_id = store.create_session(resume_data)
        
        return UploadResponse(
            session_id=session_id,
            resume_summary={
                "name": resume_data.name,
                "skills": resume_data.skills,
                "experience_count": len(resume_data.experience),
                "education_count": len(resume_data.education)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
