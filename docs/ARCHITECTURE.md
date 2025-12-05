# Slide Library Architecture - Design Document

**Status**: Updated - Ready for Implementation

**Date**: 2025-12-04

**Version**: 2.0 (Simplified Model)

---

## Executive Summary

The Slide Library feature transforms the slide generator from a template-based system into an intelligent, RAG-powered presentation composition engine. It enables:

1. **Ingestion**: Split presentations into single-slide units with rich metadata
2. **Storage**: Distributed storage across S3 (files), MongoDB (metadata), Qdrant (embeddings)
3. **Retrieval**: Pure semantic search for slides based on comprehensive descriptions
4. **Composition**: Dynamic assembly of presentations from retrieved slides

---

## Key Changes in v2.0

### ✅ Simplified Metadata Model

- **Removed**: `purpose` field → Replaced with comprehensive `description` field
- **Removed**: `tags` field → Not needed, description contains all context
- **Removed**: `layout_type` field → Encoded in description text
- **Removed**: `content_types` field → Encoded in description text
- **Changed**: `ingestion_date` → `last_updated` for better semantics

### ✅ Simplified Retrieval

- **Pure semantic search** on `description` field only
- **No hybrid filtering** - description contains all necessary context
- **No re-ranking** - Qdrant similarity scores are sufficient
- **No layout/content type filters** - all encoded in description

### ✅ Comprehensive Description Field

The `description` field now includes:

- Slide purpose/theme
- Content summary with key messages
- Visual structure and layout information
- Component types and positioning
- All context needed for retrieval

**Example**:

```
This slide presents Q4 financial performance with a focus on revenue growth.

Purpose: Communicate quarterly financial results to investors.

Content: Main title "Q4 2024 Financial Results", subtitle highlighting 25% YoY growth,
bar chart showing revenue progression from $8M to $10M over four quarters.

Structure: Title-content-chart layout with title at top (large, bold), descriptive text
middle-left, chart on right (40% width). Blue color scheme with clear axis labels.

Visual Elements: 1 title text, 2 body text blocks, 1 bar chart (CHART type).
```

---

## Current State Analysis

### Existing Components

| Component                  | File                  | Capabilities                                             | Reusability                                |
| -------------------------- | --------------------- | -------------------------------------------------------- | ------------------------------------------ |
| **Presentation Processor** | `slide_generation.py` | Complete pipeline: normalize → reason → generate → merge | ✅ High - extend for dynamic mode          |
| **Slide Loader/Copier**    | `load_and_merge.py`   | Load PPTX, copy slides between presentations (Spire)     | ✅ High - core functionality ready         |
| **Content Utilities**      | `utils.py`            | Normalization, extraction, table/chart handling          | ✅ High - leverage for metadata extraction |
| **Data Models**            | `schemas.py`          | SlideContent, ContentItem, PresentationMapping           | ✅ Medium - extend for library metadata    |
| **RAG Engine**             | `../rag_engine/`      | Ingest/retrieval pipelines, storage services             | ✅ High - wrap for slide-specific logic    |

### Existing Workflow (Fixed Mode)

```
User Template + Context
        ↓
    Normalize (utils.py)
        ↓
    Extract Structure (utils.py)
        ↓
    AI Reasoning (slide_generation.py)
        ↓
    Content Generation (slide_generation.py)
        ↓
    Apply Content (utils.py)
        ↓
    Final PPTX

```

---

## Proposed Architecture

### Module Structure

```
slide_library/
├── __init__.py                 # Public API exports
├── schemas.py                  # Slide library specific data models
├── ingestion.py                # SlideIngestionService
├── retrieval.py                # SlideRetrievalService
├── storage.py                  # SlideStorageAdapter (wraps rag_engine)
├── planner.py                  # SlidePlannerAgent (LLM-based planning)
└── orchestrator.py             # SlideCompositionOrchestrator

```

### Component Responsibilities

### 1. [**schemas.py**](http://schemas.py/) - Data Models

**New Models:**

```python
class SlideLibraryMetadata(BaseModel):
    """Extended metadata for library slides."""
    slide_id: str                           # Unique identifier (UUID)
    description: str                        # Comprehensive description (purpose + content + structure)
    dimensions: SlideMetadata               # Width, height
    element_count: int                      # Number of content elements
    storage_ref: StorageReference           # S3/MongoDB/Qdrant references
    source_presentation: str                # Original file name
    last_updated: datetime

class StorageReference(BaseModel):
    """Storage locations for a slide."""
    s3_key: str                             # S3 object key
    mongodb_id: str                         # MongoDB document ID
    qdrant_id: str                          # Qdrant point ID

class SlideOutlineItem(BaseModel):
    """Single slide specification from planner."""
    position: int                           # Order in final presentation
    description: str                        # What this slide should convey (detailed)
    content_guidelines: str                 # Specific content requirements

class PresentationPlan(BaseModel):
    """Complete presentation outline."""
    slides: List[SlideOutlineItem]
    overall_theme: str
    target_audience: str
    estimated_duration: int                 # Minutes

```

**Rationale**: Extend existing schemas rather than replace. `SlideContent` already has `purpose` field - we build on that foundation.

---

### 2. [**ingestion.py**](http://ingestion.py/) - Slide Ingestion Service

**Class: `SlideIngestionService`**

