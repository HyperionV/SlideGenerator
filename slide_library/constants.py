"""
Constants for RAG Engine

Defines collection names and constants used across the RAG engine.
This prevents naming mismatches and confusion between different services.
"""

# MongoDB Collection Names
MONGODB_COLLECTION_PARENT_CHUNKS = "parent_chunks"  # Stores parent chunk metadata (page-level chunks)
MONGODB_COLLECTION_CHUNKS = "chunks"  # Stores child chunk metadata (element-level chunks)
MONGODB_COLLECTION_FILE_MAPPINGS = "file_mappings"  # Stores S3 file hash mappings

MONGODB_DATABASE_RAG_ENGINE = "rag_engine"

# Files Registry Database
MONGODB_DATABASE_FILES_REGISTRY = "files-registry"  # Database for central file registry
MONGODB_COLLECTION_FILES = "files"  # Stores file content and metadata in registry

# Qdrant Collection Names
QDRANT_COLLECTION_DOCUMENTS = "documents"  # Default vector database collection for document embeddings

# List of all MongoDB collections (for reset scripts)
MONGODB_COLLECTIONS = [
    MONGODB_COLLECTION_PARENT_CHUNKS,
    MONGODB_COLLECTION_CHUNKS,
    MONGODB_COLLECTION_FILE_MAPPINGS,
]

