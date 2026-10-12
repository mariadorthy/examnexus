"""
Profile-image storage helper.

Responsibilities:
  - Validate an uploaded image (magic bytes, size).
  - Persist it under app/static/profile_images/ with a
    server-generated UUID filename.
  - Return the public URL that the app serves from /static.

No database access. No auth. Callers decide whether to attach
the returned URL to a Student row.
"""

import os
import uuid


# Flask's static_folder on this deployment is
# backend/app/static — confirmed via app.static_folder.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.abspath(
    os.path.join(_THIS_DIR, "..", "static")
)
PROFILE_IMAGE_DIR = os.path.join(STATIC_ROOT, "profile_images")

# Canonical extension per allowed image format.
ALLOWED_FORMATS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Authoritative size cap. Client-side checks are advisory only.
MAX_BYTES = 2 * 1024 * 1024


def detect_image_mimetype(file_bytes):
    """
    Return the MIME type inferred from magic bytes, or None.

    Never trusts the client-supplied Content-Type.
    """
    if not file_bytes:
        return None
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if (
        file_bytes.startswith(b"RIFF")
        and len(file_bytes) >= 12
        and file_bytes[8:12] == b"WEBP"
    ):
        return "image/webp"
    return None


def validate_image_bytes(file_bytes):
    """
    Return (mime, None) on success, or (None, message) on failure.
    """
    if not file_bytes:
        return None, "Uploaded file is empty."
    if len(file_bytes) > MAX_BYTES:
        return None, (
            f"Image is too large (max {MAX_BYTES // (1024 * 1024)} MB)."
        )
    mime = detect_image_mimetype(file_bytes)
    if mime is None:
        return None, "Unsupported format. Allowed: JPEG, PNG, WebP."
    return mime, None


def save_image_bytes(file_bytes, mime):
    """
    Persist validated image bytes and return the public URL.

    Assumes the bytes have already been validated with
    validate_image_bytes(). Caller must handle OSError.
    """
    ext = ALLOWED_FORMATS[mime]
    stored_name = f"{uuid.uuid4().hex}{ext}"

    os.makedirs(PROFILE_IMAGE_DIR, exist_ok=True)
    target_path = os.path.join(PROFILE_IMAGE_DIR, stored_name)

    with open(target_path, "wb") as fh:
        fh.write(file_bytes)

    return f"/static/profile_images/{stored_name}"


def save_profile_image(file_storage):
    """
    Convenience wrapper around validate + save for a Flask
    FileStorage (single-file upload).

    Returns:
      {"success": True, "url": "..."}
      {"success": False, "message": "..."}
    """
    if file_storage is None:
        return {"success": False, "message": "No file provided."}

    try:
        file_bytes = file_storage.read()
    except Exception:
        return {
            "success": False,
            "message": "Could not read the uploaded file.",
        }

    mime, error = validate_image_bytes(file_bytes)
    if error:
        return {"success": False, "message": error}

    try:
        url = save_image_bytes(file_bytes, mime)
    except OSError as exc:
        return {
            "success": False,
            "message": f"Could not store the image: {exc}",
        }

    return {"success": True, "url": url}


def delete_profile_image(url):
    """
    Best-effort delete of a stored profile image.

    Only touches files whose URL starts with our own prefix and
    whose name contains no path separators. Never raises.
    """
    if not url:
        return

    prefix = "/static/profile_images/"
    if not url.startswith(prefix):
        return

    name = url[len(prefix):]

    if "/" in name or "\\" in name or ".." in name:
        return

    target_path = os.path.join(PROFILE_IMAGE_DIR, name)

    try:
        if os.path.isfile(target_path):
            os.remove(target_path)
    except OSError:
        pass