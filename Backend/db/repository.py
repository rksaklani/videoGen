"""Database operations — works with MongoDB or falls back to in-memory."""
from datetime import datetime
from typing import Optional
from loguru import logger
from Backend.db import mongodb
from Backend.db.models import job_doc, avatar_doc, user_doc


class JobRepository:
    """CRUD operations for jobs."""

    async def create(self, job_id: str, user_id: str = "anonymous", **kwargs) -> dict:
        doc = job_doc(job_id=job_id, user_id=user_id, **kwargs)
        if mongodb.is_connected():
            await mongodb.db.jobs.insert_one(doc)
        return doc

    async def get(self, job_id: str) -> Optional[dict]:
        if mongodb.is_connected():
            return await mongodb.db.jobs.find_one({"job_id": job_id}, {"_id": 0})
        return None

    async def update(self, job_id: str, **fields):
        if fields.get("status") == "completed":
            fields["completed_at"] = datetime.utcnow()
        if mongodb.is_connected():
            await mongodb.db.jobs.update_one({"job_id": job_id}, {"$set": fields})

    async def list_by_user(self, user_id: str = "anonymous", limit: int = 20) -> list:
        if mongodb.is_connected():
            cursor = mongodb.db.jobs.find(
                {"user_id": user_id}, {"_id": 0}
            ).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        return []


class AvatarRepository:
    """CRUD operations for avatar profiles."""

    async def create(self, user_id: str, name: str, image_path: str, **kwargs) -> dict:
        doc = avatar_doc(user_id=user_id, name=name, image_path=image_path, **kwargs)
        if mongodb.is_connected():
            result = await mongodb.db.avatars.insert_one(doc)
            doc["id"] = str(result.inserted_id)
        return doc

    async def get(self, avatar_id: str) -> Optional[dict]:
        if mongodb.is_connected():
            from bson import ObjectId
            doc = await mongodb.db.avatars.find_one({"_id": ObjectId(avatar_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        return None

    async def list_by_user(self, user_id: str, limit: int = 50) -> list:
        if mongodb.is_connected():
            cursor = mongodb.db.avatars.find(
                {"user_id": user_id}, {"_id": 0}
            ).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        return []

    async def delete(self, avatar_id: str):
        if mongodb.is_connected():
            from bson import ObjectId
            await mongodb.db.avatars.delete_one({"_id": ObjectId(avatar_id)})


class UserRepository:
    """CRUD operations for users."""

    async def create(self, email: str, name: str, hashed_password: str) -> dict:
        doc = user_doc(email=email, name=name, hashed_password=hashed_password)
        if mongodb.is_connected():
            await mongodb.db.users.insert_one(doc)
        return doc

    async def get_by_email(self, email: str) -> Optional[dict]:
        if mongodb.is_connected():
            return await mongodb.db.users.find_one({"email": email}, {"_id": 0})
        return None

    async def increment_generation(self, email: str):
        if mongodb.is_connected():
            await mongodb.db.users.update_one(
                {"email": email}, {"$inc": {"generation_count": 1}})
