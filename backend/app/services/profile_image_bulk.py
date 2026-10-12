"""
Bulk profile-image upload helper.

Takes a ZIP archive where each entry's filename (without
extension) is a student_id. For every entry:

  - validate the image bytes (magic bytes, size)
  - look up the matching Student.student_id
  - save the image via profile_image.save_image_bytes
  - mark the student's row for update

The caller is responsible for committing the transaction.
This module never touches the DB session directly — it
receives a set of student_id → Student rows from the caller
so it stays testable and side-effect-free except for the
files it writes.

Returns a per-file report so the admin UI can show what
happened to each entry.
"""

import io
import os
import zipfile

from app.services.profile_image import (
    validate_image_bytes,
    save_image_bytes,
    delete_profile_image,
)


# Refuse archives larger than 20 MB. Bulk photo zips from a
# typical batch of a few hundred students fit well under this.
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024

# Refuse archives with more than this many entries — a defense
# against zip-bomb-style uploads.
MAX_ENTRIES = 1000

# Only accept these archive extensions. (An admin uploading
# photos will produce a .zip from Windows/macOS by default.)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _student_id_from_entry(name):
    """
    Extract the student_id from an archive entry name.

    The entry basename (stripped of its directory and
    extension) is the student_id. We refuse nested directories
    to keep the contract simple.
    """
    # Some zips include a top-level folder; take only the basename.
    base = os.path.basename(name)
    if not base:
        return None, "empty filename"

    stem, ext = os.path.splitext(base)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return None, f"unsupported extension '{ext}'"

    # Sanitize: student_id must be a plain token. No slashes,
    # no dots, no null bytes.
    if not stem or "/" in stem or "\\" in stem or ".." in stem:
        return None, "invalid student_id in filename"

    return stem, None


def process_bulk_zip(
    file_bytes,
    students_by_code,
):
    """
    Process a ZIP of images and return a structured report.

    Arguments:
      file_bytes       — raw bytes of the uploaded ZIP
      students_by_code — dict mapping student_id (str) to a
                         Student ORM instance. Provided by the
                         caller so this helper stays DB-free.

    Returns:
      {
        "success": bool,
        "message": str,
        "matched": int,        # entries whose student_id exists
        "saved": int,          # entries written to disk
        "skipped": [
            {"filename": "...", "reason": "..."},
            ...
        ],
        "updated_student_ids": [int, ...]  # pks to be committed
      }

    Files on disk are written as we go. The caller commits the
    DB transaction afterwards. If the commit fails, orphan
    files remain — that's acceptable; they're inert.
    """

    if not file_bytes:
        return {
            "success": False,
            "message": "Empty archive.",
            "matched": 0,
            "saved": 0,
            "skipped": [],
            "updated_student_ids": [],
        }

    if len(file_bytes) > MAX_ARCHIVE_BYTES:
        return {
            "success": False,
            "message": (
                f"Archive is too large (max "
                f"{MAX_ARCHIVE_BYTES // (1024 * 1024)} MB)."
            ),
            "matched": 0,
            "saved": 0,
            "skipped": [],
            "updated_student_ids": [],
        }

    try:
        zf = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile:
        return {
            "success": False,
            "message": "Uploaded file is not a valid ZIP archive.",
            "matched": 0,
            "saved": 0,
            "skipped": [],
            "updated_student_ids": [],
        }

    entries = [
        name for name in zf.namelist()
        if not name.endswith("/")
        and not os.path.basename(name).startswith(".")
        and os.path.basename(name) != ""  # skip directory entries
    ]

    if len(entries) > MAX_ENTRIES:
        return {
            "success": False,
            "message": (
                f"Archive contains more than {MAX_ENTRIES} entries."
            ),
            "matched": 0,
            "saved": 0,
            "skipped": [],
            "updated_student_ids": [],
        }

    matched = 0
    saved = 0
    skipped = []
    updated_student_ids = []

    for name in entries:
        student_code, error = _student_id_from_entry(name)
        if error:
            skipped.append({"filename": name, "reason": error})
            continue

        student = students_by_code.get(student_code)
        if student is None:
            skipped.append({
                "filename": name,
                "reason": f"no student with student_id '{student_code}'",
            })
            continue

        matched += 1

        try:
            with zf.open(name) as fh:
                img_bytes = fh.read()
        except Exception as exc:
            skipped.append({
                "filename": name,
                "reason": f"could not read entry: {exc}",
            })
            continue

        mime, error = validate_image_bytes(img_bytes)
        if error:
            skipped.append({"filename": name, "reason": error})
            continue

        try:
            new_url = save_image_bytes(img_bytes, mime)
        except OSError as exc:
            skipped.append({
                "filename": name,
                "reason": f"could not store image: {exc}",
            })
            continue

        # Best-effort delete of the previous image before
        # replacing the URL on the row. Do NOT commit here.
        if student.student_img:
            delete_profile_image(student.student_img)

        student.student_img = new_url
        updated_student_ids.append(student.id)
        saved += 1

    return {
        "success": True,
        "message": (
            f"Processed {len(entries)} entries — "
            f"{saved} saved, {len(skipped)} skipped."
        ),
        "matched": matched,
        "saved": saved,
        "skipped": skipped,
        "updated_student_ids": updated_student_ids,
    }