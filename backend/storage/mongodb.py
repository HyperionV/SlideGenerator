"""
MongoDB Service - Async wrapper for MongoDB operations.

Provides CRUD operations for slide library storage.
"""

import os
import logging
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Global singleton
_mongo_service_instance = None


def get_mongo_service() -> 'MongoDBService':
    """Get singleton instance of MongoDBService."""
    global _mongo_service_instance
    if _mongo_service_instance is None:
        _mongo_service_instance = MongoDBService()
    return _mongo_service_instance


class MongoDBService:
    """
    MongoDB service for slide library operations.
    
    Supports dynamic database access per operation.
    """

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self._initialized = False

    async def initialize(self):
        """Initialize MongoDB connection."""
        if self._initialized:
            print("MongoDB already initialized")
            return

        connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

        try:
            self.client = AsyncIOMotorClient(connection_string)
            self._initialized = True
            print(f"MongoDB initialized")
        except Exception as e:
            print(f"MongoDB initialization failed: {e}")
            raise

    def get_collection(self, collection_name: str, database_name: str = "slide_library") -> AsyncIOMotorCollection:
        """
        Get a collection reference from the specified database.

        Args:
            collection_name: Name of the collection
            database_name: Name of the database

        Returns:
            Collection reference
        """
        if not self._initialized or self.client is None:
            raise RuntimeError("MongoDB not initialized. Call await mongo_service.initialize() first.")

        db = self.client[database_name]
        return db[collection_name]

    async def read(self, collection_name: str, query: Dict[str, Any], database_name: str = "slide_library") -> Optional[Dict[str, Any]]:
        """
        Read a document from the specified collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            database_name: Name of the database

        Returns:
            Document or None if not found
        """
        collection = self.get_collection(collection_name, database_name)
        return await collection.find_one(query)

    async def delete(self, collection_name: str, query: Dict[str, Any], database_name: str = "slide_library") -> bool:
        """
        Delete documents from the specified collection.

        Args:
            collection_name: Name of the collection
            query: Query filter
            database_name: Name of the database

        Returns:
            True if deleted, False if not found
        """
        collection = self.get_collection(collection_name, database_name)
        result = await collection.delete_one(query)
        success = result.deleted_count > 0

        if success:
            print(f"Deleted document from {collection_name}")
        return success

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
