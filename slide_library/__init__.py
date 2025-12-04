"""
Slide Library Package

Provides slide library functionality for ingestion, retrieval, and planning.
"""

from .schemas import (
    SlideLibraryMetadata,
    SlideMetadata,
    StorageReference,
    PresentationPlan,
    SlideOutlineItem,
    SlideRetrievalResult
)
from .ingestion import SlideIngestionService
from .planner import SlidePlannerAgent
from .retrieval import SlideRetrievalService
from .storage import SlideStorageAdapter

__all__ = [
    "SlideLibraryMetadata",
    "SlideMetadata",
    "StorageReference",
    "PresentationPlan",
    "SlideOutlineItem",
    "SlideRetrievalResult",
    "SlideStorageAdapter",
    "SlideIngestionService",
    "SlideRetrievalService",
    "SlidePlannerAgent",
]
