# Slide Library - Quick Reference

**Purpose**: Quick reference for developers implementing the Slide Library feature.

---

## Module Overview

```
slide_library/
├── schemas.py          # Data models
├── storage.py          # Storage abstraction (wraps rag_engine)
├── ingestion.py        # Slide ingestion pipeline
├── retrieval.py        # Slide retrieval and search
├── planner.py          # LLM-based presentation planning
└── orchestrator.py     # Dynamic composition orchestrator

```

---

## Core Data Models

### SlideLibraryMetadata

```python
from pydantic import BaseModel
from datetime import datetime
from typing import List

class SlideLibraryMetadata(BaseModel):
    slide_id: str                    # UUID
    purpose: str                     # "Introduce company overview with metrics"
    layout_type: str                 # "title_content_chart"
    content_types: List[str]         # ["TEXT", "CHART"]
    dimensions: SlideMetadata        # {width: 1920, height: 1080}
    element_count: int               # 3
    storage_ref: StorageReference    # S3/MongoDB/Qdrant IDs
    source_presentation: str         # "Q4_Earnings.pptx"
    ingestion_date: datetime
    tags: List[str]                  # ["earnings", "financial"]

```

### StorageReference

```python
class StorageReference(BaseModel):
    s3_key: str          # "slides/abc123hash.pptx"
    mongodb_id: str      # ObjectId as string
    qdrant_id: str       # UUID

```

### SlideOutlineItem

```python
class SlideOutlineItem(BaseModel):
    position: int                      # 1, 2, 3...
    purpose: str                       # "Show Q4 financial performance"
    required_layout: str               # "title_content_chart"
    required_content_types: List[str]  # ["TEXT", "CHART"]
    content_guidelines: str            # "Include revenue, profit, growth %"

```

### PresentationPlan

```python
class PresentationPlan(BaseModel):
    slides: List[SlideOutlineItem]
    overall_theme: str           # "Q4 Investor Update"
    target_audience: str         # "Investors and stakeholders"
    estimated_duration: int      # 15 (minutes)

```

---

## API Reference

### SlideStorageAdapter

```python
from slide_library.storage import SlideStorageAdapter

storage = SlideStorageAdapter(
    collection_name="slide_library",
    database_name="slide_agent"
)

# Store a slide
ref = await storage.store_slide(
    slide_pptx=Path("temp/slide_1.pptx"),
    metadata=slide_metadata,
    embedding=[0.123, 0.456, ...]
)

# Retrieve a slide
metadata, local_path = await storage.retrieve_slide(slide_id="uuid-123")

# Delete a slide
success = await storage.delete_slide(slide_id="uuid-123")

# Update metadata
success = await storage.update_metadata(
    slide_id="uuid-123",
    updates={"tags": ["updated", "tags"]}
)

```

---

### SlideIngestionService

```python
from slide_library.ingestion import SlideIngestionService
from slide_library.storage import SlideStorageAdapter

storage = SlideStorageAdapter()
ingestion = SlideIngestionService(storage)

# Ingest a presentation
metadata_list = await ingestion.ingest_presentation(
    pptx_path="presentations/Q4_Earnings.pptx",
    tags=["earnings", "financial", "Q4"]
)

print(f"Ingested {len(metadata_list)} slides")
for meta in metadata_list:
    print(f"  - {meta.slide_id}: {meta.purpose}")

```

**Internal Methods** (for reference):

```python
# Extract single slide to temp PPTX
slide_path = await ingestion._extract_single_slide(
    source_prs=presentation,
    slide_index=0
)

# Generate metadata for a slide
metadata = await ingestion._generate_slide_metadata(
    slide_pptx=Path("temp/slide.pptx"),
    source_name="Q4_Earnings.pptx"
)

# Classify layout
layout_type = ingestion._classify_layout(content_mapping)
# Returns: "title_content_chart", "two_column", etc.

```

---

