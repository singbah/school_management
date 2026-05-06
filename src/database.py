from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DATABASE_URL", None)
client = AsyncIOMotorClient(DB_URL)

db = client.SCHOOL_DB