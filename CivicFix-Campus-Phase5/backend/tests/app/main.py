from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .repository import repository
from .routes import admin, auth, insights, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await repository.connect()
    except Exception:
        # A missing local MongoDB should not block the student prototype.
        repository.client = None
        repository.collection = None
    if repository.collection is None:
        # In-memory storage is inherently ephemeral -- start each app run
        # (including each test session) from a clean slate rather than
        # silently accumulating data across restarts/TestClient instances.
        repository.memory = []
    yield
    await repository.close()


app = FastAPI(title="CivicFix Campus API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[get_settings().frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Path(get_settings().upload_dir).mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=get_settings().upload_dir), name="uploads")
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(insights.router)


@app.get("/health")
async def health():
    return {"status": "ok", "storage": "mongodb" if repository.collection is not None else "memory"}