### SlideRetrievalService

```python
from slide_library.retrieval import SlideRetrievalService
from slide_library.storage import SlideStorageAdapter

storage = SlideStorageAdapter()
retrieval = SlideRetrievalService(storage)

# Search for slides
results = await retrieval.search_slides(
    query="company overview with financial metrics",
    layout_filter="title_content_chart",
    content_type_filter=["TEXT", "CHART"],
    limit=5
)

for metadata, score in results:
    print(f"{metadata.purpose} (score: {score:.2f})")

# Get specific slide by ID
metadata, local_path = await retrieval.get_slide_by_id(
    slide_id="uuid-123"
)
print(f"Downloaded to: {local_path}")

```

**Internal Methods**:

```python
# Calculate layout compatibility
score = retrieval._calculate_layout_compatibility(
    slide_meta=metadata,
    required_layout="title_content_chart",
    required_content_types=["TEXT", "CHART"]
)
# Returns: 0.0 - 1.0

```

---

### SlidePlannerAgent

```python
from slide_library.planner import SlidePlannerAgent

planner = SlidePlannerAgent()

# Generate presentation plan
plan = await planner.generate_plan(
    user_context="Q4 2024: Revenue $10M, growth 25%, launched new product",
    user_prompt="Create investor deck with overview, market, financials",
    num_slides=5  # Optional, can auto-determine
)

print(f"Theme: {plan.overall_theme}")
print(f"Slides: {len(plan.slides)}")
for slide in plan.slides:
    print(f"  {slide.position}. {slide.purpose}")

```

**Output Example**:

```python
PresentationPlan(
    overall_theme="Q4 2024 Investor Update",
    target_audience="Investors and stakeholders",
    estimated_duration=15,
    slides=[
        SlideOutlineItem(
            position=1,
            purpose="Company overview and Q4 highlights",
            required_layout="title_content",
            required_content_types=["TEXT"],
            content_guidelines="Brief intro, key Q4 achievements"
        ),
        SlideOutlineItem(
            position=2,
            purpose="Financial performance - revenue and growth",
            required_layout="title_content_chart",
            required_content_types=["TEXT", "CHART"],
            content_guidelines="Revenue $10M, 25% growth, visual chart"
        ),
        # ... more slides
    ]
)

```

---

### SlideCompositionOrchestrator

```python
from slide_library.orchestrator import SlideCompositionOrchestrator
from slide_library.planner import SlidePlannerAgent
from slide_library.retrieval import SlideRetrievalService
from slide_generation import PresentationProcessor

planner = SlidePlannerAgent()
retrieval = SlideRetrievalService(storage)
processor = PresentationProcessor(...)

orchestrator = SlideCompositionOrchestrator(
    planner=planner,
    retriever=retrieval,
    processor=processor,
    fallback_strategy="default_template",
    default_template_path=Path("templates/default.pptx")
)

# Compose presentation dynamically
result = await orchestrator.compose_presentation(
    user_context="Q4 revenue $10M, growth 25%",
    user_prompt="Create investor deck",
    output_dir="output"
)

print(f"Generated: {result['generated_pptx']}")

```

**Internal Methods**:

```python
# Retrieve slide for outline item
slide_path = await orchestrator._retrieve_slide_for_outline(
    outline_item=SlideOutlineItem(...)
)

# Merge slides in order
merged_path = await orchestrator._merge_slides_in_order(
    slide_paths=[Path("slide1.pptx"), Path("slide2.pptx")]
)

# Generate content for merged presentation
result = await orchestrator._generate_content_for_merged(
    merged_pptx=Path("merged.pptx"),
    plan=presentation_plan,
    user_context="Q4 data..."
)

```

---

## Extended Components

### PresentationProcessor (Extended)

