# Slide Library Refactoring Plan

## Executive Summary

This document outlines a comprehensive refactoring plan for the `slide_library` codebase to improve maintainability, modularity, and code quality through:

1. **Modularization**: Breaking down monolithic files into focused modules
2. **Separation of Concerns**: Clear boundaries between different layers
3. **DRY Methodology**: Eliminating code duplication through utility classes
4. **Clean Architecture**: Logical organization following domain boundaries

**Estimated Effort**: 16-23 hours  
**Risk Level**: Medium (mitigated through phased approach)  
**Backward Compatibility**: Maintained

---

## Current State Analysis

### Issues Identified

1. **Monolithic `utils.py`**

   - 1,249 lines, 46KB
   - 28+ functions with mixed concerns
   - Handles: alt text, XML manipulation, chart extraction, table styling, normalization, content updates
   - Difficult to navigate and maintain

2. **Mixed Concerns**

   - No clear separation between low-level PPTX operations and high-level business logic
   - Utility functions scattered across multiple files
   - Unclear module boundaries

3. **Code Duplication**

   - Font extraction logic repeated in multiple places
   - Table cell iteration patterns duplicated
   - Similar error handling across extraction functions
   - Validation logic repeated

4. **Poor Discoverability**
   - Flat structure makes it hard to find relevant code
   - No clear API surface
   - Unclear dependencies between modules

---

## Target Architecture

### New Directory Structure

```
slide_library/
├── core/                          # Core business logic
│   ├── __init__.py
│   ├── ingestion.py              # Slide ingestion service
│   ├── retrieval.py              # Slide retrieval service
│   ├── orchestrator.py           # Composition orchestrator
│   ├── planner.py                # Planner agent
│   └── storage.py                # Storage adapter
│
├── processing/                    # Content generation & processing
│   ├── __init__.py
│   ├── processor.py              # PresentationProcessor class
│   └── generator.py              # process_presentation_flow function
│
├── pptx/                         # PowerPoint manipulation layer
│   ├── __init__.py
│   ├── loader.py                 # PPTXLoader (from load_and_merge.py)
│   ├── slide_manager.py          # PPTXSlideManager (from load_and_merge.py)
│   ├── extractors.py             # Content extraction utilities
│   ├── updaters.py               # Content application utilities
│   ├── normalizer.py             # Presentation normalization
│   ├── styling.py                # Style extraction/application
│   ├── xml_utils.py              # XML manipulation, chart links
│   └── utilities.py              # Shared utility classes (NEW)
│
├── models/                       # Data models
│   ├── __init__.py
│   └── schemas.py                # Pydantic models
│
├── config/                       # Configuration
│   ├── __init__.py
│   ├── llm.py                    # LLM configuration
│   └── constants.py              # Constants
│
├── prompts/                      # Prompt templates (unchanged)
│   ├── __init__.py
│   ├── prompts.py
│   └── schemas.py
│
├── rag_engine/                   # RAG engine (unchanged)
│   └── ...
│
└── docs/                         # Documentation
    ├── ARCHITECTURE.md
    ├── PLANNING.md
    ├── QUICK_REFERENCE.md
    ├── REFACTORING_PLAN.md       # This document
    └── MIGRATION.md              # Migration guide (to be created)
```

### Layer Responsibilities

#### 1. `pptx/` - PowerPoint Manipulation Layer

**Purpose**: Low-level PowerPoint operations  
**Dependencies**: Only external libraries (python-pptx, spire.presentation)  
**No dependencies on**: core/, processing/, models/

**Modules**:

- `xml_utils.py`: Alt text operations, chart link breaking, XML manipulation
- `extractors.py`: Extract content from presentations (charts, notes, styles)
- `updaters.py`: Apply content to presentations (text, tables, charts)
- `normalizer.py`: Normalize presentations, export structure
- `styling.py`: Style extraction and application
- `loader.py`: PPTXLoader class for loading presentations
- `slide_manager.py`: PPTXSlideManager for slide operations
- `utilities.py`: Shared utility classes (FontExtractor, TableIterator, etc.)

#### 2. `core/` - Core Business Logic

**Purpose**: High-level business services  
**Dependencies**: models/, config/, pptx/, rag_engine/

**Modules**:

- `ingestion.py`: Slide ingestion service
- `retrieval.py`: Slide retrieval service
- `storage.py`: Storage adapter (MongoDB, S3, Qdrant)
- `orchestrator.py`: Composition orchestrator
- `planner.py`: Presentation planner agent

#### 3. `processing/` - Content Generation

**Purpose**: AI-powered content generation and processing  
**Dependencies**: models/, config/, pptx/, prompts/

**Modules**:

- `processor.py`: PresentationProcessor class
- `generator.py`: High-level generation functions

#### 4. `models/` - Data Models

**Purpose**: Pydantic schemas and data structures  
**Dependencies**: None (pure data models)

#### 5. `config/` - Configuration

**Purpose**: Configuration and constants  
**Dependencies**: External libraries only

---

## Detailed File Mappings

### Phase 1: Foundation (Config & Models)

| Current File   | New Location          | Changes       |
| -------------- | --------------------- | ------------- |
| `schemas.py`   | `models/schemas.py`   | Move only     |
| `constants.py` | `config/constants.py` | Move only     |
| `config.py`    | `config/llm.py`       | Move + rename |

### Phase 2: PPTX Layer (Split utils.py & load_and_merge.py)

#### From `utils.py` (1,249 lines):

| Function(s)                                                                                                                                                                  | New Location         | Lines    |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | -------- |
| `get_shape_alt_text()`, `set_shape_alt_text()`, `break_external_chart_links()`, `_modify_chart_xml()`, `_modify_relationships_xml()`                                         | `pptx/xml_utils.py`  | 17-178   |
| `extract_chart_metadata()`, `extract_slide_notes()`, `extract_cell_style()`, `extract_table_styling()`                                                                       | `pptx/extractors.py` | 180-332  |
| `normalize_presentation()`, `export_slide_structure()`, `save_structure_to_file()`, `clear_all_alt_text()`                                                                   | `pptx/normalizer.py` | 335-579  |
| `update_text_component()`, `update_single_cell_table()`, `update_table_component()`, `apply_content_to_presentation()`                                                       | `pptx/updaters.py`   | 582-1100 |
| `apply_cell_style()`, `_copy_font_formatting()`, `_add_table_row()`, `_add_table_column()`, `_remove_table_row()`, `_remove_table_column()`, `_redistribute_column_widths()` | `pptx/styling.py`    | 859+     |

#### From `load_and_merge.py`:

| Class/Function           | New Location            |
| ------------------------ | ----------------------- |
| `PPTXLoader` class       | `pptx/loader.py`        |
| `PPTXSlideManager` class | `pptx/slide_manager.py` |
| `load_pptx()` function   | `pptx/loader.py`        |

### Phase 3: Processing Layer

| Current File          | New Location              | Component                              |
| --------------------- | ------------------------- | -------------------------------------- |
| `slide_generation.py` | `processing/processor.py` | `PresentationProcessor` class          |
| `slide_generation.py` | `processing/generator.py` | `process_presentation_flow()` function |

### Phase 4: Core Layer

| Current File      | New Location           | Changes   |
| ----------------- | ---------------------- | --------- |
| `ingestion.py`    | `core/ingestion.py`    | Move only |
| `retrieval.py`    | `core/retrieval.py`    | Move only |
| `storage.py`      | `core/storage.py`      | Move only |
| `orchestrator.py` | `core/orchestrator.py` | Move only |
| `planner.py`      | `core/planner.py`      | Move only |

---

## DRY Improvements (Phase 5)

### New Utility Classes in `pptx/utilities.py`

#### 1. FontExtractor

**Purpose**: Consolidate font extraction logic  
**Eliminates**: Duplicate font extraction in normalize_presentation()

```python
class FontExtractor:
    @staticmethod
    def from_text_frame(text_frame) -> Font:
        """Extract font from text frame's first run."""

    @staticmethod
    def from_table_cell(cell) -> Font:
        """Extract font from table cell's first run."""
```

#### 2. FontApplicator

**Purpose**: Consolidate font application logic  
**Eliminates**: \_copy_font_formatting() duplication

```python
class FontApplicator:
    @staticmethod
    def copy_formatting(target_font, source_font):
        """Copy font formatting from source to target."""
```

