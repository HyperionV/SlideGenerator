"""
Slide Library Utils Package

Provides utility functions and schemas for slide library operations.
"""

from .schemas import (
    SlideLibraryMetadata,
    SlideMetadata,
    StorageReference,
    PresentationPlan,
    SlideOutlineItem,
    SlideRetrievalResult,
    Position,
    Size,
    Font,
    CellStyle,
    TableStyleInfo,
    ChartSeries,
    ChartMetadata,
    ContentItem,
    SlideContent,
    PresentationMapping,
    ContentReasoningResponse
)

from .utils import (
    get_shape_alt_text,
    set_shape_alt_text,
    break_external_chart_links,
    extract_chart_metadata,
    extract_slide_notes,
    extract_cell_style,
    extract_table_styling,
    normalize_presentation,
    export_slide_structure,
    update_text_component,
    update_single_cell_table,
    update_table_component,
    apply_cell_style,
    update_chart_component,
    apply_content_to_presentation,
    save_structure_to_file,
    save_presentation,
    clear_all_alt_text,
    process_tag
)

from .load_and_merge import (
    PPTXLoader,
    PPTXSlideManager,
    load_pptx
)

__all__ = [
    # Schemas
    "SlideLibraryMetadata",
    "SlideMetadata",
    "StorageReference",
    "PresentationPlan",
    "SlideOutlineItem",
    "SlideRetrievalResult",
    "Position",
    "Size",
    "Font",
    "CellStyle",
    "TableStyleInfo",
    "ChartSeries",
    "ChartMetadata",
    "ContentItem",
    "SlideContent",
    "PresentationMapping",
    "ContentReasoningResponse",
    # Utils
    "get_shape_alt_text",
    "set_shape_alt_text",
    "break_external_chart_links",
    "extract_chart_metadata",
    "extract_slide_notes",
    "extract_cell_style",
    "extract_table_styling",
    "normalize_presentation",
    "export_slide_structure",
    "update_text_component",
    "update_single_cell_table",
    "update_table_component",
    "apply_cell_style",
    "update_chart_component",
    "apply_content_to_presentation",
    "save_structure_to_file",
    "save_presentation",
    "clear_all_alt_text",
    "process_tag",
    # Load and merge
    "PPTXLoader",
    "PPTXSlideManager",
    "load_pptx",
]
