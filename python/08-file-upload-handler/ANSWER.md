# Problem 17: File Upload Handler — Bugs

## Bug 1: Path Traversal via Filename (Security — Critical)

**Line:** `return storage_dir / filename` in `generate_storage_path`

The user-supplied `file.filename` is used directly to construct the file path. An attacker can upload a file named `../../etc/cron.d/malicious` or `../../../app/config.py` to write files anywhere on the filesystem the process has access to. The `Path` `/` operator does not sanitize directory traversal sequences.

**Fix:** Use `werkzeug.utils.secure_filename(filename)` or generate a random filename with `f"{uuid.uuid4()}{ext}"` instead of trusting user input.

---

## Bug 2: No File Size Limit (Security / Availability — High)

**Line:** `contents = await file.read()`

The entire file is read into memory with no size check. An attacker can upload a multi-gigabyte file to exhaust server memory and disk space, causing a denial of service. There is no `max_size` parameter, no chunked reading with a byte counter, and no FastAPI request body limit configured.

**Fix:** Read the file in chunks and track total bytes, raising a 413 error if the total exceeds a maximum (e.g., 10 MB). Also configure FastAPI/uvicorn with a maximum request body size.

---

## Bug 3: MIME Type Checked by Extension Only (Security — High)

**Line:** `ext = os.path.splitext(filename)[1].lower()` in `validate_file_type`

Validation only checks the file extension, not the actual file content. An attacker can upload a PHP webshell, executable, or malicious HTML file renamed with a `.jpg` extension. The `ALLOWED_MIME_TYPES` set is defined but never actually used anywhere in the code.

**Fix:** Inspect actual file content using `python-magic` (`magic.from_buffer(contents, mime=True)`) to verify the MIME type matches the extension. Use the already-defined `ALLOWED_MIME_TYPES` set for this check.

---

## Bug 4: Temp Files Never Cleaned Up on Failure (Reliability — Medium)

**Line:** The `shutil.move` try/except block

If `shutil.move` fails (or any other error occurs after writing to `temp_path`), the temporary file remains on disk and is never deleted. Over time, failed uploads will accumulate temp files, wasting disk space. There is no `finally` block or cleanup logic.

**Fix:** Add a `finally` block that removes the temp file if it still exists: `if temp_path.exists(): temp_path.unlink()`. Or use a context manager / `tempfile.NamedTemporaryFile` with automatic cleanup.

---

## Bug 5: No Authentication on Upload Endpoint (Security — Critical)

**Location:** `@app.post("/api/upload")` has no auth dependency

The upload endpoint has no authentication or authorization check. Any anonymous user can upload files to the server. This allows abuse for malware hosting, phishing content, or simply exhausting storage. The delete endpoint is similarly unprotected.

**Fix:** Add a FastAPI dependency for authentication, e.g., `current_user: User = Depends(get_current_user)`, and verify the user has upload permissions before processing the file.
