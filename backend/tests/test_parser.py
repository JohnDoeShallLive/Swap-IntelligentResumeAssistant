from backend.tools.resume_parser import parse_resume_text

def test_parse_resume_text_name():
    text = "John Doe\njohn@example.com\n555-123-4567\nSkills: Python, AWS"
    data = parse_resume_text(text)
    assert data.name == "John Doe"
    assert data.email == "john@example.com"
    assert data.phone == "555-123-4567"
    assert "Python" in data.skills