#### 3. ShapeValidator

**Purpose**: Centralize shape validation  
**Eliminates**: Repeated shape type checking

```python
class ShapeValidator:
    @staticmethod
    def is_replaceable_text(shape) -> bool:
        """Check if shape contains replaceable text."""

    @staticmethod
    def is_replaceable_table(shape) -> bool:
        """Check if shape is a replaceable table."""
```

#### 4. UUIDManager

**Purpose**: Manage UUID operations  
**Eliminates**: UUID generation and alt_text setting duplication

```python
class UUIDManager:
    @staticmethod
    def generate_and_set(shape, is_single_cell=False) -> str:
        """Generate UUID and set as alt_text."""

    @staticmethod
    def get_from_shape(shape) -> str:
        """Get UUID from shape alt_text."""
```

#### 5. TableIterator

**Purpose**: Standardize table iteration  
**Eliminates**: Repeated table iteration patterns

```python
class TableIterator:
    @staticmethod
    def iter_cells(table):
        """Iterate all cells."""

    @staticmethod
    def iter_rows(table):
        """Iterate rows."""
```

---

## API Design

### Root Package (`slide_library/__init__.py`)

```python
"""
Slide Library - AI-powered presentation composition system
"""

# Core services
from .core.ingestion import SlideIngestionService
from .core.retrieval import SlideRetrievalService
from .core.storage import SlideStorageAdapter
from .core.orchestrator import SlideCompositionOrchestrator
from .core.planner import SlidePlannerAgent

# Processing
from .processing.processor import PresentationProcessor
from .processing.generator import process_presentation_flow

# Models
from .models.schemas import *

__all__ = [
    # Core
    'SlideIngestionService',
    'SlideRetrievalService',
    'SlideStorageAdapter',
    'SlideCompositionOrchestrator',
    'SlidePlannerAgent',
    # Processing
    'PresentationProcessor',
    'process_presentation_flow',
]
```

### PPTX Package (`pptx/__init__.py`)

```python
"""
PowerPoint manipulation utilities
"""

from .loader import PPTXLoader, load_pptx
from .slide_manager import PPTXSlideManager
from .normalizer import normalize_presentation, export_slide_structure
from .extractors import (
    extract_chart_metadata,
    extract_slide_notes,
    extract_cell_style,
    extract_table_styling
)
from .updaters import (
    update_text_component,
    update_table_component,
    update_single_cell_table
)
from .styling import apply_cell_style
from .xml_utils import get_shape_alt_text, set_shape_alt_text

__all__ = [
    # Loader
    'PPTXLoader',
    'load_pptx',
    'PPTXSlideManager',
    # Normalizer
    'normalize_presentation',
    'export_slide_structure',
    # Extractors
    'extract_chart_metadata',
    'extract_slide_notes',
    'extract_cell_style',
    'extract_table_styling',
    # Updaters
    'update_text_component',
    'update_table_component',
    'update_single_cell_table',
    # Styling
    'apply_cell_style',
    # XML Utils
    'get_shape_alt_text',
    'set_shape_alt_text',
]
```

---

## Implementation Plan

### Phase 1: Foundation (2-3 hours)

**Risk**: LOW  
**Rollback**: Easy

**Steps**:

1. Create directory structure

   ```bash
   mkdir -p slide_library/{core,pptx,processing,models,config}
   ```

2. Move configuration files

   - `schemas.py` → `models/schemas.py`
   - `constants.py` → `config/constants.py`
   - `config.py` → `config/llm.py`

3. Create `__init__.py` files for all new packages

4. Update imports in dependent files:

   - `ingestion.py`
   - `retrieval.py`
   - `storage.py`
   - `orchestrator.py`
   - `planner.py`
   - `slide_generation.py`

5. Test: Run existing workflows to ensure nothing broke

6. **Commit**: "Phase 1: Create modular structure and move config files"

**Validation**:

- [ ] All imports resolve correctly
- [ ] Existing tests pass
- [ ] No runtime errors

---

### Phase 2: PPTX Layer (6-8 hours)

**Risk**: MEDIUM-HIGH (biggest change)  
**Rollback**: Moderate (keep utils.py as backup)

**Steps**:

