"""
Rule-Based Intent Classifier — No LLM dependency.

Classifies user queries into intent categories using keyword pattern matching.
This replaces the previous LLM-based classifier to eliminate latency,
API cost, and failure modes.
"""

import re
from typing import Literal

# ─── Intent type definition ────────────────────────────────────────────────────
IntentType = Literal[
    "factual_skills",
    "factual_experience", 
    "factual_education",
    "factual_certifications",
    "factual_contact",
    "factual_projects",
    "skill_match",
    "keyword",
    "evaluation",
    "summary",
    "direct_qa",
]

# ─── Pattern definitions ──────────────────────────────────────────────────────

FACTUAL_SKILLS_PATTERNS = [
    r"(?i)\bskills?\b",
    r"(?i)\btechnolog(?:y|ies)\b",
    r"(?i)\btech\s*stack\b",
    r"(?i)\bprogramming\s*language",
    r"(?i)\bproficien(?:t|cy)\b",
    r"(?i)\bfamiliar\s+with\b",
    r"(?i)\bknow(?:s|ledge)?\b.*\b(?:python|java|react|docker|aws|kubernetes|sql|linux|html|css|javascript|typescript|angular|vue|node|go|rust|ruby|c\+\+|c#|terraform|ansible|jenkins|git|bash|mongodb|postgresql|mysql|redis|kafka|nginx|express|next|flask|django|spring|graphql|rest)\b",
    r"(?i)\bexperience\s+with\b.*\b(?:python|java|react|docker|aws|kubernetes|sql|linux|html|css|javascript|typescript|angular|vue|node|go|rust|ruby)\b",
    r"(?i)\bdo(?:es)?\s+(?:the\s+)?(?:candidate|they|he|she)\s+(?:know|have|use)\b",
    r"(?i)\bwhat\s+(?:tools?|framework|language|tech)",
    r"(?i)\b(?:list|show|extract)\s+all\s+(?:technolog(?:y|ies)|skills?)",
]

FACTUAL_EXPERIENCE_PATTERNS = [
    r"(?i)\bexperience\b",
    r"(?i)\bwork(?:ed|ing)?\s+(?:at|for|with|history)\b",
    r"(?i)\bcompan(?:y|ies)\b",
    r"(?i)\bduration\b",
    r"(?i)\byears?\s+of\b",
    r"(?i)\bhow\s+(?:long|many\s+years|much\s+experience)\b",
    r"(?i)\bjob\s+title",
    r"(?i)\brole(?:s)?\b",
    r"(?i)\bposition(?:s)?\b",
    r"(?i)\bemploy(?:ment|er)\b",
    r"(?i)\bintern(?:s|ship|ships)?\b",
    r"(?i)\btotal\s+(?:experience|work)\b",
    r"(?i)\bwhere\s+(?:did|has|does)\s+(?:the\s+)?(?:candidate|they|he|she)\s+work",
    r"(?i)\bnumber\s+of\s+(?:internships?|jobs?|roles?|positions?)",
    r"(?i)\bexperience\s+dates?\b",
    r"(?i)\bdates?\s+of\s+experience\b",
    r"(?i)\btimeline\b",
]

FACTUAL_EDUCATION_PATTERNS = [
    r"(?i)\beducat(?:ion|ional)\b",
    r"(?i)\bdegree\b",
    r"(?i)\buniversit(?:y|ies)\b",
    r"(?i)\bcollege\b",
    r"(?i)\bschool\b",
    r"(?i)\bgraduat(?:e|ed|ion)\b",
    r"(?i)\bacademic\b",
    r"(?i)\bqualification\b",
    r"(?i)\bb\.?(?:e|tech|sc|a|com)\b",
    r"(?i)\bm\.?(?:e|tech|sc|a|com|ba)\b",
    r"(?i)\bph\.?d\b",
    r"(?i)\bdiploma\b",
]

FACTUAL_CERT_PATTERNS = [
    r"(?i)\bcertificat(?:ion|ions|e|es|ed)\b",
    r"(?i)\bcredential\b",
    r"(?i)\blicens(?:e|ed|ing)\b",
    r"(?i)\baws\s+certified\b",
    r"(?i)\bcertified\b",
]

FACTUAL_CONTACT_PATTERNS = [
    r"(?i)\bemail\b",
    r"(?i)\bphone\b",
    r"(?i)\bcontact\b",
    r"(?i)\bname\b.*\b(?:candidate|their|his|her)\b",
    r"(?i)\bwhat\s+is\s+(?:the\s+)?(?:candidate'?s?|their|his|her)\s+name\b",
    r"(?i)\blinkedin\b",
    r"(?i)\bgithub\b",
    r"(?i)\bportfolio\b",
]

FACTUAL_PROJECT_PATTERNS = [
    r"(?i)\bproject(?:s)?\b",
    r"(?i)\bbuilt\b",
    r"(?i)\bdeveloped\b",
    r"(?i)\bportfolio\b",
    r"(?i)\bside\s+project",
    r"(?i)\bpersonal\s+project",
]