```python
class SlideIngestionService:
    """Handles splitting presentations and extracting metadata."""

    def __init__(self, storage_adapter: SlideStorageAdapter):
        self.storage = storage_adapter
        self.loader = PPTXLoader  # From load_and_merge.py

    async def ingest_presentation(
        self,
        pptx_path: str
    ) -> List[SlideLibraryMetadata]:
        """
        Complete ingestion pipeline.

        Steps:
        1. Load presentation
        2. For each slide:
           a. Extract to single-slide PPTX
           b. Normalize and extract metadata
           c. Generate comprehensive description (LLM)
           d. Store to S3/MongoDB/Qdrant

        Returns:
            List of metadata for ingested slides
        """

    async def _extract_single_slide(
        self,
        source_prs: Presentation,
        slide_index: int
    ) -> Path:
        """Extract slide to temporary single-slide PPTX."""
        # Use PPTXSlideManager.copy_slide

    async def _generate_slide_description(
        self,
        slide_pptx: Path,
        slide_content: SlideContent,
        source_name: str
    ) -> str:
        """
        Generate comprehensive description using LLM.

        The description includes:
        - Purpose/theme of the slide
        - Content summary (what information is presented)
        - Visual structure and layout
        - Component types and positioning
        - Any other relevant context

        Uses:
        - User notes if available (PRIORITY)
        - LLM generation with structured prompt
        - Content from normalize_presentation()
        """

```

**Key Design Decisions:**

1. **Single-slide PPTX storage**: Preserves all formatting, compatible with existing tools
2. **Description generation**: Use LLM with comprehensive prompt to generate rich descriptions
3. **User notes priority**: Check for user notes first before LLM generation
4. **Async processing**: Leverage existing async patterns from rag_engine

**Integration Points:**

- `load_and_merge.py`: PPTXLoader, PPTXSlideManager for slide extraction
- `utils.py`: normalize_presentation for content extraction
- `config.py`: vertexai_model for description generation
- `storage.py`: SlideStorageAdapter for persistence

---

### 3. [**retrieval.py**](http://retrieval.py/) - Slide Retrieval Service

**Class: `SlideRetrievalService`**

```python
class SlideRetrievalService:
    """Semantic search and retrieval for library slides."""

    def __init__(self, storage_adapter: SlideStorageAdapter):
        self.storage = storage_adapter

    async def search_slides(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.7
    ) -> List[Tuple[SlideLibraryMetadata, float]]:
        """
        Pure semantic search on description field.

        Steps:
        1. Embed query using Voyage
        2. Vector search in Qdrant
        3. Fetch metadata from MongoDB
        4. Return top-k with scores

        No filtering, no re-ranking - just pure semantic similarity.

        Returns:
            List of (metadata, relevance_score) tuples
        """

    async def get_slide_by_id(
        self,
        slide_id: str
    ) -> Tuple[SlideLibraryMetadata, Path]:
        """
        Retrieve specific slide by ID.

        Returns:
            (metadata, local_pptx_path)
        """



```

**Key Design Decisions:**

1. **Pure semantic search**: Description field contains all context (purpose, layout, content types)
2. **No filtering**: Qdrant's vector search is sufficient
3. **Caching**: Download slides to temp directory, cache for session
4. **Fallback strategy**: If no suitable slide found, return None (orchestrator handles fallback)

**Integration Points:**

- `rag_engine/pipelines/retrieval.py`: Use RetrievalPipeline for vector search
- `rag_engine/services/storage_service.py`: MongoDB and S3 access
- `storage.py`: Abstraction layer

---

### 4. [**storage.py**](http://storage.py/) - Storage Adapter

**Class: `SlideStorageAdapter`**

```python
class SlideStorageAdapter:
    """
    Abstraction layer for slide storage across S3, MongoDB, Qdrant.
    Wraps rag_engine services with slide-specific logic.
    """

    def __init__(
        self,
        collection_name: str = "slide_library",
        database_name: str = "slide_agent"
    ):
        self.mongo = get_mongo_service()
        self.s3 = get_s3_service()
        self.qdrant = get_qdrant_service()
        self.collection_name = collection_name
        self.database_name = database_name

    async def store_slide(
        self,
        slide_pptx: Path,
        metadata: SlideLibraryMetadata,
        embedding: List[float]
    ) -> StorageReference:
        """
        Store slide across all backends atomically.

        Steps:
        1. Upload PPTX to S3 (hash-based naming)
        2. Store metadata to MongoDB
        3. Store embedding to Qdrant
        4. Return storage references

        Rollback on failure.
        """

    async def retrieve_slide(
        self,
        slide_id: str
    ) -> Tuple[SlideLibraryMetadata, Path]:
        """
        Retrieve slide from storage.

        Steps:
        1. Fetch metadata from MongoDB
        2. Download PPTX from S3 to temp
        3. Return metadata + local path
        """

    async def delete_slide(self, slide_id: str) -> bool:
        """Delete slide from all backends."""

    async def update_metadata(
        self,
        slide_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update slide metadata in MongoDB."""

```

**Key Design Decisions:**

1. **Atomic operations**: Store/delete should be transactional (rollback on failure)
2. **Separate database**: Use `slide_agent` database in MongoDB (not `rag_engine`)
3. **Separate collection**: Use `slide_library` collection in Qdrant
4. **Hash-based S3 keys**: Leverage S3Service's hash-based naming for deduplication

