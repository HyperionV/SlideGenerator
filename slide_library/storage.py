"""
Slide Library Storage Adapter

Wraps rag_engine storage services (MongoDB, S3, Qdrant) for slide library operations.
Provides atomic storage with rollback on failure.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from .schemas import SlideLibraryMetadata, StorageReference

# Import rag_engine services
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from .rag_engine.services.storage_service import get_mongo_service, get_s3_service
from .rag_engine.services.vector_store_service import get_qdrant_service

logger = logging.getLogger(__name__)

# Database and collection names
MONGODB_DATABASE = "slide_library"
MONGODB_COLLECTION = "slides"
QDRANT_COLLECTION = "slide_library"


class SlideStorageAdapter:
    """
    Storage adapter for slide library.
    
    Wraps rag_engine services and provides atomic operations with rollback.
    All slides are stored in a separate 'slide_library' database to avoid
    contaminating the rag_engine database.
    """
    
    def __init__(self):
        """Initialize storage adapter with rag_engine services."""
        self.mongo = get_mongo_service()
        self.s3 = get_s3_service()
        self.qdrant = get_qdrant_service()
        
        self.database_name = MONGODB_DATABASE
        self.collection_name = MONGODB_COLLECTION
        self.qdrant_collection = QDRANT_COLLECTION
        
        print(f"SlideStorageAdapter initialized (database: {self.database_name})")
    
    async def initialize(self):
        """
        Initialize all storage backends.
        
        Must be called before using the adapter.
        """
        # Initialize MongoDB
        await self.mongo.initialize()
        
        # Initialize S3
        await self.s3.initialize()
        
        # Qdrant client is already initialized in __init__
        # Ensure Qdrant collection exists
        await self._ensure_qdrant_collection()
        
        print("All storage backends initialized")
    
    async def _ensure_qdrant_collection(self):
        """Ensure Qdrant collection exists with correct configuration."""
        try:
            # Check if collection exists
            collections = await self.qdrant.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.qdrant_collection not in collection_names:
                # Create collection with Voyage embedding dimension (1024)
                from qdrant_client.models import Distance, VectorParams
                
                await self.qdrant.client.create_collection(
                    collection_name=self.qdrant_collection,
                    vectors_config=VectorParams(
                        size=1024,  # Voyage embedding dimension
                        distance=Distance.COSINE
                    )
                )
                print(f"Created Qdrant collection: {self.qdrant_collection}")
            else:
                print(f"Qdrant collection already exists: {self.qdrant_collection}")
        except Exception as e:
            print(f"Failed to ensure Qdrant collection: {e}")
            raise
    
    async def store_slide(
        self,
        slide_pptx_path: Path,
        metadata: SlideLibraryMetadata,
        embedding: list[float]
    ) -> StorageReference:
        """
        Store a slide atomically across S3, MongoDB, and Qdrant.
        
        If any step fails, all changes are rolled back.
        
        Args:
            slide_pptx_path: Path to single-slide PPTX file
            metadata: Slide metadata
            embedding: 1024-dim Voyage embedding vector
            
        Returns:
            StorageReference with S3 key, MongoDB ID, and Qdrant ID
            
        Raises:
            Exception: If storage fails (after rollback)
        """
        s3_key = None
        mongodb_id = None
        qdrant_id = None
        
        try:
            # Step 1: Upload to S3 (hash-based naming for deduplication)
            print(f"Uploading slide to S3: {slide_pptx_path.name}")
            s3_result = await self.s3.upload_file_with_hash(
                file_path=slide_pptx_path,
                original_name=slide_pptx_path.name
            )
            s3_key = s3_result["s3_key"]
            print(f"S3 upload successful: {s3_key}")
            
            # Step 2: Store metadata in MongoDB
            print(f"Storing metadata in MongoDB (database: {self.database_name})")
            mongo_doc = metadata.model_dump()
            mongo_doc["storage_ref"] = {
                "s3_key": s3_key,
                "mongodb_id": "",  # Will be filled after insert
                "qdrant_id": metadata.slide_id
            }
            
            # Insert into MongoDB
            collection = self.mongo.get_collection(
                self.collection_name,
                database_name=self.database_name
            )
            result = await collection.insert_one(mongo_doc)
            mongodb_id = str(result.inserted_id)
            
            # Update storage_ref with mongodb_id
            await collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"storage_ref.mongodb_id": mongodb_id}}
            )
            print(f"MongoDB insert successful: {mongodb_id}")
            
            # Step 3: Store in Qdrant
            print(f"Storing vector in Qdrant (collection: {self.qdrant_collection})")
            from qdrant_client.models import PointStruct
            
            point = PointStruct(
                id=metadata.slide_id,
                vector=embedding,
                payload={
                    "slide_id": metadata.slide_id,
                    "description": metadata.description,
                    "source_presentation": metadata.source_presentation,
                    "element_count": metadata.element_count
                }
            )
            
            await self.qdrant.client.upsert(
                collection_name=self.qdrant_collection,
                points=[point]
            )
            qdrant_id = metadata.slide_id
            print(f"Qdrant upsert successful: {qdrant_id}")
            
            # Create storage reference
            storage_ref = StorageReference(
                s3_key=s3_key,
                mongodb_id=mongodb_id,
                qdrant_id=qdrant_id
            )
            
            print(f"Slide stored successfully: {metadata.slide_id}")
            return storage_ref
            
        except Exception as e:
            print(f"Storage failed, rolling back: {e}")
            
            # Rollback: Delete what was created
            if qdrant_id:
                try:
                    await self.qdrant.client.delete(
                        collection_name=self.qdrant_collection,
                        points_selector=[qdrant_id]
                    )
                    print(f"Rolled back Qdrant: {qdrant_id}")
                except Exception as rollback_error:
                    print(f"Qdrant rollback failed: {rollback_error}")
            
            if mongodb_id:
                try:
                    await self.mongo.delete(
                        collection_name=self.collection_name,
                        query={"slide_id": metadata.slide_id},
                        database_name=self.database_name
                    )
                    print(f"Rolled back MongoDB: {mongodb_id}")
                except Exception as rollback_error:
                    print(f"MongoDB rollback failed: {rollback_error}")
            
            if s3_key:
                try:
                    await self.s3.delete_file(s3_key)
                    print(f"Rolled back S3: {s3_key}")
                except Exception as rollback_error:
                    print(f"S3 rollback failed: {rollback_error}")
            
            raise
    
    async def slide_exists_by_hash(self, file_hash: str) -> Optional[SlideLibraryMetadata]:
        """
        Check if a slide with the given file hash already exists.
        
        Args:
            file_hash: SHA256 hash of the slide file
            
        Returns:
            SlideLibraryMetadata if exists, None otherwise
        """
        doc = await self.mongo.read(
            collection_name=self.collection_name,
            query={"file_hash": file_hash},
            database_name=self.database_name
        )
        
        if doc:
            return SlideLibraryMetadata(**doc)
        return None
    
    async def get_slide_by_id(
        self,
        slide_id: str
    ) -> Tuple[SlideLibraryMetadata, Path]:
        """
        Retrieve a slide by ID.
        
        Args:
            slide_id: Slide UUID
            
        Returns:
            Tuple of (metadata, local_pptx_path)
            
        Raises:
            ValueError: If slide not found
        """
        # Fetch metadata from MongoDB
        doc = await self.mongo.read(
            collection_name=self.collection_name,
            query={"slide_id": slide_id},
            database_name=self.database_name
        )
        
        if not doc:
            raise ValueError(f"Slide not found: {slide_id}")
        
        # Convert to SlideLibraryMetadata
        metadata = SlideLibraryMetadata(**doc)
        
        # Download from S3
        s3_key = metadata.storage_ref.s3_key
        local_path = Path(f"temp/slides/{slide_id}.pptx")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        await self.s3.download_file(s3_key, local_path)
        
        print(f"Retrieved slide: {slide_id}")
        return metadata, local_path
    
    async def delete_slide(self, slide_id: str) -> bool:
        """
        Delete a slide from all storage backends.
        
        Args:
            slide_id: Slide UUID
            
        Returns:
            True if deleted, False if not found
        """
        # Get metadata first
        doc = await self.mongo.read(
            collection_name=self.collection_name,
            query={"slide_id": slide_id},
            database_name=self.database_name
        )
        
        if not doc:
            print(f"Slide not found for deletion: {slide_id}")
            return False
        
        metadata = SlideLibraryMetadata(**doc)
        
        # Delete from all backends
        try:
            # Delete from Qdrant
            await self.qdrant.client.delete(
                collection_name=self.qdrant_collection,
                points_selector=[slide_id]
            )
            
            # Delete from MongoDB
            await self.mongo.delete(
                collection_name=self.collection_name,
                query={"slide_id": slide_id},
                database_name=self.database_name
            )
            
            # Delete from S3
            await self.s3.delete_file(metadata.storage_ref.s3_key)
            
            print(f"Deleted slide: {slide_id}")
            return True
            
        except Exception as e:
            print(f"Failed to delete slide {slide_id}: {e}")
            raise
    
    async def close(self):
        """Close all storage connections."""
        await self.mongo.close()
        print("Storage connections closed")
