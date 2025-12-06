from typing import Optional

CONTENT_REASONING_PROMPT = f"""
## Objective
Analyze the provided slide content mapping and generate a **generalized template analysis** that describes the structural purpose and content guidelines—not the specific details of the original slide.

## Output Format
Return a JSON object following this exact structure:

```json
{{
    "slide": "slide_num",
    "description": "Rich description including purpose, content, and structure of this slide",
    "content": [
        {{
            "uuid": "uuid_1",
            "content_description": "general description of what content belongs in this component"
        }},
        {{
            "uuid": "uuid_2",
            "content_description": "general description of what content belongs in this component"
        }}
    ]
}}
```

## Critical Instructions

### 1. Template Generalization
- Treat the input as a **template structure**, not a specific instance
- Remove all references to the main entity, organization, or individual mentioned in the original slide
- Focus on the **pattern and purpose** of each component

### 2. Content Descriptions
- Use **generic placeholders** instead of specific data
- For role-based elements, describe the general category with examples:
  - ❌ "Chief Technology Officer"
  - ✅ "Leadership position (e.g., C-suite executive, department head, senior manager)"

### 3. Description Statement
- Rich description including purpose, content, and structure of this slide

### 4. Component Analysis
- For each UUID, specify:
  - What **type** of content fits this component
  - What **function** it serves in the slide
  - Relevant examples where helpful

## Example Transformation

**Input (Specific):** "John Smith, CEO at Acme Corp"

**Output (Generalized):** "Executive profile with name and title (e.g., C-level position, founder, board member)"
"""


CONTENT_GENERATION_PROMPT = """
## Objective
Generate comprehensive slide content based on user requirements, provided documents, and template structure. You have full creative control over content, styling, positioning, and sizing decisions.

## Input Context
- **User Input**: Specific requirements and context for the presentation
- **Provided Documents**: Reference materials and data sources
- **Template Structure**: Slide layout with component descriptions and metadata

## Output Format
Return a JSON object following this exact structure:

```json
{
    "slide": "slide_num",
    "description": "Rich description including purpose, content, and structure based on generated content",
    "content": [
        {
            "uuid": "component_uuid",
            "content": "generated content text (can include newlines for bullets)"
        }
    ],
    "charts": [
        {
            "uuid": "chart_component_uuid",
            "content": {
                "series": [
                    {
                        "name": "Series name (e.g. 'Market size (US$bn)')",
                        "values": [16.1, 17.66009, 19.37135, 21.24843, 23.30741]
                    }
                ]
            },
            "categories": ["2020", "2021", "2022", "2023", "2024"]
        }
    ]
}
```

## Critical Instructions

### 1. Content Generation
- Generate **specific, relevant content** based on user input and documents
- Use the component's `content_description` as guidance for what type of content belongs there
- For multi-line content, use `\n` for line breaks (will be rendered as bullets)
- Ensure content is appropriate for the slide's purpose and context

### 2. Content Guidelines
- For titles: Use clear, impactful headlines
- For body text: Provide detailed, informative content
- For lists: Use `\n` between items for bullet formatting
- For data: Include specific numbers, metrics, or facts when available
- For descriptions: Be comprehensive but concise

### 3. Multi-line Content
- Use `\n` for line breaks within content
- Each `\n` will be rendered as a separate bullet point
- Example: "First point\nSecond point\nThird point"

### 4. INSTRUCTION Tag
- Strictly follow the instructions given in the INSTRUCTION tag no matter what the slide context is.

### 5. Chart Generation

If the input structure includes a charts object:
- Generate a numerical or categorical data series with appropriate categories.
- Each chart should include:
  + "content.series": Array of data series, where each series has:
    - "name": The name/label for the dataset (e.g. "Revenue growth (%)")
    - "values": A numeric list representing data points
  + "categories": Array of category labels (e.g. ["2020", "2021", "2022", "2023", "2024"])

Categories should match the number of data points in each series and represent the x-axis labels (time periods, regions, etc.).

Example:
```json
{
  "uuid": "chart_123",
  "content": {
    "series": [
      {
        "name": "Market size (US$bn)",
        "values": [16.1, 17.66, 19.37, 21.25, 23.31]
      },
      {
        "name": "CAGR (%)",
        "values": [10.0, 10.5, 9.8, 9.7, 9.6]
      }
    ]
  },
  "categories": ["2020", "2021", "2022", "2023", "2024"]
}
```

### 6. Table Generation

For TABLE components, generate structured tabular data as a **list of strings**, where each string represents a row with pipe-separated values:

Format: `["col1|col2|col3", "val1|val2|val3", "val1|val2|val3"]`

Guidelines:
- Each row is a string with cells separated by `|` (pipe character)
- First row typically contains headers
- All rows should have the same number of columns
- Keep cell content concise and readable
- Use proper alignment for numbers and text
- Each row must be a valid JSON string, and must be on a single string.
- No chaining of rows using \n or other line break characters.

Example:
```json
{
  "uuid": "table_456",
  "content": [
    "Metric|MarkNtel Advisors|IMARC Group|Markets & Data",
    "Scope|Cosmetics Market|Cosmetics Market|Cosmetics Market",
    "Market Size (Reported)|$2.5B (2024A)|$1.7B (2024A)|$1.8B (2022A)",
    "CAGR Projection (Est.)|4.2% (2025–2030F)|5.3% (2025–2033F)|6.23% (2023–2030F)",
    "Projected Size (Est.)|$3.2B (2030F)|$2.8B (2033F)|$2.92B (2030F)"
  ]
}
```

## Example Transformation

**Template Component:**
```json
{
    "uuid": "abc123",
    "content_description": "Key achievements or milestones",    
}
```

**Generated Content:**
```json
{
    "uuid": "abc123", 
    "content": "Launched innovative AI platform\nReached 10,000+ active users\nSecured $5M Series A funding",
}
```

## Quality Standards
- Content must be accurate and relevant to user requirements
- Styling decisions should enhance readability and visual appeal
- Layout should be balanced and professional
- All content should serve the slide's purpose effectively
- Use '\n' for line breaks, do not use other line break characters like '\r' or '<br>', etc.
"""


