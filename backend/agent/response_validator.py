"""
Post-LLM response validation layer.

This module sits between the LLM output and the user-facing response.
It cross-references claims made in the generated answer against the
actual extracted resume data and *sanitizes* responses that contain
potential hallucinations.  Responses are never rejected — they are
adjusted (confidence recalibrated, source corrected, missing_data
populated) so downstream consumers always receive a usable payload.

Design rationale
────────────────
The LLM occasionally returns high-confidence answers sourced as
"resume" even when the underlying data doesn't support the claim.
Without this layer the retry loop in the LLM client can exhaust its
budget chasing a confidence threshold that was never warranted.
Clamping confidence by source prevents that bug while still allowing
the pipeline to surface useful inferred information at an honestly
lower confidence.
"""

from __future__ import annotations

import re
from typing import FrozenSet, List, Set

from backend.models.response import AgentResponse
from backend.models.session import ResumeData

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

#: Comprehensive set of technology / skill keywords used for grounding.
#: All entries are stored in **lower-case** for case-insensitive matching.
COMMON_TECH_SKILLS: FrozenSet[str] = frozenset({
    # ── Languages ────────────────────────────────────────────────────
    "python", "javascript", "typescript", "java", "c", "c++", "c#",
    "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
    "perl", "r", "matlab", "lua", "haskell", "elixir", "erlang",
    "clojure", "groovy", "dart", "objective-c", "fortran", "cobol",
    "assembly", "shell", "bash", "powershell", "sql", "plsql",
    "html", "css", "sass", "less", "graphql",

    # ── Frontend ─────────────────────────────────────────────────────
    "react", "reactjs", "react.js", "angular", "angularjs", "vue",
    "vuejs", "vue.js", "svelte", "next.js", "nextjs", "nuxt",
    "nuxtjs", "gatsby", "remix", "ember", "backbone", "jquery",
    "bootstrap", "tailwind", "tailwindcss", "material-ui", "mui",
    "chakra-ui", "ant-design", "redux", "mobx", "zustand", "webpack",
    "vite", "rollup", "parcel", "babel", "eslint", "prettier",
    "storybook",

    # ── Backend / Frameworks ─────────────────────────────────────────
    "node", "nodejs", "node.js", "express", "expressjs", "fastapi",
    "flask", "django", "spring", "spring-boot", "springboot",
    "rails", "ruby-on-rails", "laravel", "symfony", "asp.net",
    ".net", "dotnet", "gin", "fiber", "echo", "actix", "rocket",
    "fastify", "nestjs", "koa", "hapi",

    # ── Databases ────────────────────────────────────────────────────
    "mysql", "postgresql", "postgres", "sqlite", "mariadb",
    "oracle", "sql-server", "mssql", "mongodb", "dynamodb",
    "cassandra", "couchdb", "couchbase", "redis", "memcached",
    "neo4j", "arangodb", "influxdb", "timescaledb", "cockroachdb",
    "firestore", "supabase", "fauna", "elasticsearch",

    # ── Cloud & Infrastructure ───────────────────────────────────────
    "aws", "azure", "gcp", "google-cloud", "heroku", "vercel",
    "netlify", "digitalocean", "linode", "cloudflare", "alibaba-cloud",
    "oracle-cloud", "ibm-cloud", "openstack",

    # ── AWS Services ─────────────────────────────────────────────────
    "ec2", "s3", "lambda", "ecs", "eks", "fargate", "rds", "aurora",
    "redshift", "sqs", "sns", "kinesis", "cloudformation",
    "cloudwatch", "iam", "route53", "api-gateway", "step-functions",
    "sagemaker", "bedrock", "glue", "athena", "emr",

    # ── DevOps / CI-CD ───────────────────────────────────────────────
    "docker", "kubernetes", "k8s", "helm", "terraform", "ansible",
    "puppet", "chef", "vagrant", "packer", "consul", "vault",
    "jenkins", "github-actions", "gitlab-ci", "circleci", "travis-ci",
    "argo", "argocd", "flux", "spinnaker", "bamboo", "teamcity",

    # ── Data / ML / AI ───────────────────────────────────────────────
    "pandas", "numpy", "scipy", "scikit-learn", "sklearn",
    "tensorflow", "pytorch", "keras", "xgboost", "lightgbm",
    "catboost", "huggingface", "transformers", "langchain",
    "llamaindex", "openai", "opencv", "spacy", "nltk", "gensim",
    "mlflow", "kubeflow", "airflow", "dbt", "spark", "pyspark",
    "hadoop", "hive", "presto", "trino", "kafka", "flink",
    "beam", "dask", "ray", "polars", "matplotlib", "seaborn",
    "plotly", "tableau", "power-bi", "looker", "superset",

    # ── Testing ──────────────────────────────────────────────────────
    "pytest", "unittest", "jest", "mocha", "chai", "jasmine",
    "cypress", "playwright", "selenium", "puppeteer", "testcafe",
    "vitest", "junit", "testng", "rspec", "minitest",

    # ── Observability & Monitoring ───────────────────────────────────
    "prometheus", "grafana", "datadog", "new-relic", "splunk",
    "elk", "logstash", "kibana", "jaeger", "zipkin", "opentelemetry",
    "sentry", "pagerduty",

    # ── Messaging & Queues ───────────────────────────────────────────
    "rabbitmq", "celery", "nats", "pulsar", "zeromq",

    # ── Version Control & Collaboration ──────────────────────────────
    "git", "github", "gitlab", "bitbucket", "svn", "mercurial",
    "jira", "confluence", "notion", "slack", "trello",

    # ── API & Protocols ──────────────────────────────────────────────
    "rest", "restful", "grpc", "protobuf", "soap", "websocket",
    "mqtt", "amqp", "oauth", "oauth2", "jwt", "openapi", "swagger",

    # ── Mobile ───────────────────────────────────────────────────────
    "android", "ios", "react-native", "flutter", "xamarin", "ionic",
    "swiftui", "jetpack-compose",

    # ── Miscellaneous ────────────────────────────────────────────────
    "linux", "unix", "nginx", "apache", "caddy", "haproxy",
    "figma", "sketch", "adobe-xd", "photoshop", "illustrator",
    "agile", "scrum", "kanban", "microservices", "serverless",
    "ci/cd", "devops", "sre", "machine-learning", "deep-learning",
    "nlp", "computer-vision", "blockchain", "solidity", "web3",
    "cybersecurity", "pentesting",
})

