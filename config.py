from loguru import logger
import os
from pymongo import MongoClient
import hashlib

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_NAME = "tiktok_downloader"

# Collections
COLLECTION_STATS = "website_stats"
COLLECTION_NOTIFICATIONS = "notifications"
COLLECTION_ACTIVITY = "admin_activity"
COLLECTION_USERS = "admin_users"

# Admin credentials (in production, use environment variables)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_PASSWORD_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

# Initialize MongoDB
try:
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    logger.info("✅ Connected to MongoDB successfully")
    
    # Create indexes for better performance
    db[COLLECTION_STATS].create_index([("timestamp", -1)])
    db[COLLECTION_STATS].create_index([("page", 1)])
    db[COLLECTION_NOTIFICATIONS].create_index([("active", 1), ("timestamp", -1)])
    db[COLLECTION_ACTIVITY].create_index([("timestamp", -1)])
    logger.info("✅ Database indexes created successfully")
    
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")

    raise
