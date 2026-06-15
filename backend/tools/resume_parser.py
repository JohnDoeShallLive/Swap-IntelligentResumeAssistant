"""
Deterministic Resume Parser — No LLM dependency.

Extracts structured data from resume text using regex patterns and heuristics.
This replaces the previous LLM-based extraction to eliminate hallucination
at the foundation layer. Every field is extracted directly from the text
or marked as None/empty.
"""

import re
import io
from typing import Optional, List, Dict, Any
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser as dateutil_parser

import pdfplumber

from backend.models.session import ResumeData


# ─── Section heading patterns ──────────────────────────────────────────────────
SECTION_PATTERNS = {
    "summary": r"(?i)^(?:summary|objective|profile|about\s*me|professional\s*summary)",
    "skills": r"(?i)^(?:skills?|technical\s*skills?|core\s*competencies|technologies|tech\s*stack)",
    "experience": r"(?i)^(?:experience|work\s*experience|professional\s*experience|employment|work\s*history)",
    "education": r"(?i)^(?:education|academic|qualifications?|academic\s*background)",
    "projects": r"(?i)^(?:projects?|personal\s*projects?|academic\s*projects?|key\s*projects?)",
    "certifications": r"(?i)^(?:certifications?|certificates?|licenses?|certifications?\s*[&\u0026]\s*activit)",
}

# ─── Date parsing helpers ──────────────────────────────────────────────────────
MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

DATE_RANGE_PATTERN = re.compile(
    r"(?P<start_month>[A-Za-z]+)\s*(?P<start_year>\d{4})\s*[-–—to]+\s*"
    r"(?P<end>(?:(?P<end_month>[A-Za-z]+)\s*(?P<end_year>\d{4}))|(?:present|current|now|ongoing))",
    re.IGNORECASE,
)

# ─── Skill normalization ──────────────────────────────────────────────────────
TECH_SYNONYMS = {
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
    "github actions": "GitHub Actions",
    "shell scripting": "Shell Scripting",
    "data structures": "Data Structures",
}


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from PDF bytes using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text


def _fix_pdf_spacing(text: str) -> str:
    """
    Fix common PDF text extraction artifacts where spaces are missing.
    E.g., 'DrivenJuniorDevOps' -> tries to detect and doesn't modify 
    (we keep raw for parsing but use it for section detection).
    
    Also handles the split-name artifact: 'S S\\nHREYASH ULE' -> 'SHREYASH SULE'
    """
    lines = text.split("\n")
    if len(lines) >= 2:
        # Check for the split first-letter pattern: "S S" followed by "HREYASH ULE"
        first_line = lines[0].strip()
        second_line = lines[1].strip()
        # Pattern: single letters separated by spaces on first line
        if re.match(r'^[A-Z]\s+[A-Z]$', first_line) and re.match(r'^[A-Z]+\s+[A-Z]+', second_line):
            # Reconstruct name: first letters + remaining parts
            initials = first_line.replace(" ", "")
            parts = second_line.split()
            if len(initials) == len(parts):
                reconstructed_parts = []
                for i, part in enumerate(parts):
                    reconstructed_parts.append(initials[i] + part)
                lines[0] = " ".join(reconstructed_parts)
                lines[1] = ""  # Remove the second line since we merged it
    
    return "\n".join(lines)


