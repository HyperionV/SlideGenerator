**Status**: Ready for Review

**Last Updated**: 2025-12-03

**Document Version**: 1.0

---

**Confidence Level**: High - this architecture is production-ready and maintainable.

**Verdict**: Your initial plan was solid! The recommended architecture refines it with professional structure, better integration, and production-ready patterns.

---

- **rag_engine**: All storage and retrieval infrastructure
- **slide_generation.py**: Existing content generation pipeline
- [**utils.py**](http://utils.py/): Existing normalization and extraction
- **load_and_merge.py**: Existing slide loading/copying

### What We Reused ♻️

- **Caching**: Purpose and slide caching
- **Re-ranking**: Layout compatibility scoring
- **Duplicate detection**: Hash-based deduplication
- [**schemas.py**](http://schemas.py/): Centralized data models
- [**storage.py**](http://storage.py/): Abstraction layer for rag_engine
- [**planner.py**](http://planner.py/): Dedicated planning agent

### What We Added ➕

- **Fallback handling**: Configurable strategies
- **Layout classification**: Rule-based with ML upgrade path
- **Purpose generation**: Hybrid approach (notes → LLM → cache)
- **Storage operations**: Atomic with rollback
- **Retrieval strategy**: Hybrid search (semantic + structural)
- **Module structure**: More granular, professional naming

### What We Enhanced 🔧

- Retrieval-based composition
- Two-mode system (fixed/dynamic)
- Distributed storage (S3 + MongoDB + Qdrant)
- Single-slide PPTX storage

### What We Kept ✅

## Summary: Your Plan vs. Recommended

---

1. **Iterate based on feedback**
2. **Begin Phase 1 implementation** (Foundation)
3. **Approve module structure** and naming conventions
4. **Discuss open questions** and finalize design decisions
5. **Review this document** and `ARCHITECTURE.md`

## Next Steps

---

1. **Performance Targets**: Acceptable latency for dynamic generation?
2. **Metadata Enrichment**: Allow manual editing of slide metadata?
3. **Batch Ingestion**: Support batch ingestion of multiple presentations?
4. **Content Regeneration**: Always regenerate or allow using original content?
5. **Fallback Template**: Should it match required layout or use generic?
6. **Layout Taxonomy**: Are proposed layout types sufficient? Custom layouts?
7. **Embedding Model**: Stick with Voyage or explore alternatives?
8. **Access Control**: User-level permissions (public vs. private slides)?
9. **Slide Curation**: Manual review/approval process for ingested slides?
10. **Default Template Management**: Where to store default templates? How to manage multiple templates?

## Open Questions for Discussion

---

**Mitigation**: S3 hash-based dedup + similarity detection

### Issue 5: Duplicate Slides

**Mitigation**: Enrich embedding with content summary + layout + tags

### Issue 4: Embedding Quality

**Mitigation**: Always regenerate content (don't use original)

### Issue 3: Content Coherence Across Slides

**Mitigation**: Flexible matching + fallback to default template

### Issue 2: Layout Compatibility Mismatch

**Mitigation**: Hybrid approach (notes → LLM → cache)

### Issue 1: LLM Cost for Purpose Generation

## Potential Issues & Mitigations

---

- Write documentation and tests
- Add merge_presentations to load_and_merge
- Extend PresentationProcessor with dynamic mode

### Week 5: Integration & Polish

- Add fallback strategies
- Implement SlideCompositionOrchestrator
- Implement SlidePlannerAgent

### Week 4: Planning & Orchestration

- Implement caching
- Add hybrid search and re-ranking
- Implement SlideRetrievalService

### Week 3: Retrieval

- Add layout classifier and purpose generator
- Integrate with existing loaders
- Implement SlideIngestionService

### Week 2: Ingestion

- Set up MongoDB/Qdrant collections
- Implement schemas and storage adapter
- Create module structure

### Week 1: Foundation

## Implementation Phases (5 weeks)

---

**Rationale**: Clear hierarchy, professional naming, single responsibility per module.

```
slide_library/
├── __init__.py              # Public API
├── schemas.py               # Data models
│   ├── SlideLibraryMetadata
│   ├── StorageReference
│   ├── SlideOutlineItem
│   └── PresentationPlan
│
├── storage.py               # Storage abstraction
│   └── SlideStorageAdapter
│
├── ingestion.py             # Ingestion pipeline
│   └── SlideIngestionService
│
├── retrieval.py             # Retrieval pipeline
│   └── SlideRetrievalService
│
├── planner.py               # Planning agent
│   └── SlidePlannerAgent
│
└── orchestrator.py          # Composition orchestrator
    └── SlideCompositionOrchestrator

```

## Recommended Module Structure

---

**Why**: Reuse proven infrastructure, add slide-specific logic as thin layer.

```python
# storage.py wraps rag_engine services
class SlideStorageAdapter:
    def __init__(self):
        self.mongo = get_mongo_service()  # From rag_engine
        self.s3 = get_s3_service()        # From rag_engine
        self.qdrant = get_qdrant_service()  # From rag_engine

    async def store_slide(self, ...):
        # Slide-specific logic on top of rag_engine
        ...

```

### Slide-specific Adaptations

| Component             | Usage                                      |
| --------------------- | ------------------------------------------ |
| **IngestPipeline**    | Reference for pipeline structure           |
| **RetrievalPipeline** | Voyage embedding, query expansion patterns |
| **MongoDBService**    | Direct usage for metadata storage          |
| **S3Service**         | Direct usage for PPTX file storage         |
| **QdrantService**     | Direct usage for vector storage            |

### What We're Using from rag_engine

## Integration with RAG Engine

---

**Why**: Flexibility for different use cases.

```python
orchestrator = SlideCompositionOrchestrator(
    fallback_strategy="default_template",  # or "skip", "error"
    default_template_path="templates/default.pptx"
)

```

**Recommended**: Configurable (default template / skip / error)

**Your Plan**: Not specified

### 5. Fallback Strategy: Configurable

---

**Why**: Finds relevant AND usable slides.

```python
# 1. Semantic search with filters
results = qdrant.search(
    query_vector=embed(purpose),
    filter={
        "layout_type": required_layout,
        "content_types": required_types
    }
)

# 2. Re-rank by compatibility
reranked = sort_by(
    0.7 * semantic_score +
    0.3 * layout_compatibility_score
)

```

**Search Strategy**:

**Recommended**: Semantic + structural + re-ranking

**Your Plan**: Query slide purpose

### 4. Retrieval: Hybrid Search

---

**Why**: Fast to implement, deterministic, upgradeable.

```python
if text_count == 1 and chart_count == 0:
    return "title_only"
elif text_count >= 1 and chart_count >= 1:
    return "title_content_chart"
# ... more rules

```

**Rule-based Example**:

**Recommended**: Start rule-based, upgrade to ML in v2

**Your Plan**: Not specified

### 3. Layout Classification: Rule-based → ML

---

**Why**: Reduces LLM costs, respects existing slide notes.

```python
if slide.has_notes:
    purpose = slide.notes_text
elif cached_purpose := check_cache(slide_hash):
    purpose = cached_purpose
else:
    purpose = await llm_generate_purpose(slide)
    cache_purpose(slide_hash, purpose)

```

**Recommended**: Hybrid (notes → LLM → cache)

**Your Plan**: Always generate with LLM

### 2. Purpose Generation: Hybrid Approach

---

**Verdict**: ✅ **Correct choice** - preserves formatting, compatible with existing tools

**Alternatives**: Images, JSON, XML fragments

**Decision**: Store as single-slide PPTX files (your approach)

### 1. Storage Format: Single-slide PPTX ✅

## Critical Design Decisions

---

- **Fallback strategy**: Use default template if no suitable slide found
- **Reuse existing pipeline**: PresentationProcessor handles content generation
- **Ordered merging**: Maintain slide sequence from plan
- **Hybrid retrieval**: Semantic + layout matching
- **Structured planning**: JSON schema for consistent output

**Key Refinements**:

```
Context + Prompt
    ↓
SlidePlannerAgent → PresentationPlan (JSON)
    ↓
For each SlideOutlineItem:
    SlideRetrievalService
        - Embed purpose query
        - Search Qdrant (with layout filters)
        - Re-rank by compatibility
        - Download from S3
    ↓
Collect slide paths
    ↓
PPTXSlideManager.merge_presentations (ordered)
    ↓
PresentationProcessor (fixed mode)
    - Normalize merged PPTX
    - AI reasoning
    - Content generation
    - Apply content
    ↓
Final PPTX

```

**Recommended**:

```
1. Context + prompt → input
2. Input → user intentions (LLM)
3. Intentions → slide outline (planner agent)
4. For each slide:
   4.1. Retrieve suitable slide (query purpose)
   4.2. Generate and fill content
   4.3. Merge slides

```

**Your Plan**:

### Dynamic Generation Workflow

---

- **Atomic storage**: Rollback on failure
- **Layout classification**: Rule-based classifier (upgradeable to ML)
- **Duplicate detection**: Check S3 hash before ingesting
- **Caching**: Cache generated purposes to avoid re-processing

**Key Additions**:

```
Multi-slide PPTX
    ↓
Load with PPTXLoader (Spire - already exists)
    ↓
For each slide:
    Extract to single-slide PPTX (PPTXSlideManager)
    Normalize content (utils.normalize_presentation)
    Generate purpose (LLM - with caching)
    Classify layout (rule-based → ML in v2)
    Create SlideLibraryMetadata
    Generate embedding (Voyage via rag_engine)
    ↓
Store atomically (S3 + MongoDB + Qdrant)

```

**Recommended**:

```
Slide → python-pptx → extract → metadata → store

```

**Your Plan**:

### Ingestion Workflow

## Workflow Refinements

---

**Why**: Prevents orphaned data (e.g., S3 file without MongoDB entry).

```python
try:
    s3_key = upload_to_s3()
    mongo_id = save_to_mongodb()
    qdrant_id = save_to_qdrant()
except:
    rollback_all()  # Clean up partial writes
    raise

```

**Enhancement**:

**Recommended**: Atomic storage with rollback on failure

**Your Plan**: Store to Qdrant, MongoDB, S3

### 5. **Atomic Storage Operations**

---

**Why**: Semantic search finds relevant slides, structural filters ensure they're usable.

```
Query → Embed → Qdrant Search (with layout/content type filters)
                      ↓
                Re-rank by layout compatibility
                      ↓
                Top-k results

```

**Enhancement**:

**Recommended**: Hybrid search (semantic + structural filtering + re-ranking)

**Your Plan**: Query slide purpose in Qdrant

### 4. **Hybrid Retrieval Strategy**

---

**Why**: Don't Repeat Yourself (DRY) - leverage battle-tested code.

- ✅ `rag_engine`: All storage services (MongoDB, S3, Qdrant, retrieval pipeline)
- ✅ `slide_generation.py`: PresentationProcessor (extend, don't replace)
- ✅ `utils.py`: normalize_presentation, content extraction (proven code)
- ✅ `load_and_merge.py`: PPTXLoader, PPTXSlideManager (no duplication)

**What We're Reusing**:

### 3. **Reuse Existing Infrastructure**

---

**Why**: Single Responsibility Principle - each module has one clear job.

- [**schemas.py**](http://schemas.py/): Centralized data models (prevents schema sprawl)
- [**storage.py**](http://storage.py/): Abstraction layer for rag_engine (makes storage backend swappable)
- [**planner.py**](http://planner.py/): Dedicated LLM-based planning agent (separated from orchestrator)

**Added Modules**:

### 2. **Separation of Concerns**

---

**Why**: Professional, verb-based naming that clearly indicates purpose.

- "engine" → `orchestrator.py` (avoids confusion with main engine)
- "slide merge" → `SlideCompositionOrchestrator` (more descriptive)
- "retrieve pipeline" → `SlideRetrievalService`
- "ingest pipeline" → `SlideIngestionService`

**Your Draft** → **Recommended**

### 1. **Better Naming Conventions**

## Key Improvements Over Initial Draft

---

| Your Draft                            | Recommended                                                                           | Rationale                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Slide library** (ingest + retrieve) | [**ingestion.py**](http://ingestion.py/) + [**retrieval.py**](http://retrieval.py/)   | Separate concerns, clearer responsibilities    |
| **Slide merge**                       | **Enhanced load_and_merge.py**                                                        | Already exists, just add orchestration wrapper |
| **Generator**                         | **Extended slide_generation.py**                                                      | Reuse existing PresentationProcessor           |
| **File handler**                      | **Existing load_and_merge.py**                                                        | Already has PPTXLoader + PPTXSlideManager      |
| **Engine**                            | [**orchestrator.py**](http://orchestrator.py/) + [**planner.py**](http://planner.py/) | Split planning from orchestration              |
| _(not mentioned)_                     | [**storage.py**](http://storage.py/)                                                  | Abstraction layer for rag_engine integration   |
| _(not mentioned)_                     | [**schemas.py**](http://schemas.py/)                                                  | Slide library specific data models             |

### Module Structure Comparison

## Your Initial Plan vs. Recommended Architecture

---

This document summarizes the architectural evaluation and recommendations for the Slide Library feature. For detailed technical specifications, see `ARCHITECTURE.md`.

## Quick Overview

---

**Status**: Planning Mode - Ready for Review

**Date**: 2025-12-03

# Slide Library - Planning Summary
