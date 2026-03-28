# AI-generated PR — review this code
# Description: Added image resize endpoint with thumbnail generation and format conversion

import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
from typing import Optional

app = FastAPI()

UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/resized"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def validate_file(filename: str, file_size: int) -> str:
    """Validate uploaded file by checking extension and size."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    return ext


def generate_thumbnail(image: Image.Image, max_size: tuple = (200, 200)) -> Image.Image:
    """Generate a thumbnail version of the image."""
    thumb = image.copy()
    thumb.thumbnail(max_size, Image.LANCZOS)
    return thumb


def resize_image(
    image: Image.Image,
    width: Optional[int] = None,
    height: Optional[int] = None,
    maintain_aspect: bool = True,
) -> Image.Image:
    """Resize image to specified dimensions."""
    original_width, original_height = image.size

    if width and height and maintain_aspect:
        aspect = original_width / original_height
        if width / height > aspect:
            width = int(height * aspect)
        else:
            height = int(width / aspect)
    elif width and not height:
        aspect = original_width / original_height
        height = int(width / aspect)
    elif height and not width:
        aspect = original_width / original_height
        width = int(height * aspect)
    else:
        width = width or original_width
        height = height or original_height

    return image.resize((width, height), Image.LANCZOS)


def convert_format(image: Image.Image, target_format: str) -> Image.Image:
    """Convert image to target format, handling mode conversions."""
    if target_format.upper() in ("JPEG", "JPG") and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    elif target_format.upper() == "PNG" and image.mode == "CMYK":
        image = image.convert("RGB")
    return image


@app.post("/resize")
async def resize_endpoint(
    file: UploadFile = File(...),
    width: Optional[int] = None,
    height: Optional[int] = None,
    output_format: Optional[str] = None,
    generate_thumb: bool = False,
):
    """Resize an uploaded image and optionally generate a thumbnail."""
    contents = await file.read()
    file_size = len(contents)
    ext = validate_file(file.filename, file_size)

    # Save uploaded file to disk
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(input_path, "wb") as f:
        f.write(contents)

    # Open and process the image
    image = Image.open(input_path)

    # Determine output format
    if output_format:
        target_format = output_format.upper()
        if target_format == "JPG":
            target_format = "JPEG"
    else:
        format_map = {
            ".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG",
            ".gif": "GIF", ".webp": "WEBP", ".bmp": "BMP", ".tiff": "TIFF",
        }
        target_format = format_map.get(ext, "JPEG")

    # Resize the image
    if width or height:
        image = resize_image(image, width=width, height=height)

    # Handle format conversion
    image = convert_format(image, target_format)

    # Save resized image
    output_ext = f".{target_format.lower()}"
    if output_ext == ".jpeg":
        output_ext = ".jpg"
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}_resized{output_ext}")
    image.save(output_path, format=target_format, quality=85)

    response_data = {
        "file_id": file_id,
        "resized_url": f"/download/{file_id}_resized{output_ext}",
        "original_size": file_size,
        "new_dimensions": image.size,
    }

    # Generate thumbnail if requested
    if generate_thumb:
        thumb = generate_thumbnail(image)
        thumb = convert_format(thumb, target_format)
        thumb_path = os.path.join(OUTPUT_DIR, f"{file_id}_thumb{output_ext}")
        thumb.save(thumb_path, format=target_format, quality=75)
        response_data["thumbnail_url"] = f"/download/{file_id}_thumb{output_ext}"

    return response_data


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a processed image."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.post("/batch-resize")
async def batch_resize(
    files: list[UploadFile] = File(...),
    width: Optional[int] = None,
    height: Optional[int] = None,
):
    """Resize multiple images at once."""
    results = []
    for file in files:
        contents = await file.read()
        ext = validate_file(file.filename, len(contents))
        file_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
        with open(input_path, "wb") as f:
            f.write(contents)

        image = Image.open(input_path)
        if width or height:
            image = resize_image(image, width=width, height=height)
        output_path = os.path.join(OUTPUT_DIR, f"{file_id}_resized{ext}")
        image.save(output_path, quality=85)
        results.append({
            "original_name": file.filename,
            "file_id": file_id,
            "resized_url": f"/download/{file_id}_resized{ext}",
            "dimensions": image.size,
        })

    return {"results": results}
