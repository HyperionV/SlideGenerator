# Slide Agent - Usage Guide

**Version**: 2.0  
**Last Updated**: 2025-12-04

---

## Overview

The Slide Agent is a RAG-powered presentation generation system with two modes:

1. **Fixed Mode** - Generate content for an existing template
2. **Dynamic Mode** - Compose presentations from a slide library

---

## Quick Start

### 1. Fixed Mode (Template-Based)

Generate content for an existing PowerPoint template:

```python
import asyncio
from slide_library.slide_generation import PresentationProcessor

async def generate_from_template():
    processor = PresentationProcessor(
        pptx_path="templates/my_template.pptx",
        user_input="Create Q4 investor update with financial highlights",
        documents="""
        Q4 2024 Performance:
        - Revenue: $10M (25% YoY growth)
        - New product: AI analytics platform
        - Market: Expanded to APAC
        """,
        output_dir="output",
        mode="fixed"
    )

    result = await processor.execute()
    print(f"Generated: {result['generated_pptx']}")

asyncio.run(generate_from_template())
```

**Output Files:**

- `normalized_pptx` - Template with UUIDs in alt-text
- `structure_json` - Content mapping
- `reasoning_json` - AI reasoning for each element
- `generated_pptx` - Final presentation

---

### 2. Dynamic Mode (Library-Based)

Build presentations from ingested slides:

```python
import asyncio
from slide_library.slide_generation import PresentationProcessor

async def generate_dynamic():
    processor = PresentationProcessor(
        pptx_path=None,  # Not needed in dynamic mode
        user_input="Create 3-slide investor deck: overview, market, financials",
        documents="Q4 revenue $10M, growth 25%, launched AI product",
        output_dir="output",
        mode="dynamic"
    )

    result = await processor.execute()
    print(f"Generated: {result['generated_pptx']}")

asyncio.run(generate_dynamic())
```

---

## Slide Library Management

### Ingesting Presentations

Add slides to the library for reuse:

```python
import asyncio
from slide_library import SlideStorageAdapter, SlideIngestionService

async def ingest_presentation():
    # Initialize storage
    storage = SlideStorageAdapter()
    await storage.initialize()

    # Ingest presentation
    ingestion = SlideIngestionService(storage)
    slides = await ingestion.ingest_presentation("presentations/Q4_Deck.pptx")

    print(f"✅ Ingested {len(slides)} slides")
    for slide in slides:
        print(f"  📄 {slide.slide_id[:8]}... - {slide.description[:60]}...")

    await storage.close()

asyncio.run(ingest_presentation())
```

**What Happens:**

1. Each slide extracted to single-slide PPTX
2. Description generated (from user notes or LLM)
3. Stored in:
   - **S3** - PPTX file
   - **MongoDB** - Metadata
   - **Qdrant** - Vector embedding

---

### Searching Slides

Find slides semantically:

```python
import asyncio
from slide_library import SlideStorageAdapter, SlideRetrievalService

async def search_slides():
    storage = SlideStorageAdapter()
    await storage.initialize()

    retrieval = SlideRetrievalService(storage)

    results = await retrieval.search_slides(
        query="financial performance with revenue chart",
        limit=5
    )

    print(f"🔍 Found {len(results)} slides:")
    for metadata, score in results:
        print(f"  📊 Score: {score:.2f}")
        print(f"     {metadata.description[:80]}...")
        print(f"     Source: {metadata.source_presentation}")

    await storage.close()

asyncio.run(search_slides())
```

---

## Architecture Overview

### Core Components

```
slide_library/
├── schemas.py          # Data models (SlideLibraryMetadata, PresentationPlan)
├── storage.py          # Storage adapter (S3 + MongoDB + Qdrant)
├── ingestion.py        # Slide ingestion pipeline
├── retrieval.py        # Semantic search
├── planner.py          # LLM-based presentation planning
├── orchestrator.py     # Dynamic composition orchestrator
├── slide_generation.py # Content generation pipeline
└── utils.py            # PPTX manipulation utilities
```

### Data Models

**SlideLibraryMetadata** - Metadata for library slides:

```python
{
    "slide_id": "uuid-123",
    "description": "Comprehensive description including purpose, content, structure",
    "dimensions": {"width": 1920, "height": 1080},
    "element_count": 3,
    "storage_ref": {
        "s3_key": "slides/abc123.pptx",
        "mongodb_id": "ObjectId(...)",
        "qdrant_id": "uuid-456"
    },
    "source_presentation": "Q4_Earnings.pptx",
    "ingested_at": "2025-12-04T..."
}
```