EVALUATION_PATTERNS = [
    r"(?i)\bsuitabl(?:e|ility)\b",
    r"(?i)\bstrength(?:s)?\b",
    r"(?i)\bweakness(?:es)?\b",
    r"(?i)\bevaluat(?:e|ion)\b",
    r"(?i)\brecommend(?:ation)?\b",
    r"(?i)\bfit\s+for\b",
    r"(?i)\bgap\s+analysis\b",
    r"(?i)\bassess(?:ment)?\b",
    r"(?i)\bqualified\b",
    r"(?i)\bgood\s+(?:for|fit|candidate|match)\b",
    r"(?i)\bhir(?:e|ing)\b",
    r"(?i)\bshould\s+(?:we|i)\b",
    r"(?i)\bpros?\s+(?:and|&)\s+cons?\b",
    r"(?i)\bhow\s+(?:good|strong|qualified|suitable)\b",
    r"(?i)\bwhat\s+(?:do\s+you\s+think|is\s+your\s+(?:assessment|opinion))\b",
    r"(?i)\bcompare\s+(?:to|with|against)\b.*\b(?:role|position|job)\b",
]

SUMMARY_PATTERNS = [
    r"(?i)\bsummar(?:y|ize|ise)\b",
    r"(?i)\boverview\b",
    r"(?i)\btell\s+me\s+about\b",
    r"(?i)\bwalk\s+(?:me\s+)?through\b",
    r"(?i)\bbrief(?:ly)?\s+describe\b",
    r"(?i)\bhighlight(?:s)?\b",
    r"(?i)\bwhat\s+(?:does|can)\s+(?:the\s+)?(?:resume|candidate)\s+(?:say|offer|show|tell)\b",
    r"(?i)\bgive\s+me\s+(?:a\s+)?(?:summary|overview|rundown)\b",
]

SKILL_MATCH_PATTERNS = [
    r"(?i)\bmatch\b.*\b(?:job|jd|description|requirements?|role|position)\b",
    r"(?i)\bcompare\b.*\b(?:job|jd|description|requirements?)\b",
    r"(?i)\bjob\s+description\b",
    r"(?i)\b(?:jd|job)\s+match\b",
    r"(?i)\brequirements?\s+match\b",
    r"(?i)\bfit\s+(?:for|against)\s+(?:this|the)\s+(?:job|role|position)\b",
]

KEYWORD_PATTERNS = [
    r"(?i)\bkeyword(?:s)?\b",
    r"(?i)\bextract\s+keyword",
    r"(?i)\bats\b",
    r"(?i)\bimportant\s+terms?\b",
    r"(?i)\btechnical\s+terms?\b",
    r"(?i)\bdomain\s+keyword",
]


def classify_intent(query: str) -> IntentType:
    """
    Classify the user query intent using rule-based keyword matching.
    
    No LLM call is made. Classification is instant, deterministic, and free.
    
    Priority order matters — more specific intents are checked first:
    1. Skill match (requires JD context)
    2. Keywords extraction
    3. Summary/evaluation (LLM-required)
    4. Factual lookups (deterministic tools)
    5. Default to evaluation (safest LLM path)
    
    Args:
        query: The user's natural language query.
    
    Returns:
        IntentType indicating which handler should process the query.
    """
    query_stripped = query.strip()

    # 1. Check skill match first (specific)
    if _matches_any(query_stripped, SKILL_MATCH_PATTERNS):
        return "skill_match"

    # 2. Keyword extraction
    if _matches_any(query_stripped, KEYWORD_PATTERNS):
        return "keyword"

    # 3. Summary requests
    if _matches_any(query_stripped, SUMMARY_PATTERNS):
        return "summary"

    # 4. Evaluation/assessment (LLM-required, but grounded)
    if _matches_any(query_stripped, EVALUATION_PATTERNS):
        return "evaluation"

    # 5. Factual lookups (deterministic tools) — order matters
    if _matches_any(query_stripped, FACTUAL_CERT_PATTERNS):
        return "factual_certifications"
    
    if _matches_any(query_stripped, FACTUAL_CONTACT_PATTERNS):
        return "factual_contact"

    if _matches_any(query_stripped, FACTUAL_EDUCATION_PATTERNS):
        return "factual_education"

    if _matches_any(query_stripped, FACTUAL_PROJECT_PATTERNS):
        return "factual_projects"

    # Skills before experience because "experience with X" should check skills
    if _matches_any(query_stripped, FACTUAL_SKILLS_PATTERNS):
        return "factual_skills"

    if _matches_any(query_stripped, FACTUAL_EXPERIENCE_PATTERNS):
        return "factual_experience"

    # 6. Default to evaluation (LLM handles with guardrails)
    return "evaluation"


def _matches_any(text: str, patterns: list) -> bool:
    """Check if text matches any of the given regex patterns."""
    return any(re.search(p, text) for p in patterns)
