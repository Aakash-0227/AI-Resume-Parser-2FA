
from pathlib import Path

import pdfplumber
from docx import Document


def extract_text(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("Resume file not found")

    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(path)

    elif extension == ".docx":
        return extract_docx_text(path)

    else:
        raise ValueError("Only PDF and DOCX files are supported")


def extract_pdf_text(file_path: Path) -> str:
    extracted_text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                extracted_text.append(page_text)

    text = "\n".join(extracted_text).strip()

    if not text:
        raise ValueError("No readable text found in PDF")

    return text


def extract_docx_text(file_path: Path) -> str:
    document = Document(file_path)

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    text = "\n".join(paragraphs)

    if not text:
        raise ValueError("No readable text found in DOCX")

    return text
