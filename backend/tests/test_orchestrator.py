from unittest.mock import patch, MagicMock
from backend.agent.orchestrator import process_query
from backend.models.session import SessionState, ResumeData
from backend.models.response import AgentResponse

@patch("backend.agent.orchestrator.classify_intent")
@patch("backend.agent.orchestrator.llm_client.generate_response")
def test_process_query_direct_qa(mock_generate, mock_classify):
    mock_classify.return_value = "direct_qa"
    
    mock_response = AgentResponse(
        answer="Mock answer",
        confidence=0.9,
        source="resume",
        missing_data=[]
    )
    mock_generate.return_value = mock_response
    
    session = SessionState(
        session_id="123",
        resume_data=ResumeData(raw_text="Test resume")
    )
    
    response = process_query(session, "What is the name?")
    
    mock_classify.assert_called_with("What is the name?")
    assert mock_generate.called
    assert len(session.conversation_history) == 2

@patch("backend.agent.orchestrator.classify_intent")
@patch("backend.agent.orchestrator.extract_keywords")
@patch("backend.agent.orchestrator.llm_client.generate_response")
def test_process_query_keyword_tool(mock_generate, mock_extract, mock_classify):
    mock_classify.return_value = "keyword"
    mock_extract.return_value = {"keywords": ["python", "aws"]}
    
    mock_response = AgentResponse(
        answer="Mock answer",
        confidence=0.9,
        source="resume",
        missing_data=[]
    )
    mock_generate.return_value = mock_response
    
    session = SessionState(
        session_id="123",
        resume_data=ResumeData(raw_text="Test resume")
    )
    
    response = process_query(session, "Extract keywords")
    
    assert mock_classify.called
    assert mock_extract.called
    assert mock_generate.called
