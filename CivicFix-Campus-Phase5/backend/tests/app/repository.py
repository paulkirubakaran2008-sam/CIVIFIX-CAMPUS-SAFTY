from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings


class ReportRepository:
    def __init__(self):
        self.memory: list[dict] = []
        self.client = None
        self.collection = None

    async def connect(self):
        settings = get_settings()
        if settings.mongodb_url:
            self.client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=1500)
            await self.client.admin.command("ping")
            self.collection = self.client[settings.mongodb_db].reports

    async def close(self):
        if self.client:
            self.client.close()

    async def create(self, data: dict) -> dict:
        record = {**data, "id": str(uuid4()), "report_id": f"CF-{str(uuid4().int)[-6:]}", "status": "AI Verified", "support_count": 0, "created_at": datetime.now(UTC)}
        if self.collection is not None:
            await self.collection.insert_one(record.copy())
        else:
            self.memory.append(record)
        return record

    async def for_user(self, campus_id: str, user_id: str, is_admin: bool = False) -> list[dict]:
        """Campus isolation is enforced here, not in the frontend or the
        route handlers: every read path funnels through this method, and
        every query is scoped to campus_id. Admins see every report on
        their own campus; students only see their own reports."""
        if self.collection is not None:
            query = {"campus_id": campus_id} if is_admin else {"campus_id": campus_id, "user_id": user_id}
            return await self.collection.find(query, {"_id": 0}).sort("created_at", -1).to_list(length=100)
        if is_admin:
            reports = [r for r in self.memory if r["campus_id"] == campus_id]
        else:
            reports = [r for r in self.memory if r["campus_id"] == campus_id and r["user_id"] == user_id]
        return sorted(reports, key=lambda r: r["created_at"], reverse=True)

    async def get(self, report_id: str, campus_id: str, user_id: str, is_admin: bool = False) -> dict | None:
        if self.collection is not None:
            query = {"id": report_id, "campus_id": campus_id}
            if not is_admin:
                query["user_id"] = user_id
            return await self.collection.find_one(query, {"_id": 0})
        return next(
            (r for r in self.memory if r["id"] == report_id and r["campus_id"] == campus_id and (is_admin or r["user_id"] == user_id)),
            None,
        )

    async def apply_analysis(self, report_id: str, campus_id: str, analysis: dict) -> dict | None:
        if self.collection is not None:
            await self.collection.update_one({"id": report_id, "campus_id": campus_id}, {"$set": analysis})
            return await self.collection.find_one({"id": report_id, "campus_id": campus_id}, {"_id": 0})
        report = next((r for r in self.memory if r["id"] == report_id and r["campus_id"] == campus_id), None)
        if report:
            report.update(analysis)
        return report

    async def update(self, report_id: str, campus_id: str, changes: dict) -> dict | None:
        if self.collection is not None:
            await self.collection.update_one({"id": report_id, "campus_id": campus_id}, {"$set": changes})
            return await self.collection.find_one({"id": report_id, "campus_id": campus_id}, {"_id": 0})
        report = next((r for r in self.memory if r["id"] == report_id and r["campus_id"] == campus_id), None)
        if report:
            report.update(changes)
        return report


repository = ReportRepository()


def upload_path(filename: str) -> Path:
    folder = Path(get_settings().upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename
