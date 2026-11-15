
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.resume import UserResume
from app.services.resume_parser import extract_text
from app.services.resume_extractor import extract_resume_data
from app.schemas.resume import ResumeParseResponse, ResumeExtractedData


# Logging configuration
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/resume",
    tags=["Resume"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )

    saved_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / saved_filename

    try:
        # Read uploaded file
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        # Save uploaded file
        file_path.write_bytes(content)

        # Extract text from PDF or DOCX
        extracted_text = extract_text(str(file_path))

        # Extract structured resume information
        extracted_data = extract_resume_data(extracted_text)

        # Validate extracted data
        validated_data = ResumeExtractedData.model_validate(
            extracted_data
        )

        # Create database record
        resume_record = UserResume(
            user_id=None,
            original_filename=file.filename or saved_filename,
            file_path=str(file_path),
            extracted_text=extracted_text,
            extracted_data=validated_data.model_dump(mode="json")
        )

        db.add(resume_record)

        await db.commit()
        await db.refresh(resume_record)

        logger.info(
            "Resume successfully parsed and saved. Record ID: %s",
            resume_record.id
        )

        return ResumeParseResponse(
            message="Resume parsed and saved successfully",
            filename=file.filename or saved_filename,
            extracted_data=validated_data
        )

    except HTTPException:
        raise

    except (ValueError, FileNotFoundError) as error:
        await db.rollback()

        logger.exception(
            "Resume validation or file processing failed: %s",
            error
        )

        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error

    except Exception as error:
        await db.rollback()

        logger.exception(
            "Resume processing failed: %s",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Resume processing or database storage failed"
        ) from error

    finally:
        await file.close()
