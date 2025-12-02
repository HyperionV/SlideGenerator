CONTENT_REASONING_PROMPT = f"""
## Objective
Analyze the provided slide content mapping and generate a **generalized template analysis** that describes the structural purpose and content guidelines—not the specific details of the original slide.

## Output Format
Return a JSON object following this exact structure:

```json
{{
    "slide": "slide_num",
    "purpose": "high-level purpose this slide template serves",
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

### 3. Purpose Statement
- Describe what type of information this slide **category** communicates
- Examples: "Team overview slide", "Metrics dashboard", "Process workflow"

### 4. Component Analysis
- For each UUID, specify:
  - What **type** of content fits this component
  - What **function** it serves in the slide
  - Relevant examples where helpful

## Example Transformation

**Input (Specific):** "John Smith, CEO at Acme Corp"

**Output (Generalized):** "Executive profile with name and title (e.g., C-level position, founder, board member)"
"""

CONTENT_REASONING_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "slide": {
            "type": "NUMBER",
        },
        "purpose": {
            "type": "STRING",
        },
        "content": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {
                        "type": "STRING",
                    },
                    "content_description": {
                        "type": "STRING",
                    }
                }
            }
        }
    },
}


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
    "purpose": "updated purpose based on generated content",
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

CONTENT_GENERATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "slide": {"type": "NUMBER"},
        "purpose": {"type": "STRING"},
        "content": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {"type": "STRING"},
                    "content": {}  # Can be STRING (text) or ARRAY (list/table)
                },
                "required": ["uuid", "content"]
            }
        },
        "charts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {"type": "STRING"},
                    "content": {
                        "type": "OBJECT",
                        "properties": {
                            "series": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "name": {"type": "STRING"},
                                        "values": {
                                            "type": "ARRAY",
                                            "items": {"type": "NUMBER"}
                                        }
                                    },
                                    "required": ["name", "values"]
                                }
                            }
                        },
                        "required": ["series"]
                    },
                    "categories": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["uuid", "content", "categories"]
            }
        }
    },
    "required": ["slide", "purpose", "content"]
}