1. **Create `pptx/xml_utils.py`**

   - Extract lines 17-178 from `utils.py`
   - Functions: `get_shape_alt_text()`, `set_shape_alt_text()`, `break_external_chart_links()`, `_modify_chart_xml()`, `_modify_relationships_xml()`

2. **Create `pptx/extractors.py`**

   - Extract lines 180-332 from `utils.py`
   - Functions: `extract_chart_metadata()`, `extract_slide_notes()`, `extract_cell_style()`, `extract_table_styling()`

3. **Create `pptx/styling.py`**

   - Extract styling functions from `utils.py`
   - Functions: `apply_cell_style()`, `_copy_font_formatting()`, `_add_table_row()`, `_add_table_column()`, `_remove_table_row()`, `_remove_table_column()`, `_redistribute_column_widths()`

4. **Create `pptx/normalizer.py`**

   - Extract lines 335-579 from `utils.py`
   - Functions: `normalize_presentation()`, `export_slide_structure()`, `save_structure_to_file()`, `clear_all_alt_text()`

5. **Create `pptx/updaters.py`**

   - Extract update functions from `utils.py`
   - Functions: `update_text_component()`, `update_single_cell_table()`, `update_table_component()`, `apply_content_to_presentation()`

6. **Create `pptx/loader.py`**

   - Extract `PPTXLoader` class from `load_and_merge.py`
   - Include `load_pptx()` function

7. **Create `pptx/slide_manager.py`**

   - Extract `PPTXSlideManager` class from `load_and_merge.py`

8. **Create `pptx/__init__.py`** with proper exports

9. **Update imports** in all dependent files:

   - `ingestion.py`
   - `orchestrator.py`
   - `slide_generation.py`
   - Any other files importing from `utils.py` or `load_and_merge.py`

10. **Keep backups**: Rename `utils.py` → `utils.py.bak`, `load_and_merge.py` → `load_and_merge.py.bak`

11. **Test**: Run ingestion and generation workflows

12. **Commit**: "Phase 2: Split utils.py and load_and_merge.py into pptx/ modules"

**Validation**:

- [ ] All pptx/ modules import correctly
- [ ] Ingestion workflow works
- [ ] Generation workflow works
- [ ] No missing functions

---

### Phase 3: Processing Layer (2-3 hours)

**Risk**: MEDIUM  
**Rollback**: Easy

**Steps**:

1. **Create `processing/processor.py`**

   - Extract `PresentationProcessor` class from `slide_generation.py`
   - Include all methods and dependencies

2. **Create `processing/generator.py`**

   - Extract `process_presentation_flow()` function from `slide_generation.py`
   - Include any helper functions

3. **Create `processing/__init__.py`** with exports

4. **Update imports** in dependent files

5. **Keep backup**: Rename `slide_generation.py` → `slide_generation.py.bak`

6. **Test**: Run generation pipeline

7. **Commit**: "Phase 3: Create processing layer"

**Validation**:

- [ ] Processing modules import correctly
- [ ] Generation pipeline works end-to-end
- [ ] No functionality lost

---

### Phase 4: Core Layer (2-3 hours)

**Risk**: LOW  
**Rollback**: Easy

**Steps**:

1. **Move files to `core/`**:

   ```bash
   mv ingestion.py core/
   mv retrieval.py core/
   mv storage.py core/
   mv orchestrator.py core/
   mv planner.py core/
   ```

2. **Create `core/__init__.py`** with exports

3. **Update imports** in:

   - Root `__init__.py`
   - Any external scripts using these modules

4. **Test**: Full integration test

5. **Commit**: "Phase 4: Organize core services"

**Validation**:

- [ ] All core services accessible
- [ ] Full workflow (ingestion → retrieval → orchestration) works
- [ ] External scripts still work

---

### Phase 5: DRY Improvements (4-6 hours)

**Risk**: LOW-MEDIUM  
**Rollback**: Easy (utilities are additive)

**Steps**:

1. **Create `pptx/utilities.py`**

   - Implement `FontExtractor` class
   - Implement `FontApplicator` class
   - Implement `ShapeValidator` class
   - Implement `UUIDManager` class
   - Implement `TableIterator` class

