"""
Tests for the response validator.
"""
import pytest
from backend.agent.response_validator import validate_response
from backend.models.response import AgentResponse
from backend.models.session import ResumeData

@pytest.fixture
def mock_resume_data():
    return ResumeData(
        skills=["Python", "FastAPI"],
        experience=[{"company": "Google", "role": "Engineer"}],
        raw_text="Worked at Google using Python and FastAPI.",
        education=[],
        projects=[],
        certifications=[]
    )

def test_source_verification_hedging(mock_resume_data):
    response = AgentResponse(
        answer="The candidate might have experience with databases.",
        confidence=0.9,
        source="resume"
    )
    validated = validate_response(response, mock_resume_data)
    # Hedging word "might" changes source to "inference" and limits confidence to 0.75
    assert validated.source == "inference"
    assert validated.confidence <= 0.75

def test_skill_grounding_missing_skill(mock_resume_data):
    response = AgentResponse(
        answer="The candidate is skilled in Python and Kubernetes.",
        confidence=0.95,
        source="resume"
    )
    validated = validate_response(response, mock_resume_data)
    # Kubernetes is not in resume_data, so it should trigger strict rejection
    assert validated.answer == "Not mentioned in resume"
    assert validated.confidence == 1.0
    assert validated.source == "resume"
    assert len(validated.missing_data) > 0
    assert any("Kubernetes" in item for item in validated.missing_data)

def test_company_grounding_missing_company(mock_resume_data):
    response = AgentResponse(
        answer="The candidate worked at Google and Microsoft.",
        confidence=0.95,
        source="resume"
    )
    validated = validate_response(response, mock_resume_data)
    assert validated.answer == "Not mentioned in resume"
    assert validated.confidence == 1.0
    assert validated.source == "resume"
    assert len(validated.missing_data) > 0
    assert any("Microsoft" in item for item in validated.missing_data)

def test_missing_data_consistency_negative_phrases(mock_resume_data):
    response = AgentResponse(
        answer="The candidate's education is not mentioned in the resume.",
        confidence=0.9,
        source="resume"
    )
    validated = validate_response(response, mock_resume_data)
    # Negative phrases trigger missing_data, which triggers strict rejection
    assert validated.answer == "Not mentioned in resume"
    assert validated.confidence == 1.0
    assert validated.source == "resume"
    assert "Requested information not found in resume" in validated.missing_data

def test_confidence_calibration(mock_resume_data):
    # Resume source clamped up to 0.85
    resp1 = AgentResponse(answer="Yes, Python is there.", confidence=0.5, source="resume")
    val1 = validate_response(resp1, mock_resume_data)
    assert val1.confidence == 0.85

    # Inference source clamped down to 0.75
    resp2 = AgentResponse(answer="I assume they know coding.", confidence=0.99, source="inference")
    val2 = validate_response(resp2, mock_resume_data)
    assert val2.confidence == 0.75
