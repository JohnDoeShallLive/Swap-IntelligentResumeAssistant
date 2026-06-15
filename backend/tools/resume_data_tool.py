"""
Resume Data Tool — Deterministic factual query answering.

Answers factual questions about resume data by directly looking up
extracted fields. No LLM is involved. This ensures zero hallucination
for factual queries about skills, experience, education, etc.
"""

from typing import Optional, Dict, Any, List
from backend.models.session import ResumeData
from backend.models.response import AgentResponse
from backend.tools.resume_parser import calculate_total_experience


# ─── Skill synonym map for fuzzy matching ──────────────────────────────────────
SKILL_ALIASES = {
    "js": "javascript", "javascript": "javascript",
    "ts": "typescript", "typescript": "typescript",
    "py": "python", "python": "python",
    "k8s": "kubernetes", "kubernetes": "kubernetes",
    "postgres": "postgresql", "postgresql": "postgresql",
    "mongo": "mongodb", "mongodb": "mongodb",
    "react.js": "react", "reactjs": "react", "react": "react",
    "node.js": "node.js", "nodejs": "node.js",
    "vue.js": "vue.js", "vuejs": "vue.js",
    "next.js": "next.js", "nextjs": "next.js",
    "express.js": "express.js", "expressjs": "express.js",
    "c++": "c++", "cpp": "c++",
    "c#": "c#", "csharp": "c#",
    "aws": "aws", "gcp": "gcp", "azure": "azure",
    "ci/cd": "ci/cd", "cicd": "ci/cd",
    "docker": "docker", "ansible": "ansible",
    "terraform": "terraform", "jenkins": "jenkins",
    "git": "git", "github": "github",
    "linux": "linux", "bash": "bash",
    "sql": "sql", "mysql": "mysql",
    "nginx": "nginx", "redis": "redis",
}


def _normalize_skill(skill: str) -> str:
    """Normalize a skill name for comparison."""
    return SKILL_ALIASES.get(skill.lower().strip(), skill.lower().strip())


def _skill_exists(skill_query: str, resume_skills: List[str]) -> bool:
    """Check if a skill exists in the resume skills list (case-insensitive with aliases)."""
    normalized_query = _normalize_skill(skill_query)
    for skill in resume_skills:
        if _normalize_skill(skill) == normalized_query:
            return True
    return False


def get_skills(resume_data: ResumeData, query: str = "") -> AgentResponse:
    """Return all explicitly listed skills from the resume.
    If the query asks to list/extract technologies, return exact extraction.
    """
    if not resume_data.skills:
        return AgentResponse(
            answer="No skills are explicitly listed in the resume.",
            confidence=0.9,
            source="resume",
            missing_data=["skills"],
        )

    skills_list = ", ".join(resume_data.skills)
    
    # Check if raw extraction is requested
    if re.search(r"(?i)\b(?:list|show|extract)\s+all\s+(?:technolog(?:y|ies)|skills?)", query):
        answer = json.dumps(resume_data.skills)
    else:
        skills_list = ", ".join(resume_data.skills)
        answer = f"The candidate lists the following skills: {skills_list}"
        
    return AgentResponse(
        answer=answer,
        confidence=1.0,
        source="resume",
        missing_data=[],
    )


def has_skill(resume_data: ResumeData, skill_name: str) -> AgentResponse:
    """Check if a specific skill is explicitly listed in the resume."""
    if _skill_exists(skill_name, resume_data.skills):
        return AgentResponse(
            answer=f"Yes, {skill_name} is explicitly listed in the candidate's skills.",
            confidence=1.0,
            source="resume",
            missing_data=[],
        )
    else:
        return AgentResponse(
            answer=f"'{skill_name}' is not mentioned in the resume.",
            confidence=1.0,
            source="resume",
            missing_data=[skill_name],
        )


