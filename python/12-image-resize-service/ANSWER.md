# Answer: Image Resize Service

## Bug 1: Decompression Bomb (No Pixel Limit)

The code never sets `PIL.Image.MAX_IMAGE_PIXELS` and never checks image dimensions before opening. PIL's default limit is quite high, and with a 50MB file size cap, a carefully crafted image (e.g., a highly compressed 100000x100000 pixel image) can decompress to consume gigabytes of RAM, causing denial of service.

**Fix:** Set `PIL.Image.MAX_IMAGE_PIXELS` to a reasonable value (e.g., 25 million pixels) and/or check dimensions after opening before proceeding with resize operations.

```python
PIL.Image.MAX_IMAGE_PIXELS = 25_000_000  # ~5000x5000
```

## Bug 2: EXIF Data Preserved (Leaks GPS Coordinates)

When the image is resized and saved, EXIF metadata is preserved by default. This means photos uploaded by users retain GPS coordinates, camera serial numbers, timestamps, and other sensitive metadata. This is a serious privacy issue for any user-facing image service.

**Fix:** Strip EXIF data before saving:

```python
from PIL.ExifTags import Base as ExifBase

# Strip all EXIF data
image_data = list(image.getdata())
clean_image = Image.new(image.mode, image.size)
clean_image.putdata(image_data)
```

Or use the `exif` parameter when saving: `image.save(path, exif=b"")` (for formats that support it).

## Bug 3: No Format Validation Beyond Extension

The `validate_file` function only checks the file extension (e.g., `.jpg`, `.png`). It never verifies the actual file content. An attacker could rename a `.exe`, `.html`, or `.svg` file to `.jpg` and it would pass validation. While `Image.open()` may fail on truly invalid images, specially crafted files (like SVGs with embedded scripts or polyglot files) could cause unexpected behavior.

**Fix:** After opening the image, verify `image.format` matches the expected format. Also use magic bytes / file signatures to validate before opening:

```python
import imghdr
actual_type = imghdr.what(input_path)
if actual_type not in ("jpeg", "png", "gif", "webp", "bmp", "tiff"):
    raise HTTPException(status_code=400, detail="Invalid image content")
```

## Bug 4: Synchronous Processing Blocks Event Loop

The endpoint is declared as `async def` but all PIL operations (`Image.open()`, `resize()`, `save()`, etc.) are CPU-bound synchronous calls. In an async FastAPI/uvicorn setup, these block the entire event loop, meaning no other requests can be served while an image is being processed. This is especially bad for the `batch-resize` endpoint which processes multiple images sequentially.

**Fix:** Run CPU-bound operations in a thread pool:

```python
from fastapi.concurrency import run_in_threadpool

image = await run_in_threadpool(Image.open, input_path)
resized = await run_in_threadpool(resize_image, image, width, height)
```

Or use `asyncio.to_thread()` in Python 3.9+.

## Bug 5: Original Uploaded File Not Cleaned Up

The uploaded file is saved to `UPLOAD_DIR` (e.g., `/tmp/uploads/{file_id}.jpg`) but is never deleted after the image is processed. Over time, this accumulates disk usage. With a 50MB max file size and no cleanup, an attacker could fill up the disk by repeatedly uploading large files.

**Fix:** Delete the input file after processing is complete:

```python
os.remove(input_path)
```

Or use a context manager / `try/finally` to ensure cleanup even on errors.
