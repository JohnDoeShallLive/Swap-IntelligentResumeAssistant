"""
Tests for the missing data engine.
"""
import pytest
from backend.tools.missing_data_engine import check_missing_data
from backend.models.session import ResumeData

@pytest.fixture
def mock_resume_data():
    return ResumeData(
        name="John Doe",
        email="john@example.com",
        phone="555-0100",
        skills=["Python", "FastAPI", "React.js"],
        experience=[{"company": "Google", "role": "Engineer"}],
        education=[],  # Empty section
        projects=[],   # Empty section
        certifications=["AWS Certified"],
        raw_text="John Doe is a software engineer with Python and FastAPI experience."
    )

def test_tier1_never_in_resume(mock_resume_data):
    # Tests queries asking for salary, marital status etc.
    res = check_missing_data("What is the candidate's expected salary?", mock_resume_data)
    assert res is not None
    assert "expected salary" in res.missing_data or "salary" in res.missing_data
    assert res.source == "resume"
    assert res.confidence == 1.0

    res = check_missing_data("What is his GPA?", mock_resume_data)
    assert res is not None
    assert "gpa" in res.missing_data

def test_tier2_skill_existence(mock_resume_data):
    # Test for a missing skill
    res = check_missing_data("Does the candidate know Java?", mock_resume_data)
    assert res is not None
    assert "Java" in res.missing_data
    assert "not mentioned" in res.answer

    # Test for an existing skill (should return None to let LLM handle)
    res = check_missing_data("Does the candidate have experience with Python?", mock_resume_data)
    assert res is None

    res = check_missing_data("Is he proficient in React.js?", mock_resume_data)
    assert res is None

def test_tier3_section_existence(mock_resume_data):
    # Test query about an empty section
    res = check_missing_data("What degrees does he have?", mock_resume_data)
    assert res is not None
    assert "education" in res.missing_data
    assert "No education details information is mentioned" in res.answer or "education" in res.answer

    res = check_missing_data("Tell me about his projects.", mock_resume_data)
    assert res is not None
    assert "projects" in res.missing_data

    # Test query about a populated section
    res = check_missing_data("What certifications does he hold?", mock_resume_data)
    assert res is None

    res = check_missing_data("Where did he get his work experience?", mock_resume_data)
    assert res is None

def test_no_missing_data(mock_resume_data):
    res = check_missing_data("Who is the candidate?", mock_resume_data)
    assert res is None