def _detect_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into named sections based on heading patterns.
    Returns a dict mapping section names to their text content.
    """
    lines = text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = "header"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_section in sections:
                sections[current_section].append("")
            continue

        found_section = False
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, stripped):
                current_section = section_name
                if current_section not in sections:
                    sections[current_section] = []
                found_section = True
                break

        if not found_section:
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _extract_name(text: str) -> Optional[str]:
    """Extract candidate name (typically the first non-empty line)."""
    lines = text.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped and not re.search(r'@|http|www\.|\.com|phone|email|linkedin|github', stripped, re.IGNORECASE):
            # Clean up: remove any non-name characters
            name = re.sub(r'[^a-zA-Z\s.\'-]', '', stripped).strip()
            if name and len(name) > 1:
                return name.title() if name.isupper() else name
    return None


def _extract_email(text: str) -> Optional[str]:
    """Extract email address using regex."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    """Extract phone number using regex."""
    # Match various phone formats, prioritize longer matches
    patterns = [
        r'[\+]?[\d]{1,3}[-.\s]?[\d]{3}[-.\s]?[\d]{3}[-.\s]?[\d]{4}',
        r'[\+]?[\d\s\-\(\)]{10,15}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0).strip()
            # Ensure it has enough digits
            digits = re.sub(r'\D', '', phone)
            if len(digits) >= 10:
                return phone
    return None


def _extract_skills(sections: Dict[str, str], raw_text: str) -> List[str]:
    """
    Extract skills from the skills section. Only extracts EXPLICITLY listed skills.
    Never infers or assumes skills.
    """
    skills_text = sections.get("skills", "")
    if not skills_text:
        # Try to find skills in the full text with a broader pattern
        match = re.search(
            r'(?i)(?:skills?|technical\s*skills?|core\s*competencies)[:\s]*(.+?)(?=\n\s*\n|\n[A-Z]|$)',
            raw_text,
            re.DOTALL,
        )
        if match:
            skills_text = match.group(1)

    if not skills_text:
        return []

    skills = set()
    # Split by common delimiters: comma, pipe, bullet, newline, colon (for category:items patterns)
    # First, handle category patterns like "DevOps&Automation: CI/CD, Docker, Linux"
    category_pattern = re.compile(r'(?:[\w\s&/]+):\s*(.+?)(?=\n|$)', re.IGNORECASE)
    for match in category_pattern.finditer(skills_text):
        items = match.group(1)
        for skill in re.split(r'[,|•;]', items):
            cleaned = skill.strip().strip('•·-–— ')
            if cleaned and len(cleaned) > 1:
                # Normalize the skill name
                normalized = TECH_SYNONYMS.get(cleaned.lower(), cleaned)
                skills.add(normalized)

    # If no category pattern matched, split the whole text
    if not skills:
        for skill in re.split(r'[,|•;\n]', skills_text):
            cleaned = skill.strip().strip('•·-–— ')
            # Remove category labels
            cleaned = re.sub(r'^[\w\s&/]+:\s*', '', cleaned).strip()
            if cleaned and len(cleaned) > 1 and not re.match(r'^(?:skills?|technical)$', cleaned, re.IGNORECASE):
                normalized = TECH_SYNONYMS.get(cleaned.lower(), cleaned)
                skills.add(normalized)

    return sorted(list(skills))


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string like 'Jan 2026' or 'January 2026' into a datetime."""
    date_str = date_str.strip()
    try:
        return dateutil_parser.parse(date_str, fuzzy=True)
    except (ValueError, TypeError):
        pass
    
    # Manual parsing for "MonYYYY" patterns (no space, common in PDFs)
    match = re.match(r'([A-Za-z]+)\s*(\d{4})', date_str)
    if match:
        month_str = match.group(1).lower()
        year = int(match.group(2))
        month = MONTH_MAP.get(month_str[:3])
        if month and 1900 < year < 2100:
            return datetime(year, month, 1)
    
    return None


