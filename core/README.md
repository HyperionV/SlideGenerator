# Slide Agent Core Module

This module implements the core flow for processing PowerPoint presentations with AI reasoning.

## Overview

The core flow processes PowerPoint files through the following steps:

1. **Load and Normalize**: Loads PPTX files and replaces text content with UUIDs
2. **Extract Structure**: Creates content mapping with position, size, font, and alignment data
3. **AI Reasoning**: Processes each slide concurrently using AI models to generate content descriptions
4. **Update Mapping**: Updates the content mapping with AI-generated descriptions
5. **Export Results**: Saves structure.json and normalized presentation

## Files

### `schemas.py`

Pydantic models for data validation:

- `Position`, `Size`, `Font`: Basic geometric and typography models
- `ContentItem`: Individual content elements with metadata
- `SlideContent`: Complete slide structure
- `PresentationMapping`: Full presentation structure
- `ContentReasoningResponse`: AI reasoning output format

### `utils.py`

Utility functions for PowerPoint processing:

- `replace_text_with_uuid()`: Main function for content normalization
- `export_slide_structure()`: Converts internal structure to JSON format
- `update_content()`: Updates presentation with new content
- `save_structure_to_file()`: Saves structure to JSON file
- `save_presentation()`: Saves presentation to file

### `flow.py`

Main processing flow with concurrent AI reasoning:

- `process_slide_with_ai()`: Processes single slide with AI
- `process_all_slides_concurrently()`: Concurrent processing of all slides
- `update_content_mapping_with_ai_results()`: Updates mapping with AI results
- `process_presentation_flow()`: Main async flow function
- `run_presentation_processing()`: Synchronous wrapper

### `prompts.py`

AI prompts and schemas:

- `CONTENT_REASONING_PROMPT`: System prompt for AI reasoning
- `CONTENT_REASONING_SCHEMA`: JSON schema for AI output validation

## Usage

```python
from core.flow import run_presentation_processing

# Process a PowerPoint file
result_paths = run_presentation_processing("input/presentation.pptx", "output")

print(f"Structure JSON: {result_paths['structure_json']}")
print(f"Normalized PPTX: {result_paths['normalized_pptx']}")
```

## Output Structure

The `structure.json` file contains:

- Slide metadata (width, height)
- Content mapping with UUIDs as keys
- Original content, position, size, alignment, font information
- AI-generated content descriptions

## Dependencies

- `python-pptx`: PowerPoint file processing
- `pydantic`: Data validation
- `asyncio`: Concurrent processing
- `google-genai`: AI model integration

## Configuration

The AI model configuration is in `vertexai/config.py` and requires:

- Google Cloud service account credentials
- GCP project ID and location
- Model selection (default: gemini-2.5-flash-preview-09-2025)