```python
from slide_generation import PresentationProcessor

# Fixed mode (existing)
processor = PresentationProcessor(
    pptx_path="templates/template.pptx",
    user_input="Create discussion material",
    documents="Context documents...",
    mode="fixed"
)
result = await processor.execute()

# Dynamic mode (new)
processor = PresentationProcessor(
    pptx_path=None,  # Not needed in dynamic mode
    user_input="Create investor deck with overview, market, financials",
    documents="Q4 revenue $10M, growth 25%",
    mode="dynamic"
)
result = await processor.execute()
# Internally delegates to SlideCompositionOrchestrator

```

---

### PPTXSlideManager (Enhanced)

```python
from load_and_merge import PPTXSlideManager

# New method: merge multiple presentations
merged_path = PPTXSlideManager.merge_presentations(
    slide_paths=[
        Path("slide1.pptx"),
        Path("slide2.pptx"),
        Path("slide3.pptx")
    ],
    output_path=Path("output/merged.pptx"),
    copy_dimensions_from=Path("slide1.pptx")  # Optional
)

```

---

## Usage Examples

### Example 1: Ingest Presentation

```python
import asyncio
from pathlib import Path
from slide_library import SlideIngestionService, SlideStorageAdapter

async def ingest_example():
    storage = SlideStorageAdapter()
    ingestion = SlideIngestionService(storage)

    metadata_list = await ingestion.ingest_presentation(
        pptx_path="presentations/Q4_Earnings.pptx",
        tags=["earnings", "financial", "Q4", "2024"]
    )

    print(f"✅ Ingested {len(metadata_list)} slides")
    for meta in metadata_list:
        print(f"  📄 {meta.slide_id[:8]}... - {meta.purpose}")
        print(f"     Layout: {meta.layout_type}, Elements: {meta.element_count}")

asyncio.run(ingest_example())

```

---

### Example 2: Search and Retrieve Slides

```python
import asyncio
from slide_library import SlideRetrievalService, SlideStorageAdapter

async def search_example():
    storage = SlideStorageAdapter()
    retrieval = SlideRetrievalService(storage)

    results = await retrieval.search_slides(
        query="financial performance with revenue chart",
        layout_filter="title_content_chart",
        content_type_filter=["TEXT", "CHART"],
        limit=3
    )

    print(f"🔍 Found {len(results)} matching slides:")
    for metadata, score in results:
        print(f"  📊 {metadata.purpose}")
        print(f"     Score: {score:.2f}, Source: {metadata.source_presentation}")
        print(f"     Layout: {metadata.layout_type}")

asyncio.run(search_example())

```

---

### Example 3: Generate Dynamic Presentation

```python
import asyncio
from slide_generation import PresentationProcessor

async def generate_example():
    processor = PresentationProcessor(
        pptx_path=None,
        user_input="Create investor deck with company overview, market analysis, and Q4 financials",
        documents="""
        Q4 2024 Performance:
        - Revenue: $10M (25% YoY growth)
        - New product launch: AI-powered analytics
        - Market expansion: Entered APAC region
        - Customer base: 500+ enterprise clients
        """,
        output_dir="output",
        mode="dynamic"
    )

    result = await processor.execute()

    print(f"✅ Generated presentation:")
    print(f"  📁 {result['generated_pptx']}")
    print(f"  📄 {result['structure_json']}")

asyncio.run(generate_example())

```

---

### Example 4: Manual Composition (Advanced)

