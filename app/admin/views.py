from typing import ClassVar
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.fields import FileField, ImageField
from fastapi import HTTPException
from app.config import settings


class UserAdminView(ModelView):
    fields: ClassVar[list[str]] = [
        "id",
        "email",
        "first_name",
        "last_name",
        "hashed_password",
        "is_active",
        "is_verified",
        "is_admin",
        "created_at",
    ]
    exclude_fields_from_create: ClassVar[list[str]] = ["created_at"]
    exclude_fields_from_edit: ClassVar[list[str]] = ["created_at"]
    exclude_fields_from_list: ClassVar[list[str]] = ["hashed_password", "created_at"]
    export_fields: ClassVar[list[str]] = fields
    export_types: ClassVar[list[str]] = ["csv", "excel", "pdf", "print"]


class GenreAdminView(ModelView):
    fields: ClassVar[list[str]] = ["id", "name", "created_at"]
    exclude_fields_from_create: ClassVar[list[str]] = ["created_at"]
    exclude_fields_from_edit: ClassVar[list[str]] = ["created_at"]
    exclude_fields_from_list: ClassVar[list[str]] = ["created_at"]
    export_fields: ClassVar[list[str]] = fields
    export_types: ClassVar[list[str]] = ["csv", "excel", "pdf", "print"]


class MovieAdminView(ModelView):
    label = "Movies"
    icon = "fa fa-film"

    fields: ClassVar[list[str]] = [
        "id",
        "title",
        "description",
        "genre",
        "language",
        "duration",
        "file_path",
        "poster_path",
        "view_count",
        "release_date",
        "created_at",
    ]

    form_fields = [
        "title",
        "description",
        "genre",
        "language",
        "duration",
        FileField("file_path"),
        ImageField("poster_path"),
        "release_date",
    ]

    exclude_fields_from_create = ["created_at", "view_count"]
    exclude_fields_from_edit = ["created_at", "view_count"]
    exclude_fields_from_list = ["created_at"]
    export_fields = fields
    export_types = ["csv", "excel", "pdf", "print"]

    async def before_create(self, request, data, obj, session):
        if data.get("file_path") and settings.MAX_VIDEO_UPLOAD_BYTES:
            if obj.file_path and obj.file_path.size > settings.MAX_VIDEO_UPLOAD_BYTES:
                raise HTTPException(status_code=400, detail="Video file too large")

    async def before_edit(self, request, data, obj, session):
        await self.before_create(request, data, obj, session)
