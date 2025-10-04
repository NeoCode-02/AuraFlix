import uuid
import os
from pathlib import Path


ALLOWED_VIDEO_MIME = {"video/mp4", "video/webm", "video/ogg"}
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}
# limit file size to 1 GiB by default (adjust as needed)
DEFAULT_MAX_VIDEO_SIZE = 1 * 1024 * 1024 * 1024


def make_safe_filename(filename: str) -> str:
    """
    Create a safe filename using UUID prefix and original extension.
    Keeps extension from original filename (if any), prevents collisions.
    """
    ext = Path(filename).suffix
    uid = uuid.uuid4().hex
    safe = f"{uid}{ext}"
    return safe


def save_upload_file_stream(
    upload_file, dest_path: str, max_bytes: int = None, chunk_size: int = 1024 * 1024
):
    """
    Stream-write the UploadFile to disk in chunked mode and validate file size.
    upload_file: starlette UploadFile
    dest_path: filesystem path to write to
    max_bytes: optional maximum bytes allowed (raise ValueError if exceeded)
    """
    total = 0
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as out_file:
        while True:
            chunk = upload_file.file.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                out_file.close()
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
                raise ValueError("Uploaded file is too large")
    try:
        upload_file.file.seek(0)
    except Exception:
        pass
    return total
