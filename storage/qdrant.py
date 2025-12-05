"""
Qdrant Service - Async wrapper for vector database operations.

Provides vector storage and search for slide library.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Global singleton
_qdrant_service_instance: Optional['QdrantService'] = None


def get_qdrant_service() -> 'QdrantService':
    """Get singleton instance of QdrantService."""
    global _qdrant_service_instance
    if _qdrant_service_instance is None:
        _qdrant_service_instance = QdrantService()
    return _qdrant_service_instance


class QdrantService:
    """
    Qdrant service for slide library vector operations.
    
    Handles vector storage and similarity search.
    """

    def __init__(self):
        """Initialize Qdrant async client."""
        qdrant_uri = os.getenv("QDRANT_URI")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if not qdrant_uri:
            raise ValueError("QDRANT_URI environment variable must be set")
        
        try:
            self.client = AsyncQdrantClient(
                url=qdrant_uri,
                api_key=qdrant_api_key
            )
            print(f"Qdrant async client initialized: {qdrant_uri}")
        except Exception as e:
            print(f"Qdrant initialization failed: {e}")
            raise

    async def query(
        self, 
        collection_name: str, 
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Similarity search query.
        
        Args:
            collection_name: Collection name
            query_vector: Query vector for similarity search
            limit: Max results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar vectors with scores
        """
        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return [
            {
                'id': result.id,
                'vector': result.vector,
                'payload': result.payload,
                'score': result.score
            }
            for result in results
        ]

    async def deleteCollection(self, name: str) -> bool:
        """
        Delete collection.
        
        Args:
            name: Collection name
            
        Returns:
            True if successful
        """
        await self.client.delete_collection(collection_name=name)
        return True