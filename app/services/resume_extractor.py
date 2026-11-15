
import re

from app.schemas.resume import ResumeExtractedData


KNOWN_SKILLS = [
    "Python",
    "SQL",
    "FastAPI",
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "Generative AI",
    "LLMs",
    "LangChain",
    "LangGraph",
    "Hugging Face",
    "CrewAI",
    "Microsoft AutoGen",
    "FAISS",
    "Vector Databases",
    "Embeddings",
    "Semantic Search",
    "Streamlit",
    "NumPy",
    "Pandas",
    "Git",
    "GitHub",
    "MLflow",
    "OpenAI",
    "Google Gemini",
    "Anthropic Claude",
    "REST APIs",
    "OOP",
    "Data Structures and Algorithms"
]


def extract_email(text: str) -> str | None:
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = re.search(
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
        text
    )

    return match.group(0) if match else None


def extract_name(text: str) -> str | None:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines[:5]:
        if "@" not in line and not re.search(r"\d", line):
            if len(line) <= 60:
                return line

    return None


def extract_skills(text: str) -> list[str]:
    found_skills = []

    text_lower = text.lower()

    for skill in KNOWN_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    return found_skills


def extract_qualification(text: str) -> str | None:
    qualification_patterns = [
        r"\bB\.?\s?Tech\b",
        r"\bM\.?\s?Tech\b",
        r"\bB\.?\s?E\.?\b",
        r"\bM\.?\s?E\.?\b",
        r"\bB\.?\s?Sc\b",
        r"\bM\.?\s?Sc\b",
        r"\bBCA\b",
        r"\bMCA\b",
        r"\bMBA\b",
        r"\bPh\.?D\b",
        r"\bBachelor(?:'s)?\s+(?:of|in)\s+[\w\s&]+",
        r"\bMaster(?:'s)?\s+(?:of|in)\s+[\w\s&]+",
        r"\bDiploma\s+in\s+[\w\s&]+"
    ]

    for pattern in qualification_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0).strip()

    return None


def extract_experience(text: str) -> str | None:
    lines = text.splitlines()

    experience_lines = [
        line.strip()
        for line in lines
        if re.search(
            r"intern|experience|developer|engineer",
            line,
            re.IGNORECASE
        )
    ]

    if experience_lines:
        return " ".join(experience_lines[:5])

    return None


def extract_resume_data(text: str) -> ResumeExtractedData:
    return ResumeExtractedData(
        name=extract_name(text),
        email=extract_email(text),
        phone=extract_phone(text),
        qualification=extract_qualification(text),
        skills=extract_skills(text),
        experience=extract_experience(text)
    )