```python
import asyncio
from pathlib import Path
from slide_library import (
    SlidePlannerAgent,
    SlideRetrievalService,
    SlideStorageAdapter
)
from load_and_merge import PPTXSlideManager
from slide_generation import PresentationProcessor

async def manual_composition():
    # 1. Plan
    planner = SlidePlannerAgent()
    plan = await planner.generate_plan(
        user_context="Q4 revenue $10M, growth 25%",
        user_prompt="Create 3-slide investor update"
    )

    print(f"📋 Plan: {plan.overall_theme}")

    # 2. Retrieve slides
    storage = SlideStorageAdapter()
    retrieval = SlideRetrievalService(storage)

    slide_paths = []
    for outline_item in plan.slides:
        results = await retrieval.search_slides(
            query=outline_item.purpose,
            layout_filter=outline_item.required_layout,
            limit=1
        )

        if results:
            metadata, score = results[0]
            _, local_path = await retrieval.get_slide_by_id(metadata.slide_id)
            slide_paths.append(local_path)
            print(f"  ✅ Found: {metadata.purpose} (score: {score:.2f})")
        else:
            print(f"  ⚠️  No match for: {outline_item.purpose}")

    # 3. Merge slides
    merged_path = PPTXSlideManager.merge_presentations(
        slide_paths=slide_paths,
        output_path=Path("output/merged.pptx")
    )

    print(f"🔗 Merged: {merged_path}")

    # 4. Generate content
    processor = PresentationProcessor(
        pptx_path=str(merged_path),
        user_input="Q4 investor update",
        documents="Q4 revenue $10M, growth 25%",
        mode="fixed"
    )

    result = await processor.execute()
    print(f"✅ Final: {result['generated_pptx']}")

asyncio.run(manual_composition())

```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Slide Library
SLIDE_LIBRARY_COLLECTION=slide_library
SLIDE_LIBRARY_DATABASE=slide_agent
SLIDE_LIBRARY_S3_PREFIX=slides/

# Reuse existing rag_engine config
MONGODB_URI=mongodb://localhost:27017
S3_BUCKET_NAME=your-bucket
QDRANT_URL=http://localhost:6333

```

---

### Constants

Create `slide_library/config.py`:

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
    "image_focus",
    "mixed"
]

# Retrieval settings
DEFAULT_RETRIEVAL_LIMIT = 20
DEFAULT_RERANK_LIMIT = 5
LAYOUT_COMPATIBILITY_WEIGHT = 0.3

# Ingestion settings
ENABLE_PURPOSE_CACHING = True
ENABLE_DUPLICATE_DETECTION = True

```

---

## CLI Tools (Proposed)

### Ingestion CLI

```bash
python -m slide_library.ingestion \\
  --input presentations/Q4_Earnings.pptx \\
  --tags earnings,financial,Q4 \\
  --verbose

```

---

### Retrieval CLI

```bash
python -m slide_library.retrieval \\
  --query "financial performance with charts" \\
  --layout title_content_chart \\
  --limit 5

```

---

### Generation CLI

```bash
python -m slide_library.orchestrator \\
  --prompt "Create investor deck with overview, market, financials" \\
  --context "Q4 revenue $10M, growth 25%" \\
  --output output/investor_deck.pptx \\
  --mode dynamic

```

---

## Testing

### Unit Test Example

```python
import pytest
from slide_library.storage import SlideStorageAdapter
from slide_library.schemas import SlideLibraryMetadata, StorageReference

@pytest.mark.asyncio
async def test_store_and_retrieve_slide():
    storage = SlideStorageAdapter()

    # Create test metadata
    metadata = SlideLibraryMetadata(
        slide_id="test-123",
        purpose="Test slide",
        layout_type="title_content",
        content_types=["TEXT"],
        # ... other fields
    )

    # Store
    ref = await storage.store_slide(
        slide_pptx=Path("test_files/test_slide.pptx"),
        metadata=metadata,
        embedding=[0.1] * 1024
    )

    assert ref.s3_key is not None
    assert ref.mongodb_id is not None
    assert ref.qdrant_id is not None

    # Retrieve
    retrieved_meta, local_path = await storage.retrieve_slide("test-123")

    assert retrieved_meta.slide_id == "test-123"
    assert retrieved_meta.purpose == "Test slide"
    assert local_path.exists()

    # Cleanup
    await storage.delete_slide("test-123")

```

---

### Integration Test Example

