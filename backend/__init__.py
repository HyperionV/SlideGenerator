"""
Slide Library Package

Provides slide library functionality for ingestion, retrieval, planning, and generation.
"""

# Core services
from slide_library.core import (
    SlideIngestionService,
    SlidePlannerAgent,
    SlideRetrievalService,
    SlideStorageAdapter,
    PresentationProcessor,
    process_presentation_flow,
)

# Unified orchestrator
from slide_library.orchestrator import (
    SlideLibraryOrchestrator,
)

# Schemas
from slide_library.utils.schemas import (
    SlideLibraryMetadata,
    SlideMetadata,
    StorageReference,
    PresentationPlan,
    SlideOutlineItem,
    SlideRetrievalResult,
)

# Storage services
from slide_library.storage import (
    MongoDBService,
    S3Service,
    QdrantService,
    get_mongo_service,
    get_s3_service,
    get_qdrant_service,
)

__all__ = [
    # Core services
    "SlideIngestionService",
    "SlidePlannerAgent",
    "SlideRetrievalService",
    "SlideStorageAdapter",
    "PresentationProcessor",
    "process_presentation_flow",
    # Orchestrators
    "SlideLibraryOrchestrator",
    # Schemas
    "SlideLibraryMetadata",
    "SlideMetadata",
    "StorageReference",
    "PresentationPlan",
    "SlideOutlineItem",
    "SlideRetrievalResult",
    # Storage services
    "MongoDBService",
    "S3Service",
    "QdrantService",
    "get_mongo_service",
    "get_s3_service",
    "get_qdrant_service",
]
