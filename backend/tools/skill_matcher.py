"""
Skill Matcher.

Extracts tech requirements from a Job Description and matches them
against the candidate's extracted skills. Provides a match score and
identifies missing requirements.
"""

import re
from typing import List, Dict, Any

# A comprehensive list of tech skills to extract from JD
# (Uses same base dictionary as resume_parser for consistency)
TECH_ALIASES = {
    "js": "JavaScript", "javascript": "JavaScript",
    "ts": "TypeScript", "typescript": "TypeScript",
    "py": "Python", "python": "Python",
    "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "mongo": "MongoDB", "mongodb": "MongoDB",
    "react.js": "React", "reactjs": "React", "react": "React",
    "node.js": "Node.js", "nodejs": "Node.js",
    "vue.js": "Vue.js", "vuejs": "Vue.js",
    "next.js": "Next.js", "nextjs": "Next.js",
    "express.js": "Express.js", "expressjs": "Express.js",
    "c++": "C++", "cpp": "C++",
    "c#": "C#", "csharp": "C#",
    "aws": "AWS", "gcp": "GCP", "azure": "Azure",
    "ci/cd": "CI/CD", "cicd": "CI/CD",
    "docker": "Docker", "ansible": "Ansible",
    "terraform": "Terraform", "jenkins": "Jenkins",
    "git": "Git", "github": "GitHub",
    "linux": "Linux", "bash": "Bash",
    "sql": "SQL", "mysql": "MySQL",
    "nginx": "Nginx", "redis": "Redis",
    "kafka": "Kafka", "rabbitmq": "RabbitMQ",
    "graphql": "GraphQL", "rest": "REST",
    "oop": "OOP", "json": "JSON",
    "html": "HTML", "css": "CSS",
    "django": "Django", "flask": "Flask", "spring": "Spring",
    "golang": "Go", "go": "Go", "rust": "Rust", "ruby": "Ruby",
}

def _extract_jd_skills(jd_text: str) -> List[str]:
    """Extract known technical skills from JD text."""
    jd_lower = jd_text.lower()
    
    # Extract using word boundaries
    words = re.findall(r'\b[\w\.\+#]+\b', jd_lower)
    
    # Also handle some special cases that might not match \b well
    # e.g., C++, C#
    
    found_skills = set()
    for word in words:
        if word in TECH_ALIASES:
            found_skills.add(TECH_ALIASES[word])
            
    # Explicit checks for symbols
    if "c++" in jd_lower:
        found_skills.add("C++")
    if "c#" in jd_lower:
        found_skills.add("C#")
    if "ci/cd" in jd_lower:
        found_skills.add("CI/CD")
        
    return list(found_skills)


def match_skills(resume_skills: List[str], jd_text: str) -> Dict[str, Any]:
    """
    Compare resume skills against extracted Job Description requirements.
    Returns a match score, matched skills, and missing skills.
    """
    if not jd_text.strip():
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "message": "No Job Description provided."
        }

    # Extract required skills from the JD
    jd_required_skills = _extract_jd_skills(jd_text)
    
    if not jd_required_skills:
        return {
            "match_score": 100,  # If no tech skills found in JD, assume fit
            "matched_skills": [],
            "missing_skills": [],
            "message": "No standard technical skills detected in the Job Description."
        }

    # Normalize resume skills for comparison
    resume_skills_lower = [s.lower() for s in resume_skills]
    resume_skills_normalized = set()
    for s in resume_skills_lower:
        # Resolve aliases if any
        resume_skills_normalized.add(TECH_ALIASES.get(s, s.title()))
        
    # Additional raw fallback: Check if the JD skill appears in the resume skills verbatim
    raw_resume_text_lower = " ".join(resume_skills_lower)

    matched = []
    missing = []
    
    for req_skill in jd_required_skills:
        req_lower = req_skill.lower()
        if req_skill in resume_skills_normalized or req_skill in resume_skills:
            matched.append(req_skill)
        elif req_lower in raw_resume_text_lower:
            matched.append(req_skill)
        else:
            missing.append(req_skill)
            
    score = 0
    if len(jd_required_skills) > 0:
        score = int((len(matched) / len(jd_required_skills)) * 100)
        
    return {
        "match_score": score,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "total_required": len(jd_required_skills)
    }
