import os
from starlette_admin.contrib.sqla import Admin
from app.admin.auth import JSONAuthProvider
from app.admin.views import UserAdminView, GenreAdminView, MovieAdminView
from app.models import User, Genre, Movie
from app.database import engine
from app.config import settings

os.makedirs(os.path.join(settings.MEDIA_DIR, "media"), exist_ok=True)

admin = Admin(
    engine,
    title="AuraFlix Admin Panel",
    base_url="/admin",
    auth_provider=JSONAuthProvider(login_path="/login", logout_path="/logout"),
    media_dir=os.path.join(settings.MEDIA_DIR, "media"),
)

admin.add_view(UserAdminView(User, icon="fa fa-user"))
admin.add_view(GenreAdminView(Genre, icon="fa fa-tags"))
admin.add_view(MovieAdminView(Movie, icon="fa fa-film"))
