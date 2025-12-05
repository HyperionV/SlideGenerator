from typing import List, Dict, Any
import os
import voyageai

from dotenv import load_dotenv

load_dotenv(override=True)

vo = voyageai.AsyncClient(api_key=os.getenv("VOYAGE_API_KEY"))

async def voyage_embed(
    content: List[str], 
    input_type: str = "document", 
    model: str = "voyage-finance-2"
) -> List[List[float]]:
    response = await vo.embed(
        content,
        model=model,
        input_type=input_type,
    )
    return response.embeddings

async def voyage_rerank(query: str, documents: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Rerank documents using Voyage AI rerank-2.5 model.
    
    Args:
        query: Search query
        documents: List of document texts to rerank
        top_k: Number of top results to return
        
    Returns:
        List of reranked results with index and relevance_score
    """
    if not documents:
        return []
    
    response = await vo.rerank(
        query=query,
        documents=documents,
        model="rerank-2.5",
        top_k=top_k
    )
    
    return [
        {
            "index": result.index,
            "relevance_score": result.relevance_score
        }
        for result in response.results
    ]