**Integration Points:**

- `rag_engine/services/storage_service.py`: Direct usage of MongoDBService, S3Service
- `rag_engine/services/vector_store_service.py`: QdrantService for embeddings

---

### 5. [**planner.py**](http://planner.py/) - Slide Planner Agent

**Class: `SlidePlannerAgent`**

```python
class SlidePlannerAgent:
    """
    LLM-based agent for generating presentation outlines.
    Converts user intent into structured slide specifications.
    """

    async def generate_plan(
        self,
        user_context: str,
        user_prompt: str,
        num_slides: Optional[int] = None
    ) -> PresentationPlan:
        """
        Generate presentation plan from user input.

        LLM Prompt:
        - System: "You are a presentation architect..."
        - User: context + prompt
        - Output: JSON schema (PresentationPlan)

        Returns:
            Structured presentation plan
        """

    def _validate_plan(self, plan: PresentationPlan) -> bool:
        """Validate plan coherence and feasibility."""

```

**Key Design Decisions:**

1. **Structured output**: Use vertexai_model with JSON schema for consistent output
2. **Validation**: Check plan coherence (no duplicate purposes, logical flow)
3. **Flexibility**: Support both explicit slide count and auto-determination

**Integration Points:**

- `config.py`: vertexai_model for LLM calls
- `prompts.py`: Add SLIDE_PLANNING_PROMPT and schema

---

### 6. [**orchestrator.py**](http://orchestrator.py/) - Composition Orchestrator

**Class: `SlideCompositionOrchestrator`**

```python
class SlideCompositionOrchestrator:
    """
    Orchestrates dynamic presentation composition.
    Coordinates planning, retrieval, generation, and merging.
    """

    def __init__(
        self,
        planner: SlidePlannerAgent,
        retriever: SlideRetrievalService,
        processor: PresentationProcessor
    ):
        self.planner = planner
        self.retriever = retriever
        self.processor = processor

    async def compose_presentation(
        self,
        user_context: str,
        user_prompt: str,
        output_dir: str = "output"
    ) -> Dict[str, str]:
        """
        Complete dynamic composition pipeline.

        Steps:
        1. Generate presentation plan (planner)
        2. For each slide in plan:
           a. Retrieve suitable slide (retriever)
           b. If found: download and prepare
           c. If not found: use default template or skip
        3. Merge slides in order (load_and_merge)
        4. Generate content for merged presentation (processor)
        5. Return final PPTX

        Returns:
            Dict with output file paths
        """

    async def _retrieve_slide_for_outline(
        self,
        outline_item: SlideOutlineItem
    ) -> Optional[Path]:
        """
        Find best matching slide for outline item.

        Search strategy:
        1. Pure semantic search on description
        2. Return top match or None
        """

    async def _merge_slides_in_order(
        self,
        slide_paths: List[Path]
    ) -> Path:
        """
        Merge slides into single presentation.

        Uses:
        - PPTXSlideManager.copy_slide
        - Maintains order from plan
        """

    async def _generate_content_for_merged(
        self,
        merged_pptx: Path,
        plan: PresentationPlan,
        user_context: str
    ) -> Dict[str, str]:
        """
        Generate content for merged presentation.

        Uses:
        - PresentationProcessor.execute (existing pipeline)
        - Context enriched with plan information
        """

```

**Key Design Decisions:**

1. **Fallback strategy**: If no suitable slide found, use default template or skip (configurable)
2. **Order preservation**: Maintain slide order from plan
3. **Content coherence**: Pass entire plan to content generation for context
4. **Reuse existing pipeline**: Leverage PresentationProcessor for content generation

**Integration Points:**

- `planner.py`: SlidePlannerAgent
- `retrieval.py`: SlideRetrievalService
- `slide_generation.py`: PresentationProcessor
- `load_and_merge.py`: PPTXSlideManager for merging

---

## Extended Components

### 7. **slide_generation.py** - Extended Processor

**Modifications:**

```python
class PresentationProcessor:
    def __init__(
        self,
        pptx_path: str,
        user_input: str,
        documents: str = "",
        output_dir: str = "output",
        mode: str = "fixed"  # NEW: "fixed" or "dynamic"
    ):
        self.mode = mode
        # ... existing init

    async def execute(self) -> Dict[str, str]:
        """Route to appropriate execution mode."""
        if self.mode == "fixed":
            return await self._execute_fixed_mode()
        elif self.mode == "dynamic":
            return await self._execute_dynamic_mode()

    async def _execute_fixed_mode(self) -> Dict[str, str]:
        """Existing pipeline (current execute method)."""
        # Current implementation

    async def _execute_dynamic_mode(self) -> Dict[str, str]:
        """
        Dynamic mode using slide library.

        Delegates to SlideCompositionOrchestrator.
        """
        orchestrator = SlideCompositionOrchestrator(...)
        return await orchestrator.compose_presentation(...)

```

**Rationale**: Extend existing class rather than create new one. Maintains backward compatibility.

---

### 8. **load_and_merge.py** - Enhanced Merging

**New Method:**