def get_experience(resume_data: ResumeData, query: str = "") -> AgentResponse:
    """Return all work experience entries or specifically filtered data."""
    if not resume_data.experience:
        return AgentResponse(
            answer="No work experience entries were found in the resume.",
            confidence=0.9,
            source="resume",
            missing_data=["experience"],
        )

    query_lower = query.lower()
    
    # Specific sub-query: Number of internships
    if "intern" in query_lower and ("number" in query_lower or "how many" in query_lower):
        intern_count = sum(1 for exp in resume_data.experience if "intern" in exp.get("role", "").lower())
        return AgentResponse(
            answer=f"The candidate has {intern_count} internship(s).",
            confidence=1.0,
            source="resume",
            missing_data=[]
        )
        
    # Specific sub-query: Company names
    if "compan" in query_lower:
        companies = [exp.get("company", "Unknown") for exp in resume_data.experience]
        return AgentResponse(
            answer=f"Companies: {', '.join(companies)}",
            confidence=1.0,
            source="resume",
            missing_data=[]
        )
        
    # Specific sub-query: Dates
    if "date" in query_lower or "timeline" in query_lower:
        dates = [f"{exp.get('company', 'Unknown')}: {exp.get('start_date', '?')} – {exp.get('end_date', '?')}" for exp in resume_data.experience]
        return AgentResponse(
            answer=f"Experience dates:\n" + "\n".join(dates),
            confidence=1.0,
            source="resume",
            missing_data=[]
        )

    entries = []
    for exp in resume_data.experience:
        role = exp.get("role", "Unknown Role")
        company = exp.get("company", "Unknown Company")
        start = exp.get("start_date", "?")
        end = exp.get("end_date", "?")
        duration = exp.get("duration", {})
        dur_str = duration.get("formatted", "") if isinstance(duration, dict) else ""
        entry = f"• {role} at {company} ({start} – {end})"
        if dur_str:
            entry += f" — {dur_str}"
        entries.append(entry)

    answer = f"The candidate has {len(resume_data.experience)} experience entries:\n" + "\n".join(entries)
    return AgentResponse(
        answer=answer,
        confidence=1.0,
        source="resume",
        missing_data=[],
    )


def get_total_experience(resume_data: ResumeData) -> AgentResponse:
    """
    Calculate and return total work experience duration.
    Uses DETERMINISTIC date math — no LLM calculation.
    """
    if not resume_data.experience:
        return AgentResponse(
            answer="No work experience entries were found in the resume to calculate total duration.",
            confidence=0.9,
            source="resume",
            missing_data=["experience"],
        )

    total = calculate_total_experience(resume_data.experience)

    # Build detailed breakdown
    breakdown_lines = []
    for entry in total.get("breakdown", []):
        breakdown_lines.append(
            f"  • {entry['role']} at {entry['company']}: {entry['months']} month(s)"
        )

    breakdown = "\n".join(breakdown_lines) if breakdown_lines else "No detailed breakdown available."

    answer = (
        f"Total work experience: {total['formatted']}\n\n"
        f"Breakdown:\n{breakdown}"
    )

    return AgentResponse(
        answer=answer,
        confidence=1.0,
        source="resume",
        missing_data=[],
    )


def get_education(resume_data: ResumeData) -> AgentResponse:
    """Return all education entries from the resume."""
    if not resume_data.education:
        return AgentResponse(
            answer="No education information was found in the resume.",
            confidence=0.9,
            source="resume",
            missing_data=["education"],
        )

    entries = []
    for edu in resume_data.education:
        parts = []
        if edu.get("degree"):
            parts.append(edu["degree"])
        if edu.get("field"):
            parts.append(f"in {edu['field']}")
        if edu.get("institution"):
            parts.append(f"from {edu['institution']}")
        if edu.get("year"):
            parts.append(f"({edu['year']})")
        if edu.get("gpa"):
            parts.append(f"GPA: {edu['gpa']}")
        if edu.get("percentage"):
            parts.append(f"Percentage: {edu['percentage']}")
        entries.append("• " + " ".join(parts))

    answer = f"Education:\n" + "\n".join(entries)
    return AgentResponse(
        answer=answer,
        confidence=1.0,
        source="resume",
        missing_data=[],
    )


def get_certifications(resume_data: ResumeData, query: str = "") -> AgentResponse:
    """Return certifications from the resume."""
    if not resume_data.certifications:
        return AgentResponse(
            answer="No certifications are listed in the resume.",
            confidence=0.9,
            source="resume",
            missing_data=["certifications"],
        )

    if re.search(r"(?i)\b(?:list|show|extract)\s+all\s+certifications?", query):
        answer = json.dumps(resume_data.certifications)
    else:
        certs = "\n".join([f"• {c}" for c in resume_data.certifications])
        answer = f"The candidate has the following certifications:\n{certs}"

    return AgentResponse(
        answer=answer,
        confidence=1.0,
        source="resume",
        missing_data=[],
    )