2. **Refactor `pptx/normalizer.py`**

   - Use `FontExtractor` instead of inline font extraction
   - Use `UUIDManager` for UUID operations
   - Use `ShapeValidator` for shape validation

3. **Refactor `pptx/updaters.py`**

   - Use `FontApplicator` for font copying
   - Use `TableIterator` for table operations

4. **Refactor `pptx/styling.py`**

   - Use `FontApplicator` where applicable

5. **Remove duplicated code** from all modules

6. **Test**: Regression testing to ensure behavior unchanged

7. **Commit**: "Phase 5: Add utility classes and eliminate duplication"

**Validation**:

- [ ] All utility classes work correctly
- [ ] No duplicated code remains
- [ ] All tests pass
- [ ] Output is identical to before refactoring

---

### Final Steps (1-2 hours)

1. **Delete backup files**:

   - `utils.py.bak`
   - `load_and_merge.py.bak`
   - `slide_generation.py.bak`

2. **Update documentation**:

   - Update `ARCHITECTURE.md` with new structure
   - Update `QUICK_REFERENCE.md` with new import paths
   - Create `MIGRATION.md` guide

3. **Create migration guide** for external users

4. **Final integration test**:

   - Test all workflows
   - Test all import paths
   - Verify backward compatibility

5. **Commit**: "Refactoring complete: Clean, modular slide_library"

---

## Backward Compatibility

### Strategy

Maintain backward compatibility through root `__init__.py` exports:

```python
# slide_library/__init__.py

# New imports (preferred)
from .core.ingestion import SlideIngestionService
from .core.retrieval import SlideRetrievalService
# ... etc

# Backward compatibility for old imports
import warnings

def __getattr__(name):
    """Support old import paths with deprecation warnings."""

    # Old utils.py functions
    if name in ['normalize_presentation', 'export_slide_structure']:
        warnings.warn(
            f"{name} moved to slide_library.pptx.{name}. "
            f"Please update imports: from slide_library.pptx import {name}",
            DeprecationWarning,
            stacklevel=2
        )
        from .pptx import normalizer
        return getattr(normalizer, name)

    # Old load_and_merge.py classes
    if name in ['PPTXLoader', 'PPTXSlideManager']:
        warnings.warn(
            f"{name} moved to slide_library.pptx. "
            f"Please update imports: from slide_library.pptx import {name}",
            DeprecationWarning,
            stacklevel=2
        )
        if name == 'PPTXLoader':
            from .pptx.loader import PPTXLoader
            return PPTXLoader
        elif name == 'PPTXSlideManager':
            from .pptx.slide_manager import PPTXSlideManager
            return PPTXSlideManager

    raise AttributeError(f"module 'slide_library' has no attribute '{name}'")
```

### Migration Guide

Create `docs/MIGRATION.md`:

````markdown
# Migration Guide: Refactored slide_library

## Old Import Paths → New Import Paths

### Core Services (unchanged)

```python
# Still works
from slide_library import SlideIngestionService
from slide_library import SlideRetrievalService
```
````

### PPTX Utilities (changed)

```python
# OLD (deprecated, will show warning)
from slide_library.utils import normalize_presentation

# NEW (preferred)
from slide_library.pptx import normalize_presentation
```

### Full Migration Table

| Old Import                                               | New Import                                              |
| -------------------------------------------------------- | ------------------------------------------------------- |
| `from slide_library.utils import normalize_presentation` | `from slide_library.pptx import normalize_presentation` |
| `from slide_library.load_and_merge import PPTXLoader`    | `from slide_library.pptx import PPTXLoader`             |
| `from slide_library.schemas import *`                    | `from slide_library.models.schemas import *`            |

```

---

## Testing Strategy

### 1. Unit Tests (NEW)

Create tests for each new module:

```

tests/unit/
├── test_pptx_extractors.py
├── test_pptx_updaters.py
├── test_pptx_normalizer.py
├── test_pptx_styling.py
├── test_pptx_xml_utils.py
└── test_utilities.py

````

