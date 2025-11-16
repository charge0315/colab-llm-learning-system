"""
MongoDB database configuration and initialization
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
import logging

from app.models import MusicAnalysis

logger = logging.getLogger(__name__)


class Database:
    client: Optional[AsyncIOMotorClient] = None

    @classmethod
    async def connect_db(cls, mongodb_url: str, database_name: str):
        """Initialize database connection"""
        try:
            cls.client = AsyncIOMotorClient(mongodb_url)

            # Initialize beanie with the MusicAnalysis document model
            await init_beanie(
                database=cls.client[database_name],
                document_models=[MusicAnalysis]
            )

            logger.info(f"Connected to MongoDB database: {database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def close_db(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")


# Dependency for FastAPI
async def get_database():
    """Dependency to get database instance"""
    return Database.client
