# AI-generated PR — review this code
# Description: Added file upload endpoint with validation and storage

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

UPLOAD_DIR = Path("/var/app/uploads")
TEMP_DIR = Path("/var/app/uploads/tmp")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx", ".xlsx"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    uploaded_at: str
    url: str


def ensure_directories():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def validate_file_type(filename: str) -> bool:
    """Check if the file extension is in the allowed list."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def generate_storage_path(filename: str) -> Path:
    """Generate the final storage path preserving original filename."""
    today = datetime.utcnow().strftime("%Y/%m/%d")
    storage_dir = UPLOAD_DIR / today
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / filename


def get_file_url(file_path: Path) -> str:
    """Generate the public URL for an uploaded file."""
    relative = file_path.relative_to(UPLOAD_DIR)
    return f"/files/{relative}"


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload with validation and storage."""
    ensure_directories()

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    if not validate_file_type(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Generate a unique file ID for tracking
    file_id = str(uuid.uuid4())

    # Write to temp location first
    temp_path = TEMP_DIR / f"{file_id}_{file.filename}"

    contents = await file.read()
    total_size = len(contents)

    with open(temp_path, "wb") as temp_file:
        temp_file.write(contents)

    # Generate final storage path and move file
    final_path = generate_storage_path(file.filename)

    try:
        shutil.move(str(temp_path), str(final_path))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store file: {str(e)}",
        )

    file_url = get_file_url(final_path)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=total_size,
        uploaded_at=datetime.utcnow().isoformat(),
        url=file_url,
    )


@app.get("/api/files/{file_id}")
async def get_file_info(file_id: str):
    """Get metadata about an uploaded file."""
    # In production, look up file_id in database
    return JSONResponse(
        content={"file_id": file_id, "status": "available"},
        status_code=200,
    )


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file."""
    # In production, look up file_id in database and delete from storage
    return JSONResponse(
        content={"file_id": file_id, "deleted": True},
        status_code=200,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "upload_dir_exists": UPLOAD_DIR.exists()}