**Example test**:
```python
# tests/unit/test_pptx_extractors.py
import pytest
from slide_library.pptx import extract_chart_metadata

def test_extract_chart_metadata():
    # Test chart metadata extraction
    pass
````

### 2. Integration Tests (EXISTING + NEW)

```
tests/integration/
├── test_ingestion_workflow.py
├── test_retrieval_workflow.py
├── test_orchestration_workflow.py
└── test_generation_workflow.py
```

### 3. Regression Tests (CRITICAL)

```
tests/regression/
├── test_output_consistency.py
└── fixtures/
    ├── input_1.pptx
    ├── expected_output_1.json
    └── expected_output_1.pptx
```

**Strategy**:

1. Before refactoring: Capture outputs of key workflows
2. After each phase: Compare outputs to baseline
3. Ensure byte-for-byte consistency where possible

### 4. Import Tests (NEW)

```python
# tests/test_imports.py
def test_old_imports_work_with_warnings():
    """Test backward compatibility imports."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from slide_library.utils import normalize_presentation
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)

def test_new_imports_work():
    """Test new import paths."""
    from slide_library.pptx import normalize_presentation
    from slide_library.core import SlideIngestionService
    # Should not raise any warnings or errors
```

### Validation Criteria

- [ ] All existing functionality works
- [ ] No output changes (byte-for-byte where possible)
- [ ] All imports resolve correctly
- [ ] Deprecation warnings shown for old imports
- [ ] Performance is same or better
- [ ] All tests pass

---

## Risk Mitigation

### High-Risk Areas

1. **Splitting utils.py (Phase 2)**

   - **Risk**: Missing imports, broken dependencies
   - **Mitigation**: Keep utils.py as backup, test thoroughly before proceeding

2. **Import updates across codebase**

   - **Risk**: Missed imports causing runtime errors
   - **Mitigation**: Use IDE refactoring tools, grep for all imports

3. **Circular dependencies**
   - **Risk**: New structure creates circular imports
   - **Mitigation**: Follow dependency rules (pptx/ has no dependencies on core/)

### Rollback Plan

Each phase has a rollback strategy:

| Phase   | Rollback Action                                |
| ------- | ---------------------------------------------- |
| Phase 1 | Move files back to root, restore old imports   |
| Phase 2 | Restore utils.py.bak and load_and_merge.py.bak |
| Phase 3 | Restore slide_generation.py.bak                |
| Phase 4 | Move files back to root                        |
| Phase 5 | Remove utilities.py, restore old code          |

### Git Strategy

```bash
# Create feature branch
git checkout -b refactor/modular-structure

# Commit after each phase
git commit -m "Phase 1: ..."
git commit -m "Phase 2: ..."
# etc.

# If rollback needed
git revert <commit-hash>
# or
git reset --hard <previous-commit>
```

---

## Success Metrics

### Code Quality Metrics

| Metric                              | Before                 | Target After         |
| ----------------------------------- | ---------------------- | -------------------- |
| Largest file size                   | 1,249 lines (utils.py) | < 400 lines per file |
| Number of functions in largest file | 28+                    | < 15 per file        |
| Code duplication                    | ~200 lines             | < 50 lines           |
| Average module cohesion             | Low                    | High                 |
| Cyclomatic complexity               | High                   | Medium-Low           |

### Maintainability Metrics

- **Discoverability**: New developers can find relevant code in < 2 minutes
- **Testability**: Each module can be unit tested independently
- **Extensibility**: Adding new features requires changes to < 3 files
- **Documentation**: Each module has clear purpose and API

### Performance Metrics

- **Import time**: Should not increase by > 10%
- **Runtime performance**: Should remain unchanged
- **Memory usage**: Should remain unchanged

---

## Timeline

| Phase                     | Duration        | Dependencies |
| ------------------------- | --------------- | ------------ |
| Phase 1: Foundation       | 2-3 hours       | None         |
| Phase 2: PPTX Layer       | 6-8 hours       | Phase 1      |
| Phase 3: Processing Layer | 2-3 hours       | Phase 2      |
| Phase 4: Core Layer       | 2-3 hours       | Phase 3      |
| Phase 5: DRY Improvements | 4-6 hours       | Phase 4      |
| Final Steps               | 1-2 hours       | Phase 5      |
| **Total**                 | **17-25 hours** |              |

**Recommended Schedule**:

- Day 1: Phases 1-2 (8-11 hours)
- Day 2: Phases 3-4 (4-6 hours)
- Day 3: Phase 5 + Final Steps (5-8 hours)

---

## Conclusion

This refactoring plan provides a systematic approach to improving the `slide_library` codebase through:

1. **Clear modularization** with focused, single-responsibility modules
2. **Separation of concerns** across well-defined layers
3. **DRY methodology** through utility classes
4. **Backward compatibility** to avoid breaking existing code
5. **Phased implementation** to minimize risk
6. **Comprehensive testing** to ensure correctness

The result will be a cleaner, more maintainable codebase that is easier to understand, test, and extend.

---

## Appendix A: Detailed Function Mapping

### utils.py → pptx/ modules

| Function                          | Lines     | New Location         |
| --------------------------------- | --------- | -------------------- |
| `get_shape_alt_text()`            | 17-34     | `pptx/xml_utils.py`  |
| `set_shape_alt_text()`            | 37-57     | `pptx/xml_utils.py`  |
| `break_external_chart_links()`    | 60-102    | `pptx/xml_utils.py`  |
| `_modify_chart_xml()`             | 105-135   | `pptx/xml_utils.py`  |
| `_modify_relationships_xml()`     | 138-177   | `pptx/xml_utils.py`  |
| `extract_chart_metadata()`        | 180-218   | `pptx/extractors.py` |
| `extract_slide_notes()`           | 221-240   | `pptx/extractors.py` |
| `extract_cell_style()`            | 243-295   | `pptx/extractors.py` |
| `extract_table_styling()`         | 298-332   | `pptx/extractors.py` |
| `normalize_presentation()`        | 335-509   | `pptx/normalizer.py` |
| `export_slide_structure()`        | 512-579   | `pptx/normalizer.py` |
| `update_text_component()`         | 582-628   | `pptx/updaters.py`   |
| `update_single_cell_table()`      | 631-693   | `pptx/updaters.py`   |
| `update_table_component()`        | 696-856   | `pptx/updaters.py`   |
| `apply_cell_style()`              | 859-896   | `pptx/styling.py`    |
| `_add_table_row()`                | 899-933   | `pptx/styling.py`    |
| `_add_table_column()`             | 936-970   | `pptx/styling.py`    |
| `_remove_table_row()`             | 973-987   | `pptx/styling.py`    |
| `_remove_table_column()`          | 990-1004  | `pptx/styling.py`    |
| `_redistribute_column_widths()`   | 1007-1021 | `pptx/styling.py`    |
| `_copy_font_formatting()`         | 1024-1048 | `pptx/styling.py`    |
| `apply_content_to_presentation()` | 1051-1150 | `pptx/updaters.py`   |
| `save_structure_to_file()`        | 1153-1170 | `pptx/normalizer.py` |
| `clear_all_alt_text()`            | 1173-1249 | `pptx/normalizer.py` |

---

## Appendix B: Import Update Checklist

Files that need import updates:

### Phase 1 (Config & Models)

- [ ] `ingestion.py`
- [ ] `retrieval.py`
- [ ] `storage.py`
- [ ] `orchestrator.py`
- [ ] `planner.py`
- [ ] `slide_generation.py`
- [ ] `load_and_merge.py`

### Phase 2 (PPTX Layer)

- [ ] `ingestion.py` (uses utils functions)
- [ ] `orchestrator.py` (uses load_and_merge)
- [ ] `slide_generation.py` (uses utils functions)
- [ ] Any external scripts

### Phase 3 (Processing Layer)

- [ ] `orchestrator.py` (uses slide_generation)
- [ ] Any external scripts

### Phase 4 (Core Layer)

- [ ] Root `__init__.py`
- [ ] Any external scripts

---

## Appendix C: Testing Checklist

### Before Refactoring

- [ ] Run all existing tests and record results
- [ ] Capture output of ingestion workflow
- [ ] Capture output of retrieval workflow
- [ ] Capture output of orchestration workflow
- [ ] Capture output of generation workflow

### After Each Phase

- [ ] Run all existing tests
- [ ] Compare outputs to baseline
- [ ] Check for import errors
- [ ] Check for runtime errors
- [ ] Verify backward compatibility

### Final Validation

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All regression tests pass
- [ ] Import tests pass
- [ ] Performance benchmarks meet targets
- [ ] Documentation is updated
- [ ] Migration guide is complete