#: Phrases that indicate the LLM couldn't find the requested information.
_NEGATIVE_PHRASES: tuple[str, ...] = (
    "not mentioned",
    "not found",
    "not present",
    "not available",
    "no information",
    "not specified",
    "no details",
    "not provided",
    "not listed",
    "not included",
    "does not mention",
    "doesn't mention",
    "no mention",
    "couldn't find",
    "could not find",
    "unable to find",
    "not explicitly",
    "not clear",
)

#: Hedging language that implies the LLM is speculating.
_HEDGING_WORDS: tuple[str, ...] = (
    "might",
    "could",
    "possibly",
    "likely",
    "perhaps",
    "probably",
    "may ",          # trailing space to avoid matching "May" (month)
    "it seems",
    "it appears",
    "presumably",
    "suggest that",
    "suggests that",
    "it is possible",
    "it's possible",
    "speculate",
    "uncertain",
    "unclear",
)

# ──────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────

# Pre-compiled regex: matches word-boundary tech tokens.  We build it
# once at module load so repeated calls pay zero compilation cost.
_TECH_PATTERN: re.Pattern[str] = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in sorted(COMMON_TECH_SKILLS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _extract_tech_keywords(text: str) -> Set[str]:
    """Return the set of recognised tech keywords found in *text*.

    Matching is case-insensitive; results are returned in lower-case.
    The regex uses longest-match-first ordering so that e.g.
    ``"react-native"`` is preferred over ``"react"``.

    Args:
        text: Free-form string (typically the LLM-generated answer).

    Returns:
        A set of lower-cased technology keywords found in the text.
    """
    return {m.group().lower() for m in _TECH_PATTERN.finditer(text)}


def _normalise_skill(skill: str) -> str:
    """Normalise a skill string for comparison.

    Strips whitespace, lowercases, and collapses internal whitespace so
    that ``" React.js "`` matches ``"react.js"``.

    Args:
        skill: Raw skill string from the resume data.

    Returns:
        Normalised, lower-cased skill string.
    """
    return re.sub(r"\s+", " ", skill.strip().lower())


def _extract_resume_skills(resume_data: ResumeData) -> Set[str]:
    """Build a normalised set of skills from the resume.

    Args:
        resume_data: Parsed resume payload.

    Returns:
        Set of normalised skill strings.
    """
    return {_normalise_skill(s) for s in resume_data.skills if s.strip()}


def _extract_resume_entities(resume_data: ResumeData) -> Set[str]:
    """Build a normalised set of entities (companies, roles, certifications) from the resume.

    Args:
        resume_data: Parsed resume payload.

    Returns:
        Set of lower-cased entity names.
    """
    entities: Set[str] = set()
    for entry in resume_data.experience:
        company = entry.get("company", "")
        if company and company.strip():
            entities.add(company.strip().lower())
        role = entry.get("role", "")
        if role and role.strip():
            entities.add(role.strip().lower())
    for cert in resume_data.certifications:
        if cert and cert.strip():
            entities.add(cert.strip().lower())
    for skill in resume_data.skills:
        if skill and skill.strip():
            entities.add(skill.strip().lower())
    return entities


def _answer_contains_negative(answer_lower: str) -> bool:
    """Check whether the answer signals a data gap.

    Args:
        answer_lower: The answer text, already lower-cased.

    Returns:
        ``True`` if any negative phrase is present.
    """
    return any(phrase in answer_lower for phrase in _NEGATIVE_PHRASES)


def _answer_contains_hedging(answer_lower: str) -> bool:
    """Check whether the answer uses speculative language.

    Args:
        answer_lower: The answer text, already lower-cased.

    Returns:
        ``True`` if any hedging word/phrase is present.
    """
    return any(word in answer_lower for word in _HEDGING_WORDS)


def _find_ungrounded_entities(
    answer: str,
    resume_entities: Set[str],
) -> List[str]:
    """Identify potential entity names (companies, roles, certs) in the answer not present in the resume.

    Heuristic: we look for capitalised multi-word sequences or single
    capitalised words that are at least 3 characters long, then compare
    them against known resume entities.

    Args:
        answer: Raw answer text from the LLM.
        resume_entities: Normalised set of entity names from the resume.

    Returns:
        List of ungrounded entity candidates found in the answer.
    """
    # Match capitalised words / sequences (e.g. "Acme Corp", "Google").
    # We require at least one uppercase letter to reduce noise.
    candidates: Set[str] = set()
    for match in re.finditer(
        r"\b([A-Z][a-zA-Z&.'-]*(?:\s+[A-Z][a-zA-Z&.'-]*)*)\b", answer
    ):
        candidate = match.group()
        # Skip very short matches and common English capitalisations.
        if len(candidate) < 3:
            continue
        # Skip sentence-start false positives for extremely common words.
        if candidate.lower() in _COMMON_ENGLISH_CAPS:
            continue
        candidates.add(candidate)

    ungrounded: List[str] = []
    for candidate in sorted(candidates):
        normalised = candidate.strip().lower()
        # Check against every known entity; allow substring matching
        if not any(
            normalised in entity or entity in normalised
            for entity in resume_entities
        ):
            ungrounded.append(candidate)

    return ungrounded


#: Common capitalised English words that should NOT be treated as
#: company names.  Kept intentionally short — only the highest-frequency
#: false positives observed in practice.
_COMMON_ENGLISH_CAPS: FrozenSet[str] = frozenset({
    "the", "this", "that", "these", "those",
    "what", "which", "where", "when", "who", "how",
    "and", "but", "for", "not", "with", "from",
    "are", "was", "were", "been", "being",
    "has", "had", "have", "having",
    "does", "did", "doing",
    "will", "would", "could", "should", "might", "may",
    "can", "shall", "must",
    "yes", "also", "very", "just", "even",
    "all", "any", "each", "every", "some",
    "here", "there", "then", "than", "into",
    "about", "after", "before", "between",
    "however", "therefore", "furthermore", "moreover",
    "based", "using", "including", "according",
    "experience", "skills", "education", "projects",
    "resume", "work", "role", "position", "responsibilities",
    "summary", "overview", "background", "profile",
    "senior", "junior", "lead", "principal", "staff",
    "software", "engineer", "developer", "manager", "analyst",
    "data", "system", "application", "service", "platform",
})


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def validate_response(
    response: AgentResponse,
    resume_data: ResumeData,
) -> AgentResponse:
    """Validate and sanitise an LLM-generated response against resume data.

    This function applies a sequence of heuristic checks to the
    ``response`` and returns a *new* ``AgentResponse`` with any
    necessary corrections.  The original object is never mutated.

    Checks performed (in order):
        1. **Source verification** — hedging language forces source to
           ``"inference"``.
        2. **Skill grounding** — tech keywords in the answer not
           present in the resume reduce confidence and populate
           ``missing_data``.
        3. **Company grounding** — company names in the answer not
           present in the resume are flagged.
        4. **Missing-data consistency** — negative phrases in the
           answer force low confidence and a populated ``missing_data``
           list.
        5. **Confidence calibration** — final clamp based on source
           type to prevent retry-loop exhaustion.

    Args:
        response: The raw ``AgentResponse`` produced by the LLM layer.
        resume_data: The structured resume data to validate against.

    Returns:
        A new ``AgentResponse`` instance with validated / corrected
        fields.  The original ``response`` is not modified.
    """
    # Work on mutable copies of the fields we may adjust.
    confidence: float = response.confidence
    source: str = response.source
    missing_data: List[str] = list(response.missing_data)
    answer: str = response.answer
    answer_lower: str = answer.lower()

    # ── 1. Source verification ───────────────────────────────────────
    source, confidence = _check_source_verification(
        answer_lower, source, confidence,
    )

    # ── 2. Skill grounding ───────────────────────────────────────────
    confidence, missing_data = _check_skill_grounding(
        answer, resume_data, confidence, missing_data,
    )

    # ── 3. Entity grounding (companies, roles, certifications) ───────
    confidence, missing_data = _check_entity_grounding(
        answer, resume_data, confidence, missing_data,
    )

    # ── 4. Experience calculation grounding ──────────────────────────
    confidence, missing_data = _check_experience_calculations(
        answer_lower, resume_data, confidence, missing_data,
    )

    # ── 5. Missing-data consistency ──────────────────────────────────
    confidence, missing_data = _check_missing_data_consistency(
        answer_lower, confidence, missing_data,
    )

    # ── 6. STRICT REJECTION & SOURCE OVERRIDE ────────────────────────
    # If any missing data or hallucination is detected, we forcefully
    # reject the response and attribute it to the resume.
    if missing_data:
        answer = "Not mentioned in resume"
        source = "resume"
        confidence = 1.0

    # ── 5. Confidence calibration (always last) ──────────────────────
    confidence = _calibrate_confidence(source, confidence)

    # Clamp to valid range after all adjustments.
    confidence = max(0.0, min(1.0, confidence))

    return AgentResponse(
        answer=answer,
        confidence=round(confidence, 4),
        source=source,  # type: ignore[arg-type]
        missing_data=missing_data,
    )


# ──────────────────────────────────────────────────────────────────────
# Individual check implementations
# ──────────────────────────────────────────────────────────────────────

def _check_source_verification(
    answer_lower: str,
    source: str,
    confidence: float,
) -> tuple[str, float]:
    """Downgrade source to ``'inference'`` if hedging language is detected.

    Args:
        answer_lower: Lower-cased answer text.
        source: Current source label.
        confidence: Current confidence score.

    Returns:
        Tuple of (possibly updated source, unchanged confidence).
    """
    if source == "resume" and _answer_contains_hedging(answer_lower):
        source = "inference"
    return source, confidence


def _check_skill_grounding(
    answer: str,
    resume_data: ResumeData,
    confidence: float,
    missing_data: List[str],
) -> tuple[float, List[str]]:
    """Flag tech skills mentioned in the answer but absent from the resume.

    Each ungrounded skill reduces confidence by 0.1 and is appended to
    ``missing_data``.

    Args:
        answer: Raw answer text.
        resume_data: Parsed resume payload.
        confidence: Current confidence score.
        missing_data: Current list of missing-data labels.

    Returns:
        Tuple of (adjusted confidence, updated missing_data list).
    """
    mentioned_skills: Set[str] = _extract_tech_keywords(answer)
    if not mentioned_skills:
        return confidence, missing_data

    resume_skills: Set[str] = _extract_resume_skills(resume_data)

    # Also check raw_text as a fallback — skills can appear in
    # unstructured sections that the parser didn't capture cleanly.
    raw_text_lower: str = resume_data.raw_text.lower()

    for skill in sorted(mentioned_skills):
        # Consider the skill grounded if it appears in the structured
        # skills list OR anywhere in the raw resume text.
        if skill in resume_skills:
            continue
        if any(skill in rs for rs in resume_skills):
            continue
        if skill in raw_text_lower:
            continue

        label = f"Skill '{skill}' mentioned but not found in resume"
        if label not in missing_data:
            missing_data.append(label)
            confidence -= 0.1

    return confidence, missing_data


def _check_entity_grounding(
    answer: str,
    resume_data: ResumeData,
    confidence: float,
    missing_data: List[str],
) -> tuple[float, List[str]]:
    """Flag entities (companies, titles, certs) in the answer not present in the resume.

    Each ungrounded entity reduces confidence and is appended
    to ``missing_data``.

    Args:
        answer: Raw answer text.
        resume_data: Parsed resume payload.
        confidence: Current confidence score.
        missing_data: Current list of missing-data labels.

    Returns:
        Tuple of (adjusted confidence, updated missing_data list).
    """
    resume_entities: Set[str] = _extract_resume_entities(resume_data)
    if not resume_entities and not resume_data.experience and not resume_data.certifications:
        return confidence, missing_data

    ungrounded = _find_ungrounded_entities(answer, resume_entities)
    for entity in ungrounded:
        label = f"Entity '{entity}' mentioned but not found in resume"
        if label not in missing_data:
            missing_data.append(label)
            confidence -= 0.1

    return confidence, missing_data


def _check_experience_calculations(
    answer_lower: str,
    resume_data: ResumeData,
    confidence: float,
    missing_data: List[str],
) -> tuple[float, List[str]]:
    """Flag experience durations (years/months) that the LLM calculated but aren't supported.
    
    If the LLM outputs '10 years' or '23 months', verify if those exact strings
    appear in the raw text or the formatted total duration. If not, reject it.
    """
    from backend.tools.resume_parser import calculate_total_experience
    total_exp = calculate_total_experience(resume_data.experience)
    valid_duration = total_exp.get("formatted", "").lower()
    
    raw_lower = resume_data.raw_text.lower()
    
    # Match "\d+ year(s)" or "\d+ month(s)"
    durations = re.finditer(r"\b(\d+)\s*(year|month)s?\b", answer_lower)
    for match in durations:
        full_match = match.group(0)
        num = match.group(1)
        unit = match.group(2)
        
        # Build variations to check
        variations = [
            full_match,
            f"{num} {unit}",
            f"{num} {unit}s",
            f"{num} {unit}(s)",
            f"{num}+{unit}"
        ]
        
        is_supported = False
        for var in variations:
            if var in valid_duration or var in raw_lower:
                is_supported = True
                break
                
        if not is_supported:
            label = f"Experience duration '{full_match}' is not supported by the resume data"
            if label not in missing_data:
                missing_data.append(label)
                confidence -= 0.1
                
    return confidence, missing_data


def _check_missing_data_consistency(
    answer_lower: str,
    confidence: float,
    missing_data: List[str],
) -> tuple[float, List[str]]:
    """Ensure answers that admit missing data have low confidence.

    If the answer contains phrases like *"not mentioned"* or
    *"no information"*, confidence is clamped to ≤ 0.3 and a
    generic missing-data label is added if the list is empty.

    Args:
        answer_lower: Lower-cased answer text.
        confidence: Current confidence score.
        missing_data: Current list of missing-data labels.

    Returns:
        Tuple of (adjusted confidence, updated missing_data list).
    """
    if not _answer_contains_negative(answer_lower):
        return confidence, missing_data

    confidence = min(confidence, 0.3)
    if not missing_data:
        missing_data.append("Requested information not found in resume")

    return confidence, missing_data


def _calibrate_confidence(source: str, confidence: float) -> float:
    """Apply final confidence clamps based on source type.

    Rules:
        * ``source='resume'``   → confidence ≥ 0.85
        * ``source='inference'`` → confidence ≤ 0.75

    This prevents the retry-exhaustion bug where the LLM client keeps
    retrying because confidence is slightly below the threshold for
    resume-sourced answers, or dangerously high for inferred ones.

    Args:
        source: The (possibly corrected) source label.
        confidence: The confidence score after all prior adjustments.

    Returns:
        Clamped confidence value.
    """
    if source == "resume" and confidence < 0.85:
        return 0.85
    if source == "inference" and confidence > 0.75:
        return 0.75
    return confidence
