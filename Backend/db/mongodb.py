"""MongoDB connection and collections."""
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

client: AsyncIOMotorClient = None
db = None


async def connect(uri: str = "mongodb://localhost:27017", db_name: str = "avatar_studio"):
    """Connect to MongoDB."""
    global client, db
    try:
        client = AsyncIOMotorClient(uri)
        db = client[db_name]
        # Test connection
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB: {db_name}")

        # Create indexes
        await db.jobs.create_index("job_id", unique=True)
        await db.jobs.create_index("created_at")
        await db.jobs.create_index("user_id")
        await db.avatars.create_index("user_id")
        await db.users.create_index("email", unique=True)
        logger.info("MongoDB indexes created")
    except Exception as e:
        logger.warning(f"MongoDB not available: {e}. Using in-memory fallback.")
        client = None
        db = None


async def disconnect():
    global client
    if client:
        client.close()
        logger.info("MongoDB disconnected")


def get_db():
    return db


def is_connected() -> bool:
    return db is not None