```python
import pytest
from slide_library import SlideIngestionService, SlideRetrievalService, SlideStorageAdapter

@pytest.mark.asyncio
async def test_ingest_and_retrieve_flow():
    storage = SlideStorageAdapter()
    ingestion = SlideIngestionService(storage)
    retrieval = SlideRetrievalService(storage)

    # Ingest
    metadata_list = await ingestion.ingest_presentation(
        pptx_path="test_files/sample.pptx",
        tags=["test"]
    )

    assert len(metadata_list) > 0

    # Retrieve
    results = await retrieval.search_slides(
        query=metadata_list[0].purpose,
        limit=1
    )

    assert len(results) > 0
    assert results[0][0].slide_id == metadata_list[0].slide_id

    # Cleanup
    for meta in metadata_list:
        await storage.delete_slide(meta.slide_id)

```

---

## Common Patterns

### Pattern 1: Batch Ingestion

```python
async def batch_ingest(presentation_paths: List[Path]):
    storage = SlideStorageAdapter()
    ingestion = SlideIngestionService(storage)

    all_metadata = []
    for path in presentation_paths:
        metadata_list = await ingestion.ingest_presentation(
            pptx_path=str(path),
            tags=["batch", path.stem]
        )
        all_metadata.extend(metadata_list)

    return all_metadata

```

---

### Pattern 2: Filtered Retrieval

```python
async def retrieve_by_tags(tags: List[str], limit: int = 10):
    storage = SlideStorageAdapter()

    # Query MongoDB directly for tag filtering
    results = await storage.mongo.read_many(
        collection_name="slide_library",
        query={"tags": {"$in": tags}},
        database_name="slide_agent"
    )

    return [SlideLibraryMetadata(**r) for r in results[:limit]]

```

---

### Pattern 3: Slide Preview Generation

```python
from PIL import Image
from pptx import Presentation

def generate_preview(slide_pptx: Path, output_path: Path):
    """Generate PNG preview of slide."""
    # Use python-pptx or external tool (e.g., LibreOffice)
    # This is a placeholder - actual implementation depends on tools
    pass

```

---

## Error Handling

### Storage Errors

```python
from slide_library.storage import SlideStorageAdapter
from slide_library.exceptions import StorageError

try:
    ref = await storage.store_slide(...)
except StorageError as e:
    print(f"Storage failed: {e}")
    # Rollback already handled internally

```

---

### Retrieval Errors

```python
from slide_library.retrieval import SlideRetrievalService
from slide_library.exceptions import RetrievalError

try:
    results = await retrieval.search_slides(...)
except RetrievalError as e:
    print(f"Retrieval failed: {e}")
    # Fallback to default template

```

---

## Performance Tips

1. **Batch ingestion**: Process multiple presentations concurrently
2. **Cache embeddings**: Store generated embeddings to avoid recomputation
3. **Lazy loading**: Download slides only when needed
4. **Connection pooling**: Reuse MongoDB/S3/Qdrant connections
5. **Async everywhere**: Use async/await for all I/O operations

---

## Debugging

### Enable verbose logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("slide_library")
logger.setLevel(logging.DEBUG)

```

---

### Inspect storage

```python
# Check MongoDB
from rag_engine.services.storage_service import get_mongo_service

mongo = get_mongo_service()
slides = mongo.read_many("slide_library", {}, database_name="slide_agent")
print(f"Total slides: {len(slides)}")

# Check Qdrant
from rag_engine.services.vector_store_service import get_qdrant_service

qdrant = get_qdrant_service()
info = qdrant.client.get_collection("slide_library")
print(f"Vectors: {info.points_count}")

```

---

## Resources

- **Full Architecture**: See `ARCHITECTURE.md`
- **Planning Summary**: See `PLANNING_SUMMARY.md`
- **RAG Engine Docs**: `../rag_engine/README.md`
- **Slide Agent Docs**: `../README.md`

---

**Last Updated**: 2025-12-03

**Version**: 1.0
