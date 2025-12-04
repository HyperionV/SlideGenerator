"""
Slide Library Retrieval Service

Simple, direct retrieval for slides using:
1. Voyage-3-large for embedding
2. Qdrant for vector search
3. Voyage rerank-2.5 for reranking
4. MongoDB for metadata
"""

import logging
from typing import List, Tuple, Optional

from .schemas import SlideLibraryMetadata
from .storage import SlideStorageAdapter
from slide_library.rag_engine.models.voyage.runner import voyage_embed, voyage_rerank

logger = logging.getLogger(__name__)


class SlideRetrievalService:
    """
    Simplified retrieval service for slide library.
    
    Flow:
    1. Embed query with voyage-3-large
    2. Vector search in Qdrant (slide_library collection)
    3. Rerank with voyage rerank-2.5
    4. Fetch metadata from MongoDB
    """
    
    def __init__(self, storage: SlideStorageAdapter):
        """
        Initialize retrieval service.
        
        Args:
            storage: Storage adapter for slide library
        """
        self.storage = storage
        self.qdrant = storage.qdrant
        self.mongo = storage.mongo
        self.collection_name = storage.qdrant_collection
        self.database_name = storage.database_name
        self.mongo_collection = storage.collection_name
        
        print(f"SlideRetrievalService initialized (collection: {self.collection_name})")
    
    async def search_slides(
        self,
        query: str,
        limit: int = 5,
        retrieval_limit: int = 20
    ) -> List[Tuple[SlideLibraryMetadata, float]]:
        """
        Search for slides matching the query.
        
        Args:
            query: Search query (natural language)
            limit: Maximum number of results to return
            retrieval_limit: Number of candidates to retrieve before reranking
            
        Returns:
            List of (SlideLibraryMetadata, relevance_score) tuples, sorted by score
        """
        print(f"Searching slides: '{query}' (limit: {limit})")
        
        try:
            # Step 1: Embed query with voyage-3-large
            query_embedding = await voyage_embed(
                content=[query],
                input_type="query",
                model="voyage-3-large"
            )
            query_vector = query_embedding[0]
            print(f"Query embedded: {len(query_vector)} dimensions")
            
            # Step 2: Vector search in Qdrant
            results = await self.qdrant.query(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=retrieval_limit
            )
            
            if not results:
                print(f"No slides found for query: '{query}'")
                return []
            
            print(f"Retrieved {len(results)} candidates from Qdrant")
            
            # Step 3: Extract slide_ids and descriptions for reranking
            slide_data = []
            for result in results:
                payload = result.get('payload', {})
                slide_id = payload.get('slide_id')
                description = payload.get('description', '')
                
                if slide_id and description:
                    slide_data.append({
                        'slide_id': slide_id,
                        'description': description,
                        'vector_score': result.get('score', 0.0)
                    })
            
            if not slide_data:
                print("No valid slide data found in results")
                return []
            
            # Step 4: Rerank with voyage rerank-2.5
            descriptions = [item['description'] for item in slide_data]
            rerank_results = await voyage_rerank(
                query=query,
                documents=descriptions,
                top_k=min(limit, len(descriptions))
            )
            
            print(f"Reranked to top {len(rerank_results)} results")
            
            # Step 5: Fetch metadata from MongoDB for top results
            final_results = []
            for rerank_result in rerank_results:
                index = rerank_result['index']
                relevance_score = rerank_result['relevance_score']
                slide_id = slide_data[index]['slide_id']
                
                # Fetch full metadata from MongoDB
                metadata_doc = await self.mongo.read(
                    collection_name=self.mongo_collection,
                    query={"slide_id": slide_id},
                    database_name=self.database_name
                )
                
                if not metadata_doc:
                    print(f"Warning: Metadata not found for slide_id: {slide_id}")
                    continue
                
                # Convert to SlideLibraryMetadata
                metadata = SlideLibraryMetadata(**metadata_doc)
                final_results.append((metadata, relevance_score))
            
            print(f"✅ Found {len(final_results)} slides")
            return final_results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            raise
    
    async def search_slides_simple(
        self,
        query: str,
        limit: int = 5
    ) -> List[SlideLibraryMetadata]:
        """
        Simplified search that returns just metadata (no scores).
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of SlideLibraryMetadata
        """
        results = await self.search_slides(query, limit)
        return [metadata for metadata, _ in results]
    
    async def get_slide_by_description(
        self,
        description: str
    ) -> Optional[SlideLibraryMetadata]:
        """
        Find a single slide matching the description.
        
        Args:
            description: Description to match
            
        Returns:
            SlideLibraryMetadata or None if not found
        """
        results = await self.search_slides_simple(description, limit=1)
        return results[0] if results else None