**PresentationPlan** - Generated outline:

```python
{
    "overall_theme": "Q4 Investor Update",
    "target_audience": "Investors and stakeholders",
    "slides": [
        {
            "position": 1,
            "description": "Company overview and Q4 highlights",
            "content_guidelines": "Brief intro, key achievements"
        },
        ...
    ]
}
```

---

## Workflows

### Fixed Mode Workflow

```
Template PPTX + User Context
         ↓
    Normalize (add UUIDs to shapes)
         ↓
    Extract Structure (content mapping)
         ↓
    AI Reasoning (what content should be)
         ↓
    Content Generation (actual content)
         ↓
    Apply Content (update PPTX)
         ↓
    Final PPTX
```

### Dynamic Mode Workflow

```
User Context + Prompt
         ↓
    Generate Plan (LLM)
         ↓
    For each slide in plan:
        ↓
    Search Library (semantic)
        ↓
    Retrieve Slide (or use fallback)
         ↓
    Merge Slides (ordered)
         ↓
    Generate Content (fixed mode pipeline)
         ↓
    Final PPTX
```

---

## Key Features

### 1. Content Normalization

**What**: Assigns UUIDs to all shapes via alt-text  
**Why**: Enables bidirectional mapping between PPTX and content data  
**Where**: `utils.normalize_presentation()`

### 2. AI Reasoning

**What**: LLM analyzes template and generates content descriptions  
**Why**: Separates "what to say" from "how to say it"  
**Where**: `slide_generation._generate_content_description()`

### 3. Content Generation

**What**: LLM generates actual content based on reasoning  
**Why**: Produces contextually relevant content  
**Where**: `slide_generation._generate_slide_content()`

### 4. Semantic Retrieval

**What**: Vector search on comprehensive slide descriptions  
**Why**: Finds relevant slides without manual tagging  
**Where**: `retrieval.search_slides()`

### 5. Description Field

**What**: Rich, comprehensive slide description  
**Includes**:

- Purpose/theme
- Content summary
- Visual structure
- Component types
- Layout information

**Example**:

```
This slide presents Q4 financial performance with revenue growth focus.

Purpose: Communicate quarterly results to investors.

Content: Title "Q4 2024 Results", subtitle "25% YoY Growth",
bar chart showing $8M → $10M progression.

Structure: Title-content-chart layout, title top (large, bold),
text middle-left, chart right (40% width), blue theme.

Visual Elements: 1 title, 2 text blocks, 1 bar chart.
```

---

## Storage Architecture

### Three-Tier Storage

1. **S3** - PPTX files (hash-based deduplication)
2. **MongoDB** - Metadata (slide_agent.slide_library)
3. **Qdrant** - Vector embeddings (slide_library collection)

### Atomic Operations

All storage operations are atomic with rollback:

- Store: S3 → MongoDB → Qdrant (rollback on failure)
- Delete: Qdrant → MongoDB → S3 (best-effort cleanup)

---

## Advanced Usage

### Manual Composition

Full control over the composition process:

```python
import asyncio
from pathlib import Path
from slide_library import (
    SlidePlannerAgent,
    SlideRetrievalService,
    SlideStorageAdapter
)
from slide_library.load_and_merge import PPTXSlideManager
from slide_library.slide_generation import PresentationProcessor

async def manual_composition():
    # 1. Generate plan
    planner = SlidePlannerAgent()
    plan = await planner.generate_plan(
        user_context="Q4 revenue $10M, growth 25%",
        user_prompt="Create 3-slide investor update"
    )

    # 2. Retrieve slides
    storage = SlideStorageAdapter()
    await storage.initialize()
    retrieval = SlideRetrievalService(storage)

    slide_paths = []
    for item in plan.slides:
        results = await retrieval.search_slides(item.description, limit=1)
        if results:
            metadata, _ = results[0]
            _, path = await storage.get_slide_by_id(metadata.slide_id)
            slide_paths.append(path)

    # 3. Merge slides
    merged = PPTXSlideManager.merge_presentations(
        slide_paths=slide_paths,
        output_path=Path("output/merged.pptx")
    )

    # 4. Generate content
    processor = PresentationProcessor(
        pptx_path=str(merged),
        user_input="Q4 update",
        documents="Q4 revenue $10M, growth 25%",
        mode="fixed"
    )
    result = await processor.execute()

    await storage.close()
    return result

asyncio.run(manual_composition())
```