def get_contact_info(resume_data: ResumeData) -> AgentResponse:
    """Return contact information from the resume."""
    info_parts = []
    missing = []

    if resume_data.name:
        info_parts.append(f"Name: {resume_data.name}")
    else:
        missing.append("name")

    if resume_data.email:
        info_parts.append(f"Email: {resume_data.email}")
    else:
        missing.append("email")

    if resume_data.phone:
        info_parts.append(f"Phone: {resume_data.phone}")
    else:
        missing.append("phone")

    if not info_parts:
        return AgentResponse(
            answer="No contact information was found in the resume.",
            confidence=0.0,
            source="resume",
            missing_data=missing,
        )

    answer = "Contact Information:\n" + "\n".join(info_parts)
    if missing:
        answer += f"\n\nNot found: {', '.join(missing)}"

    return AgentResponse(
        answer=answer,
        confidence=1.0,
        source="resume",
        missing_data=missing,
    )


def get_projects(resume_data: ResumeData, query: str = "") -> AgentResponse:
    """Return all projects from the resume."""
    if not resume_data.projects:
        return AgentResponse(
            answer="No projects are mentioned in the resume.",
            confidence=0.9,
            source="resume",
            missing_data=["projects"],
        )

    if re.search(r"(?i)\b(?:list|show|extract)\s+all\s+projects?", query):
        answer = json.dumps(resume_data.projects)
    else:
        entries = []
        for proj in resume_data.projects:
            name = proj.get("name", "Unnamed Project")
            tech = proj.get("tech_stack", [])
            desc = proj.get("description", "")
            entry = f"• {name}"
            if tech:
                entry += f" ({', '.join(tech)})"
            if desc:
                entry += f"\n  {desc[:200]}"
            entries.append(entry)
        answer = f"Projects ({len(resume_data.projects)} found):\n" + "\n".join(entries)

    return AgentResponse(
        answer=answer,
        confidence=1.0,
        source="resume",
        missing_data=[],
    )


def answer_factual_query(intent: str, query: str, resume_data: ResumeData) -> AgentResponse:
    """
    Route a factual query to the appropriate deterministic lookup function.
    
    Args:
        intent: The classified intent (e.g., "factual_skills", "factual_experience").
        query: The original user query.
        resume_data: The extracted resume data.
    
    Returns:
        AgentResponse with deterministic, grounded answer.
    """
    # Extract specific skill name if query asks about a specific skill
    if intent == "factual_skills":
        # Check if asking about a specific skill
        specific_skill = _extract_skill_from_query(query)
        if specific_skill:
            return has_skill(resume_data, specific_skill)
        return get_skills(resume_data, query)

    elif intent == "factual_experience":
        # Check if asking about total/duration
        if any(kw in query.lower() for kw in ["total", "duration", "how long", "years of", "how many years", "how much experience"]):
            return get_total_experience(resume_data)
        return get_experience(resume_data, query)

    elif intent == "factual_education":
        return get_education(resume_data)

    elif intent == "factual_certifications":
        return get_certifications(resume_data, query)

    elif intent == "factual_contact":
        return get_contact_info(resume_data)

    elif intent == "factual_projects":
        return get_projects(resume_data, query)

    # Fallback
    return AgentResponse(
        answer="I could not determine the specific information requested. Please rephrase your question.",
        confidence=0.5,
        source="inference",
        missing_data=[],
    )


def _extract_skill_from_query(query: str) -> Optional[str]:
    """
    Extract a specific skill/technology name from a query like
    'Does the candidate know Docker?' or 'Do they have Python experience?'
    """
    query_lower = query.lower()

    # Patterns for specific skill queries
    patterns = [
        r"(?:does|do)\s+(?:the\s+)?(?:candidate|they|he|she)\s+(?:know|have|use|work\s+with)\s+(.+?)[\?\.]?\s*$",
        r"(?:experience|proficient|skilled|familiar)\s+(?:with|in)\s+(.+?)[\?\.]?\s*$",
        r"(?:know|have)\s+(.+?)[\?\.]?\s*$",
        r"(?:is|are)\s+(?:the\s+)?(?:candidate|they|he|she)\s+(?:proficient|skilled|experienced)\s+(?:in|with)\s+(.+?)[\?\.]?\s*$",
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            skill = match.group(1).strip().rstrip("?. ")
            # Remove articles and common words
            skill = re.sub(r'^(?:a|an|the|any)\s+', '', skill)
            if skill:
                return skill

    return None


# Required for _extract_skill_from_query
import json
import re