```python
class PPTXSlideManager:
    @staticmethod
    def merge_presentations(
        slide_paths: List[Path],
        output_path: Path,
        copy_dimensions_from: Optional[Path] = None
    ) -> Path:
        """
        Merge multiple single-slide presentations into one.

        Args:
            slide_paths: Ordered list of single-slide PPTX files
            output_path: Where to save merged presentation
            copy_dimensions_from: Optional source for dimensions

        Returns:
            Path to merged presentation
        """
        # Create new presentation
        # For each slide_path:
        #   - Load source
        #   - Copy slide to target
        # Save and return

```

**Rationale**: Orchestration wrapper around existing `copy_slide` method.

---

## Workflows

### Ingestion Workflow

```
Input: Multi-slide PPTX
        ↓
    Load with PPTXLoader
        ↓
    For each slide:
        ↓
    Extract to single-slide PPTX (PPTXSlideManager)
        ↓
    Normalize content (utils.normalize_presentation)
        ↓
    Generate comprehensive description (LLM):
        - Check for user notes first (PRIORITY)
        - If no notes: generate with LLM
        - Include: purpose, content, structure, visual elements
        ↓
    Create SlideLibraryMetadata
        ↓
    Generate embedding from description (Voyage)
        ↓
    Store atomically:
        - PPTX → S3 (hash-based key)
        - Metadata → MongoDB (slide_agent.slide_library)
        - Embedding → Qdrant (slide_library collection)
        ↓
    Return List[SlideLibraryMetadata]

```

### Dynamic Generation Workflow

```
User Context + Prompt
        ↓
    Generate Plan (SlidePlannerAgent)
        ↓
    PresentationPlan (JSON)
        ↓
    For each SlideOutlineItem:
        ↓
    Search slides (pure semantic on description)
        - Embed outline item description
        - Vector search in Qdrant
        - Return top match
        ↓
    Retrieve top match or use fallback
        ↓
    Download slide PPTX from S3
        ↓
    Collect all slide paths
        ↓
    Merge slides (PPTXSlideManager.merge_presentations)
        ↓
    Merged PPTX (template for generation)
        ↓
    Generate content (PresentationProcessor - fixed mode)
        - Normalize
        - Extract structure
        - AI reasoning
        - Content generation
        - Apply content
        ↓
    Final PPTX

```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      INGESTION FLOW                         │
└─────────────────────────────────────────────────────────────┘

Multi-slide PPTX
       │
       ├──► SlideIngestionService
       │         │
       │         ├──► PPTXLoader (load_and_merge.py)
       │         │
       │         ├──► For each slide:
       │         │      │
       │         │      ├──► Extract (PPTXSlideManager)
       │         │      │
       │         │      ├──► Normalize (utils.py)
       │         │      │
       │         │      ├──► Generate description (LLM)
       │         │      │
       │
       │         │      │
       │         │      └──► Create metadata
       │         │
       │         └──► SlideStorageAdapter
       │                  │
       │                  ├──► S3Service (PPTX file)
       │                  │
       │                  ├──► MongoDBService (metadata)
       │                  │
       │                  └──► QdrantService (embedding)
       │
       └──► List[SlideLibraryMetadata]

┌─────────────────────────────────────────────────────────────┐
│                   DYNAMIC GENERATION FLOW                   │
└─────────────────────────────────────────────────────────────┘

User Context + Prompt
       │
       ├──► SlidePlannerAgent
       │         │
       │         └──► LLM (vertexai_model)
       │                  │
       │                  └──► PresentationPlan
       │
       ├──► SlideCompositionOrchestrator
       │         │
       │         ├──► For each SlideOutlineItem:
       │         │      │
       │         │      ├──► SlideRetrievalService
       │         │      │      │
       │         │      │      ├──► Embed query (Voyage)
       │         │      │      │
       │         │      │      ├──► Search Qdrant
       │         │      │      │
       │         │      │      ├──► Fetch metadata (MongoDB)
       │         │      │      │
       │
       │         │      │      │
       │         │      │      └──► Download from S3
       │         │      │
       │         │      └──► Slide PPTX path
       │         │
       │         ├──► PPTXSlideManager.merge_presentations
       │         │         │
       │         │         └──► Merged PPTX
       │         │
       │         └──► PresentationProcessor (fixed mode)
       │                  │
       │                  ├──► Normalize
       │                  │
       │                  ├──► AI Reasoning
       │                  │
       │                  ├──► Content Generation
       │                  │
       │                  └──► Apply Content
       │
       └──► Final PPTX

```

---

## Storage Schema

### MongoDB (Database: `slide_agent`, Collection: `slide_library`)

```json
{
  "_id": "ObjectId(...)",
  "slide_id": "uuid-string",
  "description": "This slide presents Q4 financial performance...\n\nPurpose: Communicate quarterly results...\n\nContent: Main title, subtitle, bar chart...\n\nStructure: Title-content-chart layout...",
  "dimensions": {
    "width": 1920,
    "height": 1080
  },
  "element_count": 3,
  "storage_ref": {
    "s3_key": "slides/abc123hash.pptx",
    "mongodb_id": "ObjectId(...)",
    "qdrant_id": "uuid-string"
  },
  "source_presentation": "Q4_2024_Earnings.pptx",
  "last_updated": "2025-12-04T11:00:00Z"
}
```

### Qdrant (Collection: `slide_library`)

```json
{
  "id": "uuid-string",
  "vector": [0.123, 0.456, ...],  // 1024-dim Voyage embedding of description
  "payload": {
    "slide_id": "uuid-string",
    "description": "This slide presents Q4 financial performance...",
    "source_presentation": "Q4_2024_Earnings.pptx"
  }
}

