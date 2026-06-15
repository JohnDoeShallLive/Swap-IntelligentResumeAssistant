"""
Missing Data Engine
===================

Pre-LLM interception layer that detects queries about resume fields
that are known to be absent, returning deterministic responses without
consuming LLM tokens.

Three detection tiers:

1. **NEVER_IN_RESUME** — Personal / sensitive fields that a professional
   resume virtually never contains (salary, GPA, marital status, etc.).
2. **Skill existence** — Checks whether a queried technology or skill
   appears anywhere in ``resume_data.skills``.
3. **Section existence** — Verifies that queried resume sections
   (certifications, education, experience, projects) are non-empty.

Usage::

    from backend.tools.missing_data_engine import check_missing_data

    result = check_missing_data(user_query, resume_data)
    if result is not None:
        return result  # short-circuit, no LLM call needed
"""

import re
from typing import Dict, FrozenSet, List, Optional, Pattern, Set, Tuple

from backend.models.response import AgentResponse
from backend.models.session import ResumeData

# ---------------------------------------------------------------------------
# Tier 1 — Fields that are never (or almost never) in a resume
# ---------------------------------------------------------------------------

#: Canonical labels mapped to keyword sets used for query matching.
#: Grouped logically so maintainers can easily add / remove terms.
_NEVER_IN_RESUME_GROUPS: Dict[str, FrozenSet[str]] = {
    "salary_compensation": frozenset({
        "salary", "compensation", "pay", "ctc", "cost to company",
        "expected salary", "current salary", "pay scale", "remuneration",
        "stipend", "wage", "wages", "package", "lpa", "per annum",
    }),
    "academic_scores": frozenset({
        "gpa", "cgpa", "percentage", "marks", "grade point",
        "grade point average", "academic score", "test score",
    }),
    "personal_sensitive": frozenset({
        "marital status", "married", "single", "divorced",
        "age", "date of birth", "dob", "birthday",
        "passport", "passport number", "visa", "visa status",
        "nationality", "religion", "caste", "gender", "sex",
        "blood group", "blood type",
    }),
    "contact_private": frozenset({
        "full address", "home address", "residential address",
        "permanent address", "mailing address", "zip code", "pin code",
        "postal code",
    }),
    "miscellaneous": frozenset({
        "references", "hobbies", "interests", "notice period",
        "languages spoken", "mother tongue", "father's name",
        "father name", "mother's name", "mother name",
    }),
}

#: Flattened set of all never-in-resume keywords for O(1) lookup.
_NEVER_IN_RESUME_KEYWORDS: FrozenSet[str] = frozenset().union(
    *_NEVER_IN_RESUME_GROUPS.values()
)

#: Human-readable label for the category a keyword belongs to
#: (used in the ``missing_data`` list for richer feedback).
_KEYWORD_TO_CATEGORY: Dict[str, str] = {
    kw: category
    for category, keywords in _NEVER_IN_RESUME_GROUPS.items()
    for kw in keywords
}

# ---------------------------------------------------------------------------
# Tier 2 — Skill existence detection patterns
# ---------------------------------------------------------------------------