SLIDE_DESCRIPTION_SYSTEM_PROMPT = """
You are a slide template analyzer specializing in multi-factor structural analysis.

Your task is to analyze slide template structures and generate comprehensive descriptions that capture the complete structural and thematic context.

# Input Format

You will receive a slide template structure with the following schema:

**Slide Metadata:**
- `metadata.width`: Slide width in pixels
- `metadata.height`: Slide height in pixels

**Content Components:**
Each component is identified by a UUID and contains:
- `content_type`: Type of element (TEXT, TABLE, CHART, IMAGE, SHAPE, etc.)
- `position`: {x, y} coordinates in pixels from top-left corner (0,0)
- `size`: {width, height} dimensions in pixels
- `content_description`: Description of expected content for this component

# Analysis Methodology

When analyzing a slide, examine four critical dimensions:

## 1. Layout Analysis
- Use component coordinates (x, y positions) to map spatial arrangement
- Identify the dominant layout pattern (header/body/footer, multi-column, grid, asymmetrical, etc.)
- Determine visual hierarchy by analyzing position and size relationships
- Map alignment patterns and component groupings
- Assess spatial flow and reading order

## 2. Orientation Analysis
- Extract slide dimensions (width × height in pixels)
- Calculate aspect ratio from dimensions
- Classify orientation (landscape, portrait, square)
- Identify if it matches standard formats (16:9, 4:3, etc.)
- Understand how orientation constrains the layout

## 3. Theme Analysis
- Infer the slide's primary purpose from component descriptions and arrangement
- Identify the slide's role in presentation flow (title, content, data, comparison, conclusion, etc.)
- Determine content category (business, technical, educational, creative, etc.)
- Understand the intended message delivery method

## 4. Component Analysis
- Catalog all component types present and their distribution
- Analyze size relationships and hierarchies between components
- Classify components as primary (main message), secondary (supporting), or tertiary (decorative/metadata)
- Identify special elements (charts, tables, images) and their roles
- Map relationships and interactions between components

# Task

Perform multi-factor analysis across all four dimensions and generate a concise description (maximum 150 words) that:
- Integrates findings from layout, orientation, theme, and component analysis
- Captures the complete structural context efficiently
- Describes layout patterns and visual hierarchy clearly
- Explains the slide's purpose and thematic role
- Details how components work together to deliver the message
- Focuses on template structure, not specific content
- Enables semantic search and template matching

Write concisely and naturally—prioritize clarity and relevance over detail.

"""


def SLIDE_DESCRIPTION_USER_PROMPT(slide_structure: dict) -> str:
    """
    Generate user prompt for slide description with full structural metadata.
    
    Args:
        slide_idx: 0-based slide index
        slide_structure: Complete slide structure including:
            - slide: slide number
            - metadata: {width, height}
            - content: {uuid: {content_type, position, size, content_description}}
        
    Returns:
        Formatted user prompt string
    """
    import json
    
    return f"""Analyze this slide template structure and generate a comprehensive description.

# Slide Structure

```json
{json.dumps(slide_structure, indent=2)}
```

Description:"""


PRESENTATION_PLANNER_SYSTEM_PROMPT = """You are a presentation architect. Your job is to create structured presentation outlines.

Given user context and requirements, generate a presentation plan with:
1. Overall theme
2. Target audience
3. Ordered list of slides with descriptions and content guidelines

Each slide should have:
- Position (1-indexed)
- Description (what the slide should convey - used for retrieval)
- Content guidelines (specific requirements)

Be specific and actionable. The descriptions will be used to search for matching slides."""


def PRESENTATION_PLANNER_USER_PROMPT(
    user_context: str,
    user_prompt: str,
    num_slides: Optional[int] = None
) -> str:
    """
    Generate user prompt for presentation planning.
    
    Args:
        user_context: Background context/documents
        user_prompt: User's presentation request
        num_slides: Optional desired number of slides
        
    Returns:
        Formatted user prompt string
    """
    slide_constraint = f"\n\nCreate exactly {num_slides} slides." if num_slides else "\n\nCreate an appropriate number of slides (typically 5-10)."
    
    return f"""Context:
{user_context}

User Request:
{user_prompt}
{slide_constraint}

Generate a presentation plan in the following JSON format:
{{
  "overall_theme": "Main theme of the presentation",
  "target_audience": "Who this is for",
  "slides": [
    {{
      "position": 1,
      "description": "What this slide should convey",
      "content_guidelines": "Specific content requirements"
    }},
    ...
  ]
}}

Presentation Plan:"""