```

### S3 (Bucket: configured in rag_engine)

```
slides/
  ├── abc123hash.pptx  (single-slide PPTX)
  ├── def456hash.pptx
  └── ...

```

**Key**: Hash-based naming (SHA256 of file content) for automatic deduplication.

---

## API Design

### Public API (`slide_library/__init__.py`)

```python
from .ingestion import SlideIngestionService
from .retrieval import SlideRetrievalService
from .storage import SlideStorageAdapter
from .planner import SlidePlannerAgent
from .orchestrator import SlideCompositionOrchestrator
from .schemas import (
    SlideLibraryMetadata,
    StorageReference,
    SlideOutlineItem,
    PresentationPlan
)

__all__ = [
    "SlideIngestionService",
    "SlideRetrievalService",
    "SlideStorageAdapter",
    "SlidePlannerAgent",
    "SlideCompositionOrchestrator",
    "SlideLibraryMetadata",
    "StorageReference",
    "SlideOutlineItem",
    "PresentationPlan"
]
```

### Usage Examples

**Ingestion:**

```python
from slide_library import SlideIngestionService, SlideStorageAdapter

storage = SlideStorageAdapter()
ingestion = SlideIngestionService(storage)

metadata_list = await ingestion.ingest_presentation(
    pptx_path="presentations/Q4_Earnings.pptx",
    tags=["earnings", "financial"]
)

print(f"Ingested {len(metadata_list)} slides")

```

**Dynamic Generation:**

```python
from slide_generation import PresentationProcessor

processor = PresentationProcessor(
    pptx_path=None,  # Not needed in dynamic mode
    user_input="Create investor deck with company overview, market analysis, and financials",
    documents="Q4 earnings: revenue $10M, growth 25%...",
    mode="dynamic"
)

result = await processor.execute()
print(f"Generated: {result['generated_pptx']}")

```

**Manual Retrieval:**

```python
from slide_library import SlideRetrievalService, SlideStorageAdapter

storage = SlideStorageAdapter()
retrieval = SlideRetrievalService(storage)

results = await retrieval.search_slides(
    query="company overview with financial metrics",
    layout_filter="title_content_chart",
    limit=5
)

for metadata, score in results:
    print(f"{metadata.purpose} (score: {score:.2f})")

```

---

## Configuration

### Environment Variables (add to `.env`)

```bash
# Slide Library Configuration
SLIDE_LIBRARY_COLLECTION=slide_library
SLIDE_LIBRARY_DATABASE=slide_agent
SLIDE_LIBRARY_S3_PREFIX=slides/

# Reuse existing rag_engine config
MONGODB_URI=...
S3_BUCKET_NAME=...
QDRANT_URL=...

```

### Constants (add to `constants.py` or new `slide_library/config.py`)

```python
# Collection names
QDRANT_COLLECTION_SLIDES = "slide_library"
MONGODB_DATABASE_SLIDES = "slide_agent"
MONGODB_COLLECTION_SLIDES = "slide_library"

# Layout types
LAYOUT_TYPES = [
    "title_only",
    "title_content",
    "title_content_chart",
    "title_content_table",
    "two_column",
    "multi_column",
    "chart_focus",
    "table_focus",
    "image_focus"
]

# Retrieval settings
DEFAULT_RETRIEVAL_LIMIT = 20
DEFAULT_RERANK_LIMIT = 5
LAYOUT_COMPATIBILITY_WEIGHT = 0.3

```

---

## Critical Design Decisions & Rationale

### 1. Single-slide PPTX Storage vs. Alternatives

**Decision**: Store as single-slide PPTX files

**Alternatives Considered**:

- Store as images (PNG/JPG) + metadata
- Store as JSON structure only
- Store as slide XML fragments

**Rationale**:

- ✅ Preserves all formatting (fonts, colors, animations, embedded objects)
- ✅ Compatible with existing PPTXLoader/PPTXSlideManager
- ✅ Can be opened directly in PowerPoint for inspection
- ✅ No reconstruction complexity
- ❌ Larger storage footprint (mitigated by S3 compression and hash-based deduplication)

**Recommendation**: Proceed with PPTX storage. If storage costs become issue, add optional image preview generation.

---

### 2. Purpose Generation Strategy

**Decision**: LLM-based purpose generation per slide

**Alternatives Considered**:

- Use slide notes if available, skip LLM
- Extract text and use as-is
- Hybrid: notes → text → LLM fallback

**Rationale**:

- ✅ Consistent, semantic descriptions
- ✅ Handles slides without notes
- ✅ Better for retrieval (normalized language)
- ❌ LLM cost per slide (mitigated by batch processing and caching)

**Recommendation**: Implement hybrid approach:

1. If slide has notes → use notes as purpose
2. Else → generate with LLM
3. Cache generated purposes to avoid re-processing

---

### 3. Layout Classification: Rule-based vs. ML

**Decision**: Start with rule-based, upgrade to ML later

**Alternatives Considered**:

- Train ML classifier on slide layouts
- Use vision model (Gemini Vision) for layout detection
- Manual tagging during ingestion

**Rationale**:

- ✅ Rule-based is fast and deterministic
- ✅ Content structure (from normalize_presentation) provides clear signals
- ✅ Can upgrade to ML without changing API
- ❌ May miss nuanced layouts (acceptable for v1)

**Recommendation**: Implement rule-based classifier with clear rules. Add ML upgrade path in v2.

**Rules Example**:

```python
def classify_layout(content_mapping: SlideContent) -> str:
    content_items = content_mapping.content.values()
    text_count = sum(1 for c in content_items if c.content_type == "TEXT")
    table_count = sum(1 for c in content_items if c.content_type == "TABLE")
    chart_count = sum(1 for c in content_items if c.content_type == "CHART")

    if text_count == 1 and table_count == 0 and chart_count == 0:
        return "title_only"
    elif text_count >= 1 and chart_count >= 1:
        return "title_content_chart"
    elif text_count >= 1 and table_count >= 1:
        return "title_content_table"
    # ... more rules
    else:
        return "mixed"

