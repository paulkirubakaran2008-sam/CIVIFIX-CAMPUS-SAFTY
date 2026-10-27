from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = ""
    mongodb_db: str = "civicfix_campus"
    jwt_secret: str = "development-secret-change-me"
    frontend_origin: str = "http://localhost:5173"
    upload_dir: str = "uploads"

    # Real Gemini vision analysis (backend-only key). Leave gemini_api_key
    # blank to always use the transparent mock-analysis fallback.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 15.0

    # Optional persistent image storage (Cloudinary free tier). When these
    # are blank, images are written to the local uploads/ folder instead,
    # which does NOT survive a redeploy on platforms like Render.
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