---

## Configuration

### Environment Variables

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017

# S3
S3_BUCKET_NAME=your-bucket
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Qdrant
QDRANT_URL=http://localhost:6333

# Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
VERTEX_AI_PROJECT=your-project
VERTEX_AI_LOCATION=us-central1
```

### Database Configuration

```python
# slide_library/storage.py
MONGODB_DATABASE = "slide_library"
MONGODB_COLLECTION = "slides"
QDRANT_COLLECTION = "slide_library"
```

---

## Error Handling

### Storage Errors

```python
try:
    await storage.store_slide(slide_path, metadata, embedding)
except Exception as e:
    print(f"Storage failed: {e}")
    # Automatic rollback already performed
```

### Retrieval Fallback

```python
results = await retrieval.search_slides(query, limit=5)
if not results:
    # Use default template
    slide_path = Path("templates/default.pptx")
```

---

## Performance Tips

1. **Batch Ingestion** - Process multiple presentations concurrently
2. **Connection Pooling** - Reuse storage connections
3. **Async Everywhere** - Use async/await for all I/O
4. **Caching** - Cache downloaded slides during session
5. **Lazy Loading** - Download slides only when needed

---

## Troubleshooting

### Issue: "No slides found"

**Cause**: Empty library or query mismatch  
**Solution**:

1. Verify slides ingested: Check MongoDB collection
2. Test query: Try broader search terms
3. Check embeddings: Verify Qdrant collection exists

### Issue: "Storage failed"

**Cause**: S3/MongoDB/Qdrant connection issues  
**Solution**:

1. Check credentials in `.env`
2. Verify services running (MongoDB, Qdrant)
3. Check network connectivity
4. Review logs for specific error

### Issue: "Content generation failed"

**Cause**: LLM API issues or malformed template  
**Solution**:

1. Verify Vertex AI credentials
2. Check template structure (valid PPTX)
3. Review reasoning output for errors
4. Ensure template has editable elements

---

## Best Practices

### 1. Description Quality

**Good**:

```
Financial performance slide showing Q4 revenue growth.
Title: "Q4 Results", chart comparing Q3 ($8M) vs Q4 ($10M).
Layout: title-chart, blue theme, bar chart on right.
```

**Bad**:

```
Slide about money
```

### 2. Template Design

- Use consistent layouts across templates
- Add meaningful alt-text to shapes
- Use slide notes for ingestion hints
- Keep element count reasonable (< 10 per slide)

### 3. Context Provision

**Good**:

```
Q4 2024: Revenue $10M (25% YoY), 500 customers,
launched AI analytics, expanded to APAC,
hired 20 engineers, raised $5M Series A
```

**Bad**:

```
Good quarter
```

---

## Examples

### Example 1: Batch Ingestion

```python
async def batch_ingest(paths: list[Path]):
    storage = SlideStorageAdapter()
    await storage.initialize()
    ingestion = SlideIngestionService(storage)

    all_slides = []
    for path in paths:
        slides = await ingestion.ingest_presentation(str(path))
        all_slides.extend(slides)
        print(f"✅ {path.name}: {len(slides)} slides")

    await storage.close()
    return all_slides
```

### Example 2: Filtered Search

```python
async def search_by_source(source_name: str):
    storage = SlideStorageAdapter()
    await storage.initialize()

    # Direct MongoDB query
    results = await storage.mongo.read(
        collection_name="slides",
        query={"source_presentation": source_name},
        database_name="slide_library"
    )

    await storage.close()
    return results
```

---

## CLI Usage (via runner.py)

```bash
# Ingest presentation
python runner.py

# Edit runner.py to customize:
# - Input file path
# - Output directory
# - Mode (fixed/dynamic)
```

---

## Summary

**Fixed Mode**: Template + Context → AI-generated content  
**Dynamic Mode**: User prompt → Plan → Retrieve → Merge → Generate

**Key Insight**: The `description` field is the single source of truth for retrieval. Make it comprehensive.

**Next Steps**:

1. Ingest your presentation library
2. Test retrieval with various queries
3. Generate dynamic presentations
4. Iterate on description quality

---

**For detailed architecture**: See `slide_library/docs/ARCHITECTURE.md`  
**For API reference**: See `slide_library/docs/QUICK_REFERENCE.md`