```

---

### 4. Retrieval Strategy: Pure Semantic vs. Hybrid

**Decision**: Hybrid (semantic + structural filtering + re-ranking)

**Alternatives Considered**:

- Pure semantic search (Qdrant only)
- Pure structural matching (layout + content types)
- Two-stage: semantic → structural filter

**Rationale**:

- ✅ Semantic captures intent, structural ensures compatibility
- ✅ Re-ranking balances relevance and usability
- ✅ Qdrant supports payload filtering (efficient)
- ❌ More complex than pure semantic (acceptable trade-off)

**Recommendation**: Implement hybrid with configurable weights.

**Search Flow**:

```python
# 1. Semantic search with structural filters
results = qdrant.search(
    collection="slide_library",
    query_vector=embedding,
    query_filter={
        "must": [
            {"key": "layout_type", "match": {"value": required_layout}}
        ],
        "should": [
            {"key": "content_types", "match": {"any": required_content_types}}
        ]
    },
    limit=20
)

# 2. Re-rank by layout compatibility
reranked = sorted(
    results,
    key=lambda r: (
        0.7 * r.score +  # Semantic score
        0.3 * calculate_layout_compatibility(r.payload, requirements)
    ),
    reverse=True
)[:5]

```

---

### 5. Fallback Strategy When No Slide Found

**Decision**: Configurable fallback (default template, skip, or error)

**Alternatives Considered**:

- Always use default template
- Always skip (shorter presentation)
- Always error (strict mode)
- Generate blank slide with layout

**Rationale**:

- ✅ Flexibility for different use cases
- ✅ Default template maintains presentation completeness
- ✅ Skip option for strict matching
- ❌ Requires default template management (acceptable)

**Recommendation**: Implement configurable fallback with default template as default.

```python
class SlideCompositionOrchestrator:
    def __init__(
        self,
        ...,
        fallback_strategy: str = "default_template",  # or "skip", "error"
        default_template_path: Optional[Path] = None
    ):
        ...

```

---

### 6. Content Generation: Per-slide vs. Whole Presentation

**Decision**: Whole presentation (existing PresentationProcessor pipeline)

**Alternatives Considered**:

- Generate content per slide during retrieval
- Hybrid: retrieve slides with content, then refine
- Two-pass: retrieve → merge → generate

**Rationale**:

- ✅ Maintains content coherence across slides
- ✅ Reuses existing, tested pipeline
- ✅ Single LLM context for entire presentation
- ❌ Can't leverage pre-generated content from library (acceptable for v1)

**Recommendation**: Use existing pipeline. In v2, explore hybrid approach where library slides come with "suggested content" that can be refined.

---

### 7. Atomic Storage Operations

**Decision**: Implement rollback on storage failure

**Alternatives Considered**:

- Best-effort storage (no rollback)
- Two-phase commit
- Event sourcing

**Rationale**:

- ✅ Prevents orphaned data (S3 file without MongoDB entry)
- ✅ Maintains data consistency
- ✅ Simple rollback logic (delete what was created)
- ❌ Slightly slower (acceptable for ingestion)

**Recommendation**: Implement simple rollback in SlideStorageAdapter.

```python
async def store_slide(self, ...) -> StorageReference:
    s3_key = None
    mongo_id = None
    qdrant_id = None

    try:
        # 1. Upload to S3
        s3_key = await self.s3.upload_file(...)

        # 2. Store in MongoDB
        mongo_id = await self.mongo.create(...)

        # 3. Store in Qdrant
        qdrant_id = await self.qdrant.upsert(...)

        return StorageReference(s3_key, mongo_id, qdrant_id)

    except Exception as e:
        # Rollback
        if s3_key:
            await self.s3.delete(s3_key)
        if mongo_id:
            await self.mongo.delete({"_id": mongo_id})
        if qdrant_id:
            await self.qdrant.delete([qdrant_id])
        raise