#: Regex patterns that capture a technology / skill name from the query.
#: Each pattern must expose a named group ``skill``.
_SKILL_QUERY_PATTERNS: List[Pattern[str]] = [
    re.compile(
        r"\b(?:does|do)\s+(?:the\s+)?(?:candidate|applicant|person|they?|he|she)\s+"
        r"(?:know|use|have\s+experience\s+(?:with|in)|work\s+with)\s+"
        r"(?P<skill>.+?)(?:\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:experience|expertise|proficiency|knowledge|familiarity)"
        r"\s+(?:with|in|of|on)\s+(?P<skill>.+?)(?:\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:knows?|skilled\s+in|proficient\s+in|familiar\s+with|trained\s+in)"
        r"\s+(?P<skill>.+?)(?:\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:has|have)\s+(?:the\s+)?(?:candidate|applicant|person|they?|he|she)\s+"
        r"(?:used|worked\s+with|learned|studied)\s+"
        r"(?P<skill>.+?)(?:\?|$)",
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Tier 3 — Section existence mapping
# ---------------------------------------------------------------------------

#: Maps query keywords to the corresponding ``ResumeData`` attribute name.
_SECTION_KEYWORDS: Dict[str, str] = {
    "certification": "certifications",
    "certifications": "certifications",
    "certified": "certifications",
    "certificate": "certifications",
    "certificates": "certifications",
    "education": "education",
    "degree": "education",
    "degrees": "education",
    "university": "education",
    "college": "education",
    "academic": "education",
    "qualification": "education",
    "qualifications": "education",
    "school": "education",
    "experience": "experience",
    "work experience": "experience",
    "work history": "experience",
    "employment": "experience",
    "employment history": "experience",
    "job": "experience",
    "jobs": "experience",
    "career": "experience",
    "project": "projects",
    "projects": "projects",
    "portfolio": "projects",
}

#: Friendly section labels used in user-facing responses.
_SECTION_DISPLAY_NAMES: Dict[str, str] = {
    "certifications": "certifications",
    "education": "education details",
    "experience": "work experience",
    "projects": "projects",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Collapse whitespace and lowercase for matching."""
    return " ".join(text.lower().split())


def _check_never_in_resume(query_lower: str) -> Optional[AgentResponse]:
    """Tier 1: Return a response if the query targets a never-in-resume field.

    Iterates through keywords longest-first to prefer more specific
    matches (e.g. "expected salary" before "salary").

    Args:
        query_lower: Lowercased, whitespace-normalised query string.

    Returns:
        An ``AgentResponse`` if a never-in-resume keyword is detected,
        otherwise ``None``.
    """
    # Sort keywords longest-first so multi-word phrases match first
    for keyword in sorted(_NEVER_IN_RESUME_KEYWORDS, key=len, reverse=True):
        if keyword in query_lower:
            category = _KEYWORD_TO_CATEGORY[keyword]
            return AgentResponse(
                answer=(
                    f"This information ({keyword}) is not typically included "
                    f"in a professional resume and is not mentioned in the "
                    f"uploaded document."
                ),
                confidence=1.0,
                source="resume",
                missing_data=[keyword],
            )
    return None


def _extract_queried_skill(query: str) -> Optional[str]:
    """Attempt to extract a skill / technology name from the query.

    Args:
        query: Original (non-normalised) query string.

    Returns:
        The extracted skill string (stripped, title-cased), or ``None``
        if no skill-query pattern matched.
    """
    for pattern in _SKILL_QUERY_PATTERNS:
        match = pattern.search(query)
        if match:
            skill = match.group("skill").strip().strip("?.,;:!")
            if skill:
                return skill
    return None


def _skill_exists_in_resume(skill: str, skills: List[str]) -> bool:
    """Case-insensitive check for a skill in the resume's skill list.

    Handles partial matching: if the queried skill is a substring of
    any listed skill (or vice versa), it counts as a match. This avoids
    false negatives like "React" vs "React.js" or "AWS" vs "Amazon Web
    Services (AWS)".

    Args:
        skill: The skill to search for.
        skills: The list of skills from ``ResumeData``.

    Returns:
        ``True`` if the skill is found, ``False`` otherwise.
    """
    skill_lower: str = skill.lower().strip()
    for resume_skill in skills:
        resume_skill_lower: str = resume_skill.lower().strip()
        if (
            skill_lower == resume_skill_lower
            or skill_lower in resume_skill_lower
            or resume_skill_lower in skill_lower
        ):
            return True
    return False


def _check_skill_existence(
    query: str, resume_data: ResumeData
) -> Optional[AgentResponse]:
    """Tier 2: Return a response if the query asks about a missing skill.

    Args:
        query: Original query string.
        resume_data: Parsed resume data.

    Returns:
        An ``AgentResponse`` indicating the skill is not mentioned, or
        ``None`` if the skill exists (let the LLM elaborate) or no
        skill-query pattern was detected.
    """
    skill = _extract_queried_skill(query)
    if skill is None:
        return None

    if _skill_exists_in_resume(skill, resume_data.skills):
        # Skill IS present — let the LLM generate a richer answer
        return None

    return AgentResponse(
        answer=(
            f"The skill '{skill}' is not mentioned in the candidate's resume."
        ),
        confidence=1.0,
        source="resume",
        missing_data=[skill],
    )


def _check_section_existence(
    query_lower: str, resume_data: ResumeData
) -> Optional[AgentResponse]:
    """Tier 3: Return a response if the queried section is empty.

    Args:
        query_lower: Lowercased, whitespace-normalised query string.
        resume_data: Parsed resume data.

    Returns:
        An ``AgentResponse`` if the section is empty, ``None`` if the
        section has data (let the LLM answer) or no section keyword was
        matched.
    """
    # Check multi-word keywords first (longest match wins)
    for keyword in sorted(_SECTION_KEYWORDS, key=len, reverse=True):
        if keyword in query_lower:
            attr_name: str = _SECTION_KEYWORDS[keyword]
            section_data = getattr(resume_data, attr_name, None)

            # If the section has data, let the LLM handle it
            if section_data:
                return None

            display_name = _SECTION_DISPLAY_NAMES.get(attr_name, attr_name)
            return AgentResponse(
                answer=(
                    f"No {display_name} information is mentioned in the "
                    f"candidate's resume."
                ),
                confidence=1.0,
                source="resume",
                missing_data=[attr_name],
            )

    return None


def _check_role_existence(query: str, resume_data: ResumeData) -> Optional[AgentResponse]:
    """Tier 4: Check if a queried role/title exists in experience."""
    pattern = re.compile(r"(?:is|are)\s+(?:the\s+)?(?:candidate|they|he|she)\s+(?:a|an|currently\s+a|currently\s+an)?\s+(?P<role>[A-Za-z\s]+)(?:\?|$)", re.IGNORECASE)
    match = pattern.search(query)
    if not match:
        # Also check simple "employed as a X" or "working as a X"
        pattern2 = re.compile(r"(?:employed|working)\s+(?:as\s+(?:a|an))?\s+(?P<role>[A-Za-z\s]+)(?:\?|$)", re.IGNORECASE)
        match = pattern2.search(query)
        
    if not match:
        # Check for employment status query
        if re.search(r"(?i)\b(?:currently\s+)?employed\b\?", query):
            return AgentResponse(
                answer="Employment status is not explicitly mentioned in the resume.",
                confidence=1.0,
                source="resume",
                missing_data=["employment status"]
            )
        return None
        
    queried_role = match.group("role").strip().strip("?.,;:!")
    if not queried_role or len(queried_role) < 3:
        return None
        
    # Check if the role is present in any experience entry
    queried_role_lower = queried_role.lower()
    for exp in resume_data.experience:
        exp_role = exp.get("role", "").lower()
        if queried_role_lower in exp_role or exp_role in queried_role_lower:
            return None # Role exists, let LLM answer
            
    return AgentResponse(
        answer=f"The role '{queried_role}' is not mentioned in the candidate's resume.",
        confidence=1.0,
        source="resume",
        missing_data=[queried_role]
    )

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_missing_data(
    query: str, resume_data: ResumeData
) -> Optional[AgentResponse]:
    """Check whether a query targets data that is known to be absent.

    Runs through three detection tiers in order of priority:

    1. **Never-in-resume fields** — salary, GPA, marital status, etc.
       These are personal / sensitive fields that professional resumes
       virtually never contain.
    2. **Skill existence** — If the query asks whether the candidate
       knows a specific technology, a direct lookup on
       ``resume_data.skills`` is performed.
    3. **Section existence** — If the query asks about certifications,
       education, experience, or projects and the corresponding section
       is empty, a deterministic response is returned.

    If any tier produces a match, the corresponding
    :class:`~backend.models.response.AgentResponse` is returned
    immediately, short-circuiting the LLM call. If no tier matches,
    ``None`` is returned and the query should proceed to the LLM.

    Args:
        query: The raw user query string.
        resume_data: The parsed resume data for the current session.

    Returns:
        An :class:`~backend.models.response.AgentResponse` if the
        queried data is known to be absent, or ``None`` if the query
        should be forwarded to the LLM.

    Examples:
        >>> from backend.models.session import ResumeData
        >>> data = ResumeData(raw_text="...", skills=["Python", "FastAPI"])
        >>> result = check_missing_data("What is the candidate's salary?", data)
        >>> result.answer
        "This information (salary) is not typically included in a ..."
        >>> check_missing_data("What are the candidate's skills?", data) is None
        True
    """
    if not query or not query.strip():
        return None

    query_lower: str = _normalize(query)

    # Tier 1: Never-in-resume fields
    result = _check_never_in_resume(query_lower)
    if result is not None:
        return result

    # Tier 2: Skill existence check
    result = _check_skill_existence(query, resume_data)
    if result is not None:
        return result

    # Tier 3: Section existence check
    result = _check_section_existence(query_lower, resume_data)
    if result is not None:
        return result

    # Tier 4: Role/Title existence check
    result = _check_role_existence(query, resume_data)
    if result is not None:
        return result

    # No missing-data match — let the LLM handle the query
    return None
