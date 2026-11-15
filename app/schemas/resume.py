
from pydantic import BaseModel, EmailStr, Field


class ResumeExtractedData(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    qualification: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: str | None = None


class ResumeParseResponse(BaseModel):
    message: str
    filename: str
    extracted_data: ResumeExtractedData