```

---

## Potential Issues & Mitigations

### Issue 1: LLM Cost for Purpose Generation

**Problem**: Generating purpose for every slide in large presentations could be expensive.

**Mitigations**:

1. **Batch processing**: Process multiple slides in single LLM call
2. **Caching**: Hash slide content, cache generated purposes
3. **Hybrid approach**: Use slide notes when available
4. **Cheaper model**: Use Gemini Flash Lite for purpose generation

**Recommendation**: Implement caching + hybrid approach.

---

### Issue 2: Layout Compatibility Mismatch

**Problem**: Retrieved slide layout might not perfectly match requirements.

**Mitigations**:

1. **Flexible matching**: Allow "close enough" layouts (e.g., "title_content" matches "title_content_chart" if chart is optional)
2. **Layout transformation**: Automatically remove/add elements to match requirements
3. **Fallback to default**: Use default template when mismatch is severe

**Recommendation**: Implement flexible matching with configurable threshold.

---

### Issue 3: Content Coherence Across Retrieved Slides

**Problem**: Slides from different sources might have inconsistent styling or tone.

**Mitigations**:

1. **Style normalization**: Apply consistent theme to all retrieved slides before merging
2. **Source filtering**: Prefer slides from same source presentation
3. **Content regeneration**: Always regenerate content (don't use original text)

**Recommendation**: Always regenerate content (current approach). Add style normalization in v2.

---

### Issue 4: Embedding Quality for Slide Purposes

**Problem**: Slide purposes might be too short or generic for good embeddings.

**Mitigations**:

1. **Enriched descriptions**: Include content summary + layout description in embedding
2. **Multi-field embedding**: Embed purpose + tags + content types
3. **Hybrid search**: Combine semantic with keyword matching

**Recommendation**: Enrich embedding input with content summary.

```python
embedding_text = f"""
Purpose: {metadata.purpose}
Layout: {metadata.layout_type}
Content Types: {', '.join(metadata.content_types)}
Content Summary: {content_summary}
Tags: {', '.join(metadata.tags)}
"""
embedding = await voyage_embed(embedding_text)

```

---

### Issue 5: Duplicate Slides in Library

**Problem**: Same slide ingested multiple times from different presentations.

**Mitigations**:

1. **Content hashing**: Hash slide content, check for duplicates before ingestion
2. **S3 deduplication**: S3Service already uses hash-based naming (automatic dedup)
3. **Similarity detection**: Check Qdrant for highly similar slides (>0.95 similarity)

**Recommendation**: Leverage S3 hash-based dedup + add similarity check.

```python
async def _check_duplicate(self, slide_pptx: Path) -> Optional[str]:
    """Check if slide already exists in library."""
    # 1. Generate content hash
    content_hash = self.storage.s3._generate_file_hash(slide_pptx)

    # 2. Check MongoDB for existing slide with same hash
    existing = await self.storage.mongo.read(
        collection_name="slide_library",
        query={"storage_ref.s3_key": f"slides/{content_hash}.pptx"}
    )

    return existing["slide_id"] if existing else None

```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal**: Core infrastructure and schemas

- [ ] Create `slide_library/` directory structure
- [ ] Implement `schemas.py` with all data models
- [ ] Implement `storage.py` (SlideStorageAdapter)
- [ ] Write unit tests for storage adapter
- [ ] Set up MongoDB collection and Qdrant collection

**Deliverables**:

- Working storage layer
- Ability to manually store/retrieve slides
- Test coverage >80%

---

### Phase 2: Ingestion (Week 2)

**Goal**: Automated slide ingestion pipeline

- [ ] Implement `ingestion.py` (SlideIngestionService)
- [ ] Integrate with PPTXLoader and PPTXSlideManager
- [ ] Implement layout classifier (rule-based)
- [ ] Implement purpose generation (LLM)
- [ ] Add duplicate detection
- [ ] Write integration tests

**Deliverables**:

- CLI tool for ingesting presentations
- Ingestion pipeline with error handling
- Test coverage >75%

**Test Command**:

```bash
python -m slide_library.ingestion --input presentations/Q4_Earnings.pptx --tags earnings,financial

```

---

### Phase 3: Retrieval (Week 3)

**Goal**: Semantic search and retrieval

- [ ] Implement `retrieval.py` (SlideRetrievalService)
- [ ] Integrate with rag_engine retrieval pipeline
- [ ] Implement layout compatibility scoring
- [ ] Implement re-ranking logic
- [ ] Add caching for downloaded slides
- [ ] Write integration tests

**Deliverables**:

- Working retrieval API
- CLI tool for searching slides
- Test coverage >75%

**Test Command**:

```bash
python -m slide_library.retrieval --query "company overview with metrics" --layout title_content_chart

```

---

### Phase 4: Planning & Orchestration (Week 4)

**Goal**: Dynamic presentation composition

- [ ] Implement `planner.py` (SlidePlannerAgent)
- [ ] Create planning prompts and schemas
- [ ] Implement `orchestrator.py` (SlideCompositionOrchestrator)
- [ ] Integrate with retrieval and planner
- [ ] Implement slide merging logic
- [ ] Add fallback strategies
- [ ] Write end-to-end tests

**Deliverables**:

- Working dynamic composition pipeline
- CLI tool for generating presentations
- Test coverage >70%

**Test Command**:

```bash
python -m slide_library.orchestrator \\
  --prompt "Create investor deck with overview, market, financials" \\
  --context "Q4 revenue $10M, growth 25%" \\
  --output output/investor_deck.pptx

