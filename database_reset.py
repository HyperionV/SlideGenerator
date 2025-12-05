"""
Database Reset Script

Clears all data from:
- MongoDB database:
  - slide_library database (slides collection)
- S3 bucket (only files referenced in MongoDB slide collection)
- Qdrant vector database (slide_library collection)

Usage:
    python database_reset.py
"""

import asyncio
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

from core.storage import MONGODB_DATABASE, MONGODB_COLLECTION, QDRANT_COLLECTION
from storage import get_mongo_service, get_s3_service, get_qdrant_service

# Files Registry constants
MONGODB_DATABASE_FILES_REGISTRY = "files-registry"
MONGODB_COLLECTION_FILES = "files"


async def clear_mongodb():
    """Clear all MongoDB databases and collections."""
    print("\n=== Clearing MongoDB ===")
    mongo = get_mongo_service()
    
    # Access MongoDB client directly for multi-database operations
    if not mongo._initialized:
        await mongo.initialize()
    
    client = mongo.client
    
    # Clear slide_library database collection
    print(f"\nClearing '{MONGODB_DATABASE}' database:")
    slide_db = client[MONGODB_DATABASE]
    try:
        collection = slide_db[MONGODB_COLLECTION]
        result = await collection.delete_many({})
        print(f"  Deleted {result.deleted_count} documents from '{MONGODB_DATABASE}.{MONGODB_COLLECTION}'")
    except Exception as e:
        print(f"  Error clearing '{MONGODB_DATABASE}.{MONGODB_COLLECTION}': {e}")
    
    print("\nMongoDB cleared successfully")


async def clear_s3():
    """Clear S3 objects that are referenced in the MongoDB slide collection."""
    print("\n=== Clearing S3 (slide library files only) ===")
    mongo = get_mongo_service()
    s3 = get_s3_service()
    
    if not mongo._initialized:
        await mongo.initialize()
    
    try:
        # Get all S3 keys from MongoDB collection
        client = mongo.client
        slide_db = client[MONGODB_DATABASE]
        collection = slide_db[MONGODB_COLLECTION]
        
        # Query all documents and extract S3 keys
        cursor = collection.find({}, {"storage_ref.s3_key": 1})
        s3_keys = []
        async for doc in cursor:
            if "storage_ref" in doc and "s3_key" in doc["storage_ref"]:
                s3_key = doc["storage_ref"]["s3_key"]
                if s3_key:  # Only add non-empty keys
                    s3_keys.append(s3_key)
        
        if not s3_keys:
            print("No S3 files found in MongoDB collection")
            return
        
        print(f"Found {len(s3_keys)} S3 files to delete")
        
        # Delete each S3 file
        deleted_count = 0
        failed_count = 0
        for s3_key in s3_keys:
            try:
                success = await s3.delete_file(s3_key)
                if success:
                    deleted_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Failed to delete {s3_key}: {e}")
                failed_count += 1
        
        print(f"S3 cleared: {deleted_count} deleted, {failed_count} failed")
    except Exception as e:
        print(f"Error clearing S3: {e}")
        raise


async def clear_qdrant():
    """Clear slide library Qdrant collection only."""
    print("\n=== Clearing Qdrant slide library collection ===")
    qdrant = get_qdrant_service()
    try:
        await qdrant.deleteCollection(QDRANT_COLLECTION)
        print(f"Deleted Qdrant collection '{QDRANT_COLLECTION}'")
    except Exception as e:
        print(f"Error deleting Qdrant collection '{QDRANT_COLLECTION}': {e}")


async def main():
    """Main reset function."""
    print("=" * 50)
    print("DATABASE RESET - This will delete ALL data!")
    print("=" * 50)
    
    # Confirm before proceeding
    confirmation = input("\nAre you sure you want to continue? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Reset cancelled.")
        return
    
    # Initialize services
    try:
        mongo = get_mongo_service()
        await mongo.initialize()
        
        s3 = get_s3_service()
        await s3.initialize()
        
        qdrant = get_qdrant_service()

        await clear_s3()
        await clear_mongodb()
        await clear_qdrant()
        
        print("\n" + "=" * 50)
        print("DATABASE RESET COMPLETE")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError during reset: {e}")
        raise
    finally:
        # Close connections
        if 'mongo' in locals():
            await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())