def _calculate_duration(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate exact duration between two dates."""
    delta = relativedelta(end_date, start_date)
    total_months = delta.years * 12 + delta.months
    return {
        "years": delta.years,
        "months": delta.months,
        "total_months": total_months,
        "formatted": f"{delta.years} year(s) and {delta.months} month(s)" if delta.years > 0 
                     else f"{delta.months} month(s)",
    }


def _extract_experience(sections: Dict[str, str], raw_text: str) -> List[Dict[str, Any]]:
    """
    Extract work experience entries with company, role, dates, duration, and description.
    Uses deterministic date parsing — never guesses dates.
    """
    exp_text = sections.get("experience", "")
    if not exp_text:
        return []

    experiences = []
    lines = exp_text.split("\n")
    
    current_entry = None
    description_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Try to match a date range in this line
        date_match = DATE_RANGE_PATTERN.search(stripped)
        
        if date_match:
            # Save previous entry if exists
            if current_entry:
                current_entry["description"] = " ".join(description_lines).strip()
                experiences.append(current_entry)
                description_lines = []

            # Parse the role/company line
            # Common patterns: "Role | Company – Location DateRange" or "Role | Company DateRange"
            text_before_date = stripped[:date_match.start()].strip().rstrip('|–—-,')
            
            # Split by common delimiters
            parts = re.split(r'\s*[|–—]\s*', text_before_date)
            role = parts[0].strip() if parts else ""
            company = ""
            location = ""
            
            if len(parts) >= 2:
                company_location = parts[1].strip()
                # Try to split company and location by " – " or last comma
                loc_match = re.search(r'(.+?)[-–—]\s*(\w+)$', company_location)
                if loc_match:
                    company = loc_match.group(1).strip()
                    location = loc_match.group(2).strip()
                else:
                    company = company_location

            # Parse dates
            start_str = f"{date_match.group('start_month')} {date_match.group('start_year')}"
            start_date = _parse_date(start_str)
            
            end_str = date_match.group('end').strip()
            is_current = bool(re.match(r'(?i)present|current|now|ongoing', end_str))
            
            if is_current:
                end_date = datetime.now()
            else:
                end_date = _parse_date(end_str)

            duration = None
            if start_date and end_date:
                duration = _calculate_duration(start_date, end_date)

            current_entry = {
                "role": role,
                "company": company,
                "location": location,
                "start_date": start_str,
                "end_date": "Present" if is_current else end_str,
                "duration": duration,
                "description": "",
            }
        elif stripped.startswith("•") or stripped.startswith("-") or stripped.startswith("·"):
            # Bullet point — part of description
            description_lines.append(stripped.lstrip("•-·– "))
        elif current_entry:
            # Continuation of description or role
            description_lines.append(stripped)

    # Save last entry
    if current_entry:
        current_entry["description"] = " ".join(description_lines).strip()
        experiences.append(current_entry)

    return experiences


def _extract_education(sections: Dict[str, str], raw_text: str) -> List[Dict[str, Any]]:
    """Extract education entries with institution, degree, field, year, and GPA."""
    edu_text = sections.get("education", "")
    if not edu_text:
        return []

    education = []
    lines = edu_text.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        entry = {}

        # Try to extract GPA/CGPA/percentage
        gpa_match = re.search(r'(\d+\.?\d*)\s*/\s*(\d+\.?\d*)', stripped)
        if gpa_match:
            entry["gpa"] = f"{gpa_match.group(1)}/{gpa_match.group(2)}"

        percentage_match = re.search(r'(\d+\.?\d*)\s*%', stripped)
        if percentage_match:
            entry["percentage"] = f"{percentage_match.group(1)}%"

        # Try to extract year
        year_match = re.search(r'\(?\s*(20\d{2})\s*\)?', stripped)
        if year_match:
            entry["year"] = year_match.group(1)

        # Try to extract degree type
        degree_patterns = [
            r'(?i)(B\.?E\.?|B\.?Tech|B\.?Sc|M\.?E\.?|M\.?Tech|M\.?Sc|MBA|Ph\.?D|B\.?A\.?|M\.?A\.?|BCA|MCA|B\.?Com|M\.?Com)',
            r'(?i)(Bachelor|Master|Doctorate|Associate|Diploma)',
        ]
        for pattern in degree_patterns:
            degree_match = re.search(pattern, stripped)
            if degree_match:
                entry["degree"] = degree_match.group(1)
                break

        # Try to extract field of study
        field_match = re.search(r'(?i)(?:in|of)\s+([A-Za-z\s]+?)(?:\s*\(|\s*$|\s*\d)', stripped)
        if field_match:
            entry["field"] = field_match.group(1).strip()

        # Extract institution (typically contains "University", "Institute", "College", etc.)
        # Or use the main text before the degree/year markers
        inst_patterns = [
            r'(?i)([\w\s]+(?:university|institute|college|school|academy)[\w\s]*)',
        ]
        for pattern in inst_patterns:
            inst_match = re.search(pattern, stripped)
            if inst_match:
                entry["institution"] = inst_match.group(1).strip()
                break

        # Fallback: use the line split by em-dash
        if "institution" not in entry:
            parts = re.split(r'\s*[—–-]\s*', stripped)
            if parts:
                entry["institution"] = parts[0].strip()

        if entry:
            education.append(entry)

    return education


def _extract_projects(sections: Dict[str, str], raw_text: str) -> List[Dict[str, Any]]:
    """Extract project entries with name, description, and tech stack."""
    proj_text = sections.get("projects", "")
    if not proj_text:
        return []

    projects = []
    lines = proj_text.split("\n")
    current_project = None
    description_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this is a project title line (contains tech stack after the name)
        # Pattern: "ProjectName TechList" or "ProjectName (TechList)"
        is_bullet = stripped.startswith("•") or stripped.startswith("-") or stripped.startswith("·")
        
        if not is_bullet and not stripped.startswith("–"):
            # Could be a new project title
            # Heuristic: if line doesn't start with a bullet and is relatively short
            if current_project:
                current_project["description"] = " ".join(description_lines).strip()
                projects.append(current_project)
                description_lines = []

            # Try to extract tech stack from the title line
            # Pattern: "Project Name   Tech1, Tech2, Tech3"
            # Often tech stack is at the end, separated by multiple spaces or after a delimiter
            tech_match = re.search(r'(.+?)\s{2,}(.+)$', stripped)
            
            name = stripped
            tech_stack = []
            
            if tech_match:
                name = tech_match.group(1).strip()
                tech_part = tech_match.group(2).strip()
                tech_stack = [t.strip() for t in re.split(r'[,|]', tech_part) if t.strip()]
            
            # Also check for parenthesized tech stack
            paren_match = re.search(r'\(([^)]+)\)', stripped)
            if paren_match and not tech_stack:
                name = stripped[:paren_match.start()].strip()
                tech_stack = [t.strip() for t in re.split(r'[,|]', paren_match.group(1)) if t.strip()]

            current_project = {
                "name": name,
                "tech_stack": tech_stack,
                "description": "",
            }
        elif is_bullet and current_project:
            description_lines.append(stripped.lstrip("•-·– "))

    # Save last project
    if current_project:
        current_project["description"] = " ".join(description_lines).strip()
        projects.append(current_project)

    return projects


def _extract_certifications(sections: Dict[str, str], raw_text: str) -> List[str]:
    """Extract certification names from the certifications section."""
    cert_text = sections.get("certifications", "")
    if not cert_text:
        return []

    certifications = []
    lines = cert_text.split("\n")
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Skip sub-headers like "Co-curricular Activities"
        if re.match(r'(?i)^(?:co-?curricular|activities|extra-?curricular|achievements)', stripped):
            continue
        if re.match(r'(?i)^certifications?\s*$', stripped):
            continue
        if re.match(r'(?i)^co-?curricular\s*activities?\s*$', stripped):
            continue
            
        # Handle bullet points
        if stripped.startswith("•") or stripped.startswith("-") or stripped.startswith("·"):
            cert = stripped.lstrip("•-·– ").strip()
            if cert and len(cert) > 3:
                # Only add if it looks like a certification (not an activity)
                # Certifications often have these patterns
                if any(kw in cert.lower() for kw in [
                    "certified", "certification", "certificate", "foundation",
                    "academy", "aws", "cisco", "ibm", "google", "microsoft",
                    "linux", "tata", "basics", "introduction", "getting started",
                    "professional", "associate", "practitioner",
                ]):
                    certifications.append(cert)
        else:
            # Non-bullet text in certifications section — might be a cert name
            if any(kw in stripped.lower() for kw in [
                "certified", "certification", "certificate", "–", "foundation",
            ]):
                certifications.append(stripped)

    return certifications


def calculate_total_experience(experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total work experience duration from parsed experience entries.
    This is a DETERMINISTIC calculation — no LLM involved.
    
    Returns:
        Dict with total_months, years, months, and formatted string.
    """
    total_months = 0
    entries_used = []
    
    for exp in experiences:
        duration = exp.get("duration")
        if duration and isinstance(duration, dict):
            total_months += duration.get("total_months", 0)
            entries_used.append({
                "role": exp.get("role", "Unknown"),
                "company": exp.get("company", "Unknown"),
                "months": duration.get("total_months", 0),
            })
    
    years = total_months // 12
    months = total_months % 12
    
    if years > 0:
        formatted = f"{years} year(s) and {months} month(s)"
    else:
        formatted = f"{months} month(s)"
    
    return {
        "total_months": total_months,
        "years": years,
        "months": months,
        "formatted": formatted,
        "breakdown": entries_used,
    }


def parse_resume_text(text: str) -> ResumeData:
    """
    Parse raw resume text into structured ResumeData using deterministic
    regex and heuristic extraction. No LLM calls are made.
    
    Every field is extracted directly from the text or defaults to None/empty list.
    """
    # Fix PDF spacing artifacts
    fixed_text = _fix_pdf_spacing(text)
    
    # Detect sections
    sections = _detect_sections(fixed_text)
    
    return ResumeData(
        name=_extract_name(fixed_text),
        email=_extract_email(text),  # Use original text for email to preserve formatting
        phone=_extract_phone(text),
        skills=_extract_skills(sections, text),
        experience=_extract_experience(sections, text),
        education=_extract_education(sections, text),
        projects=_extract_projects(sections, text),
        certifications=_extract_certifications(sections, text),
        raw_text=text,
    )


def parse_resume(file_bytes: bytes = None, text: str = None) -> ResumeData:
    """
    Parse a resume from PDF bytes or raw text.
    
    Args:
        file_bytes: Raw PDF file bytes.
        text: Raw text content of the resume.
    
    Returns:
        ResumeData: Structured resume data extracted deterministically.
    
    Raises:
        ValueError: If neither file_bytes nor text is provided.
    """
    if file_bytes:
        extracted_text = extract_text_from_pdf(file_bytes)
    elif text:
        extracted_text = text
    else:
        raise ValueError("Must provide either file_bytes or text")

    return parse_resume_text(extracted_text)
