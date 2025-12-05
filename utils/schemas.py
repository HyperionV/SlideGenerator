"""
Slide Library Schemas

Pydantic models for slide library data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class SlideMetadata(BaseModel):
    """Slide dimension metadata."""
    width: int
    height: int


class StorageReference(BaseModel):
    """References to stored slide across systems."""
    s3_key: str
    mongodb_id: str
    qdrant_id: str


class SlideLibraryMetadata(BaseModel):
    """Metadata for a slide in the library."""
    slide_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_hash: str = Field(description="SHA256 hash of the slide PPTX file for deduplication")
    description: str
    dimensions: SlideMetadata
    element_count: int
    storage_ref: StorageReference
    source_presentation: str
    slide_index: int = Field(description="0-based index of slide in original presentation")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)


class SlideOutlineItem(BaseModel):
    """Single slide specification in a presentation plan."""
    position: int
    description: str
    content_guidelines: str


class PresentationPlan(BaseModel):
    """Complete presentation plan from planner agent."""
    overall_theme: str
    target_audience: str
    slides: List[SlideOutlineItem]


class SlideRetrievalResult(BaseModel):
    """Result from slide retrieval."""
    slide_id: str
    description: str
    similarity_score: float
    storage_ref: StorageReference
    metadata: SlideLibraryMetadata


from pydantic import BaseModel, Field
from typing import Dict, List, Union, Any


class Position(BaseModel):
    """Represents the position of a shape on a PowerPoint slide in pixels."""
    x: float = Field(description="Horizontal position from left edge of slide")
    y: float = Field(description="Vertical position from top edge of slide")


class Size(BaseModel):
    """Represents the dimensions of a shape on a PowerPoint slide in pixels."""
    width: float = Field(description="Width of the shape")
    height: float = Field(description="Height of the shape")


class Font(BaseModel):
    """Font styling properties for text elements."""
    size: int = Field(description="Font size in points")
    bold: bool = Field(description="Whether text is bold")
    italic: bool = Field(default=False, description="Whether text is italic")
    underline: bool = Field(default=False, description="Whether text is underlined")
    name: str = Field(default="Arial", description="Font family name")


class CellStyle(BaseModel):
    """
    Comprehensive styling information for a PowerPoint table cell.
    
    Captures both text formatting (font properties) and cell-level formatting
    (background fill color). Used to preserve table styling when modifying
    table structure or content.
    """
    font_size: int = Field(default=11, description="Font size in points")
    font_bold: bool = Field(default=False, description="Whether text is bold")
    font_italic: bool = Field(default=False, description="Whether text is italic")
    font_name: str = Field(default="Arial", description="Font family name")
    font_color_rgb: tuple[int, int, int] | None = Field(default=None, description="RGB color tuple (0-255) for text")
    fill_color_rgb: tuple[int, int, int] | None = Field(default=None, description="RGB color tuple (0-255) for cell background")
    has_fill: bool = Field(default=False, description="Whether cell has a background fill")


class TableStyleInfo(BaseModel):
    """
    Stores styling templates for table headers and content cells.
    
    Implements a two-style system where the first row (headers) uses header_style
    and all subsequent rows (content) use content_style. Extracted during table
    normalization and applied during table updates to maintain consistent formatting.
    """
    header_style: CellStyle = Field(description="Styling for header row (row 0)")
    content_style: CellStyle = Field(description="Styling for content rows (row 1+)")


class ChartSeries(BaseModel):
    """Represents a single data series in a PowerPoint chart."""
    name: str = Field(default="", description="Series name/label")
    values: List[Union[float, int, str]] = Field(description="Data points in the series")


class ChartMetadata(BaseModel):
    """Complete chart data including all series and category labels."""
    series: List[ChartSeries] = Field(description="List of data series in the chart")
    categories: List[Union[float, int, str]] = Field(default=[], description="Category labels for x-axis")


class ContentItem(BaseModel):
    """
    Represents a single content element (text, table, or chart) on a slide.
    
    Stores both the original content from the template and the AI-generated content,
    along with all necessary metadata for positioning, sizing, and styling. The UUID
    key in SlideContent.content maps to this item.
    """
    original_content: Union[str, List[List[str]], ChartMetadata] = Field(description="Original content from template")
    content_type: str = Field(description="Type of content: TEXT, TABLE, or CHART")
    position: Position = Field(description="Position on slide")
    size: Size = Field(description="Dimensions of the element")
    font: Font = Field(description="Font styling (primarily for TEXT elements)")
    content_description: str = Field(default="", description="AI-generated description of what content should be")
    content: Union[str, List[str], List[List[str]], ChartMetadata] = Field(default="", description="AI-generated content to display")
    table_style: TableStyleInfo | None = Field(default=None, description="Styling info for TABLE elements")


class SlideMetadata(BaseModel):
    """Slide dimensions in pixels."""
    width: int = Field(description="Slide width")
    height: int = Field(description="Slide height")


class SlideContent(BaseModel):
    """
    Complete content mapping for a single slide.
    
    Maps UUIDs (stored in shape alt_text) to ContentItem objects, enabling
    bidirectional linking between PowerPoint shapes and content data.
    """
    slide: int = Field(description="1-based slide number")
    metadata: SlideMetadata = Field(description="Slide dimensions")
    content: Dict[str, ContentItem] = Field(description="UUID -> ContentItem mapping")
    description: str = Field(default="", description="AI-generated slide description")


class PresentationMapping(BaseModel):
    """Complete content mapping for an entire PowerPoint presentation."""
    slides: List[SlideContent] = Field(description="List of slide content mappings")


class ContentReasoningResponse(BaseModel):
    """AI reasoning output describing what content each element should contain."""
    slide: int = Field(description="1-based slide number")
    description: str = Field(description="Overall description of the slide")
    content: List[Dict[str, Any]] = Field(description="List of content descriptions with UUIDs")
