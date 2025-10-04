from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    Request,
    Response,
    Form,
)
from app.utils.dependencies import db_dependency
from app import services, schemas
from app.config import settings
import os
from fastapi.responses import StreamingResponse
from typing import List, Optional
from app.utils.dependencies import get_current_active_user, get_current_admin_user
from app.utils.files import (
    ALLOWED_VIDEO_MIME,
    ALLOWED_IMAGE_MIME,
    DEFAULT_MAX_VIDEO_SIZE,
    make_safe_filename,
    save_upload_file_stream,
)

router = APIRouter(prefix="/api/v1/movies", tags=["movies"])


@router.get("/", response_model=List[schemas.MovieOut])
def list_movies(
    db: db_dependency,
    skip: int = 0,
    limit: int = 50,
    _u=Depends(get_current_active_user),
):
    movies = services.list_movies(db, skip=skip, limit=limit)
    return movies


@router.get("/{movie_id}", response_model=schemas.MovieOut)
def get_movie(movie_id: int, db: db_dependency, _u=Depends(get_current_active_user)):
    movie = services.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Not found")
    return movie


@router.post(
    "/upload", response_model=schemas.MovieOut, status_code=status.HTTP_201_CREATED
)
def upload_movie(
    db: db_dependency,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    genre_id: Optional[int] = Form(None),
    language: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    file: UploadFile = File(...),
    poster: Optional[UploadFile] = File(None),
    admin=Depends(get_current_admin_user),
):
    """
    Upload a movie file + optional poster.
    Validates MIME type and size before saving.
    """
    # validate video content-type
    if file.content_type not in ALLOWED_VIDEO_MIME:
        raise HTTPException(
            status_code=400, detail=f"Invalid video content-type: {file.content_type}"
        )

    # allow override of max size via settings (env) if you want
    max_video_size = getattr(settings, "MAX_VIDEO_UPLOAD_BYTES", DEFAULT_MAX_VIDEO_SIZE)

    media_dir = settings.MEDIA_DIR
    movies_dir = os.path.join(media_dir, "movies")
    posters_dir = os.path.join(media_dir, "posters")
    os.makedirs(movies_dir, exist_ok=True)
    os.makedirs(posters_dir, exist_ok=True)

    # safe filenames
    safe_video_name = make_safe_filename(file.filename)
    video_rel_path = os.path.join("movies", safe_video_name)
    video_full_path = os.path.join(media_dir, video_rel_path)

    try:
        save_upload_file_stream(file, video_full_path, max_bytes=max_video_size)
    except ValueError:
        raise HTTPException(status_code=413, detail="Video file too large")
    except Exception as exc:
        # unexpected error while saving
        raise HTTPException(status_code=500, detail=f"Failed to save video: {exc}")

    poster_rel_path = None
    if poster:
        if poster.content_type not in ALLOWED_IMAGE_MIME:
            # cleanup video file we just wrote
            try:
                os.remove(video_full_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=400,
                detail=f"Invalid poster content-type: {poster.content_type}",
            )
        safe_poster_name = make_safe_filename(poster.filename)
        poster_rel_path = os.path.join("posters", safe_poster_name)
        poster_full_path = os.path.join(media_dir, poster_rel_path)
        try:
            # smaller poster size limit (e.g., 5 MiB)
            save_upload_file_stream(poster, poster_full_path, max_bytes=5 * 1024 * 1024)
        except ValueError:
            # cleanup video file
            try:
                os.remove(video_full_path)
            except Exception:
                pass
            raise HTTPException(status_code=413, detail="Poster file too large")
        except Exception as exc:
            try:
                os.remove(video_full_path)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to save poster: {exc}")

    movie = services.create_movie(
        db,
        title=title,
        description=description,
        genre_id=genre_id,
        language=language,
        duration=duration,
        file_path=video_rel_path,
        poster_path=poster_rel_path,
    )
    return movie


@router.get("/{movie_id}/stream")
def stream_movie(
    movie_id: int,
    request: Request,
    db: db_dependency,
    _u=Depends(get_current_active_user),
):
    movie = services.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Not found")
    media_root = settings.MEDIA_DIR
    path = os.path.join(media_root, movie.file_path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(path)
    range_header = request.headers.get("range")

    def iter_file(start: int = 0, end: int = None, chunk_size: int = 1024 * 1024):
        with open(path, "rb") as f:
            f.seek(start)
            remaining = (end - start + 1) if end is not None else None
            while True:
                read_size = (
                    chunk_size if remaining is None else min(chunk_size, remaining)
                )
                chunk = f.read(read_size)
                if not chunk:
                    break
                yield chunk
                if remaining is not None:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break

    if range_header:
        # parse "bytes=start-end"
        try:
            _, range_val = range_header.split("=")
            start_str, end_str = range_val.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Range header")
        if start >= file_size:
            return Response(status_code=416)
        resp = StreamingResponse(iter_file(start, end), status_code=206)
        resp.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Content-Length"] = str(end - start + 1)
        resp.headers["Content-Type"] = "video/mp4"
    else:
        resp = StreamingResponse(iter_file(0, file_size - 1), media_type="video/mp4")
        resp.headers["Content-Length"] = str(file_size)

    # increment view count
    services.increment_view_count(db, movie)
    return resp