```

---

### Phase 5: Integration & Polish (Week 5)

**Goal**: Integrate with existing slide_generation.py

- [ ] Extend PresentationProcessor with mode parameter
- [ ] Implement `_execute_dynamic_mode` method
- [ ] Update `load_and_merge.py` with `merge_presentations` method
- [ ] Add configuration management
- [ ] Write comprehensive documentation
- [ ] Perform end-to-end testing
- [ ] Optimize performance (caching, batching)

**Deliverables**:

- Fully integrated system
- Updated README and API docs
- Performance benchmarks
- Production-ready code

**Test Command**:

```bash
python slide_generation.py \\
  --mode dynamic \\
  --prompt "Create investor deck" \\
  --context "Q4 data..." \\
  --output output/

```

---

## Testing Strategy

### Unit Tests

**Coverage Target**: >80%

**Key Test Cases**:

- `storage.py`: Store/retrieve/delete operations, rollback on failure
- `ingestion.py`: Slide extraction, metadata generation, layout classification
- `retrieval.py`: Search, filtering, re-ranking, compatibility scoring
- `planner.py`: Plan generation, validation
- `orchestrator.py`: Slide selection, merging, fallback handling

---

### Integration Tests

**Coverage Target**: >70%

**Key Test Cases**:

- End-to-end ingestion: PPTX → library
- End-to-end retrieval: Query → slide download
- End-to-end composition: Prompt → final PPTX
- Storage consistency: Verify S3/MongoDB/Qdrant sync
- Duplicate detection: Ingest same slide twice

---

### Performance Tests

**Benchmarks**:

- Ingestion throughput: slides/second
- Retrieval latency: ms per query
- Composition time: seconds for 10-slide deck
- Storage overhead: MB per slide

**Targets**:

- Ingestion: >5 slides/second
- Retrieval: <500ms per query
- Composition: <30 seconds for 10-slide deck

---

## Monitoring & Observability

### Metrics to Track

1. **Ingestion**:
   - Slides ingested per day
   - Ingestion failures (with reasons)
   - Duplicate detection rate
   - Average purpose generation time
2. **Retrieval**:
   - Queries per day
   - Average retrieval latency
   - Cache hit rate
   - No-results rate (queries with no matching slides)
3. **Composition**:
   - Presentations generated per day
   - Average composition time
   - Fallback usage rate (slides not found in library)
   - Content generation failures
4. **Storage**:
   - Total slides in library
   - Storage size (S3)
   - MongoDB collection size
   - Qdrant collection size

---

### Logging Strategy

**Log Levels**:

- `DEBUG`: Detailed flow (retrieval scores, layout compatibility calculations)
- `INFO`: Key events (slide ingested, presentation generated)
- `WARNING`: Fallbacks triggered, no results found
- `ERROR`: Storage failures, LLM errors

**Structured Logging**:

```python
logger.info(
    "Slide ingested",
    extra={
        "slide_id": metadata.slide_id,
        "source": metadata.source_presentation,
        "layout": metadata.layout_type,
        "duration_ms": duration
    }
)

```

---

## Future Enhancements (v2+)

### 1. ML-based Layout Classification

Replace rule-based classifier with vision model (Gemini Vision) for more accurate layout detection.

---

### 2. Style Transfer

Apply consistent theme/styling to retrieved slides before merging.

---

### 3. Slide Versioning

Track slide versions, allow rollback to previous versions.

---

### 4. Collaborative Library

Multi-user library with permissions, sharing, and curation.

---

### 5. Smart Templates

Library slides come with "suggested content" that can be refined rather than regenerated.

---

### 6. Analytics Dashboard

Web UI for browsing library, viewing usage analytics, curating slides.

---

### 7. Auto-tagging

Automatically generate tags from slide content using LLM.

---

### 8. Presentation Templates

Store and retrieve entire presentation templates (multi-slide sequences).

---

## Open Questions for Discussion

1. **Default Template Management**: Where should default templates be stored? How to manage multiple templates?
2. **Slide Curation**: Should there be a manual review/approval process for ingested slides?
3. **Access Control**: Do we need user-level permissions for slide library (public vs. private slides)?
4. **Embedding Model**: Stick with Voyage or explore alternatives (OpenAI, Cohere)?
5. **Layout Taxonomy**: Are the proposed layout types sufficient? Should we support custom layouts?
6. **Fallback Template**: Should fallback template match the required layout, or use generic template?
7. **Content Regeneration**: Should we always regenerate content, or allow using original content from library slides?
8. **Batch Ingestion**: Should we support batch ingestion of multiple presentations in one operation?
9. **Slide Metadata Enrichment**: Should users be able to manually edit slide metadata (purpose, tags, layout)?
10. **Performance Optimization**: What's the acceptable latency for dynamic generation? Should we pre-compute embeddings?

---

## Conclusion

This architecture provides a solid foundation for the Slide Library feature. Key strengths:

✅ **Reuses existing infrastructure**: Leverages rag_engine, load_and_merge, utils

✅ **Professional structure**: Clear separation of concerns, SOLID principles

✅ **Extensible**: Easy to add new features (ML classifier, style transfer, etc.)

✅ **Production-ready**: Error handling, rollback, logging, monitoring

✅ **Backward compatible**: Fixed mode unchanged, dynamic mode is additive

Next steps:

1. Review and discuss open questions
2. Finalize naming and API design
3. Begin Phase 1 implementation
4. Iterate based on feedback

---

**Document Version**: 1.0

**Last Updated**: 2025-12-03

**Author**: Antigravity (AI Assistant)

**Status**: Ready for Review
