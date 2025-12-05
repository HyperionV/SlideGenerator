import asyncio
import json
import os
from typing import Dict, Any

from utils.utils import (
    export_slide_structure,
    save_structure_to_file,
    apply_content_to_presentation,
    normalize_presentation,
    clear_all_alt_text,
)
from utils.schemas import (
    ContentReasoningResponse,
    ContentItem,
    ChartMetadata,
    ChartSeries
)
from prompts import (
    CONTENT_REASONING_PROMPT,
    CONTENT_REASONING_SCHEMA,
    CONTENT_GENERATION_PROMPT,
    CONTENT_GENERATION_SCHEMA
)
from models.vertex import vertexai_model


class PresentationProcessor:
    """
    Centralized processor for PowerPoint presentation content generation workflow.
    Handles the complete pipeline from normalization to final output generation.
    """

    def __init__(self, pptx_path: str, user_input: str, documents: str = "", output_dir: str = "output"):
        self.pptx_path = pptx_path
        self.user_input = user_input
        self.documents = documents
        self.output_dir = output_dir

        self.presentation = None
        self.content_mapping = None
        self.slide_structures = None
        self.reasoning_results = None
        self.updated_mapping = None
        self.generated_content = None
        self.merged_mapping = None
        self.final_structure = None

    async def execute(self) -> Dict[str, str]:
        """
        Execute the complete presentation processing pipeline.

        Returns:
            Dictionary with paths to all output files
        """
        print(f"Starting presentation processing for: {self.pptx_path}")

        await self._normalize_presentation()
        self._export_slide_structure()
        await self._process_slides_with_reasoning()
        self._update_content_mapping()
        await self._generate_content()
        self._merge_generated_content()
        self._export_final_structure()
        return self._save_outputs()

    async def _normalize_presentation(self) -> None:
        """Load and normalize the presentation content."""
        self.presentation, self.content_mapping = normalize_presentation(self.pptx_path)

    def _export_slide_structure(self) -> None:
        """Export slide structures for processing."""
        self.slide_structures = export_slide_structure(self.content_mapping)

    async def _process_slides_with_reasoning(self) -> None:
        """Process all slides concurrently with reasoning."""
        tasks = [self._generate_content_description(slide_data) for slide_data in self.slide_structures]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Exception in slide {i+1}: {result}")
                fallback = ContentReasoningResponse(
                    slide=i+1,
                    description="Error processing slide",
                    content={}
                )
                valid_results.append(fallback)
            else:
                valid_results.append(result)

        self.reasoning_results = valid_results

    async def _generate_content_description(self, slide_data: Dict[str, Any]) -> ContentReasoningResponse:
        """
        Process a single slide with reasoning.

        Args:
            slide_data: Dictionary containing slide structure data

        Returns:
            ContentReasoningResponse with reasoning content descriptions
        """
        try:
            slide_json = json.dumps(slide_data, indent=2, ensure_ascii=False)

            response_text = await vertexai_model(
                system=CONTENT_REASONING_PROMPT,
                user=slide_json,
                temperature=0.2,
                model="gemini-2.5-flash-preview-09-2025",
                thinking_config=True,
                schema=CONTENT_REASONING_SCHEMA,
                extra_config={
                    "top_p": 0.3,
                    "top_k": 20,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.05,
                }
            )

            if slide_data["slide"] == 2:
                print(response_text)

            response_data = json.loads(response_text)

            return ContentReasoningResponse(
                slide=response_data["slide"],
                description=response_data["description"],
                content=response_data["content"]
            )

        except Exception as e:
            print(f"Error processing slide {slide_data.get('slide', 'unknown')}: {e}")
            return ContentReasoningResponse(
                slide=slide_data.get("slide", 0),
                description="Error processing slide",
                content={}
            )

    def _update_content_mapping(self) -> None:
        """Update content mapping with reasoning results."""
        for result in self.reasoning_results:
            for slide_content in self.content_mapping.slides:
                if result.slide == slide_content.slide:
                    if not slide_content.description:
                        slide_content.description = result.description
                    for content_item_data in result.content:
                        uuid = content_item_data["uuid"]
                        if uuid in slide_content.content:
                            existing_item = slide_content.content[uuid]
                            updated_item = ContentItem(
                                original_content=existing_item.original_content,
                                content_type=existing_item.content_type,
                                position=existing_item.position,
                                size=existing_item.size,
                                font=existing_item.font,
                                content_description= ("<i>" in existing_item.original_content and existing_item.original_content) or content_item_data["content_description"],
                                table_style=existing_item.table_style,  # Preserve table styling
                            )
                            slide_content.content[uuid] = updated_item

        self.updated_mapping = self.content_mapping

    def _extract_slide_data_for_generation(self, slide_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract slide data for content generation, removing original_content to prevent bias.

        Args:
            slide_content: Slide content dictionary from structure

        Returns:
            Cleaned slide data without original_content
        """
        cleaned_content = {}
        for uuid, component in slide_content["content"].items():
            cleaned_component = {
                "uuid": uuid,
                "content_type": component["content_type"],
                "content_description": component["content_description"],
            }
            cleaned_content[uuid] = cleaned_component

        return {
            "slide": slide_content["slide"],
            "description": slide_content["description"],
            "content": cleaned_content
        }

    async def _generate_slide_content(self, slide_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate content for a single slide using AI reasoning.

        Args:
            slide_data: Cleaned slide data without original_content

        Returns:
            Generated content with styling decisions
        """

        print(f"Processing slide {slide_data['slide']}")

        try:
            input_data = f"""
<user_input>
{self.user_input}
</user_input>

<slide_data>
{json.dumps(slide_data, indent=2, ensure_ascii=False)}
</slide_data>

<documents>
{self.documents}
</documents>

            """

            response_text = await vertexai_model(
                system=CONTENT_GENERATION_PROMPT,
                user=input_data,
                temperature=0.65,
                model="gemini-2.5-flash-preview-09-2025",
                schema=CONTENT_GENERATION_SCHEMA,
                thinking_config=True,
                extra_config={
                    "top_p": 0.85,
                    "top_k": 40,
                    "frequency_penalty": 0.15,
                    "presence_penalty": 0.1,
                }
            )

            if slide_data["slide"] == 2:
                print(response_text)

            response_data = json.loads(response_text)
            return response_data

        except Exception as e:
            print(f"Error generating content for slide {slide_data.get('slide', 'unknown')}: {e}")
            # Return fallback structure
            return {
                "slide": slide_data.get("slide", 0),
                "description": slide_data.get("description", "Error generating content"),
                "content": []
            }

    async def _generate_content(self) -> None:
        """Generate content for all slides concurrently."""
        slide_structures = []
        for slide_content in self.updated_mapping.slides:
            slide_data = self._extract_slide_data_for_generation(slide_content.model_dump())
            slide_structures.append(slide_data)

        # Process all slides concurrently
        tasks = [self._generate_slide_content(slide_data) for slide_data in slide_structures]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Exception in slide {i+1}: {result}")
                # Create fallback response
                fallback = {
                    "slide": i+1,
                    "description": "Error generating content",
                    "content": []
                }
                valid_results.append(fallback)
            else:
                valid_results.append(result)

        self.generated_content = valid_results

    def _merge_generated_content(self) -> None:
        """Merge generated content back into the presentation structure."""
        for generated_slide in self.generated_content:
            slide_num = generated_slide["slide"]

            # Find corresponding slide in mapping
            for slide_content in self.updated_mapping.slides:
                if slide_content.slide == slide_num:
                    if not slide_content.description:
                        slide_content.description = generated_slide["description"]

                    # Handle regular content components
                    for component_data in generated_slide["content"]:
                        uuid = component_data["uuid"]

                        if uuid in slide_content.content:
                            existing_item = slide_content.content[uuid]

                            updated_item = ContentItem(
                                original_content=existing_item.original_content,
                                content_type=existing_item.content_type,
                                position=existing_item.position,
                                size=existing_item.size,
                                font=existing_item.font,
                                content_description=existing_item.content_description,
                                content=component_data["content"],
                                table_style=existing_item.table_style,  # Preserve table styling
                            )

                            slide_content.content[uuid] = updated_item

                    # Handle chart components separately
                    if "charts" in generated_slide:
                        for chart_data in generated_slide["charts"]:

                            print(chart_data)
                            
                            uuid = chart_data["uuid"]

                            if uuid in slide_content.content:

                                existing_item = slide_content.content[uuid]

                                chart_content = chart_data["content"]
                                categories = chart_data.get("categories", [])
                                series_list = []

                                for series in chart_content["series"]:
                                    series_obj = ChartSeries(
                                        name=series["name"],
                                        values=series["values"]
                                    )
                                    series_list.append(series_obj)

                                chart_metadata = ChartMetadata(series=series_list, categories=categories)

                                updated_item = ContentItem(
                                    original_content=existing_item.original_content,
                                    content_type=existing_item.content_type,
                                    position=existing_item.position,
                                    size=existing_item.size,
                                    font=existing_item.font,
                                    content_description=existing_item.content_description,
                                    content=chart_metadata,
                                )

                                slide_content.content[uuid] = updated_item

        self.merged_mapping = self.updated_mapping

    def _export_final_structure(self) -> None:
        """Export the final merged structure."""
        self.final_structure = export_slide_structure(self.merged_mapping)

    def _save_outputs(self) -> Dict[str, str]:
        """Save all output files and return their paths."""
        os.makedirs(self.output_dir, exist_ok=True)

        # Save structure.json
        structure_path = os.path.join(self.output_dir, "structure.json")
        save_structure_to_file(self.final_structure, structure_path)

        base_name = os.path.splitext(os.path.basename(self.pptx_path))[0]

        normalized_pptx_path = os.path.join(self.output_dir, f"{base_name}_normalized.pptx")
        self.presentation.save(normalized_pptx_path)
        
        generated_pptx_path = os.path.join(self.output_dir, f"{base_name}_generated.pptx")
        apply_content_to_presentation(self.presentation, self.merged_mapping, generated_pptx_path)
        
        clear_all_alt_text(self.presentation)
        
        self.presentation.save(generated_pptx_path)

        print("Processing completed successfully!")

        return {
            "structure_json": structure_path,
            "normalized_pptx": [],
            "generated_pptx": generated_pptx_path,
            "original_pptx": self.pptx_path
        }


async def process_presentation_flow(
    pptx_path: str,
    user_input: str,
    documents: str = "",
    output_dir: str = "output"
) -> Dict[str, str]:
    """
    Main flow for processing PowerPoint presentation with AI reasoning and content generation.
    Now uses the centralized PresentationProcessor class.

    Args:
        pptx_path: Path to the input PowerPoint file
        user_input: User requirements and context for content generation
        documents: Reference documents and materials
        output_dir: Directory to save output files

    Returns:
        Dictionary with paths to output files
    """
    processor = PresentationProcessor(pptx_path, user_input, documents, output_dir)
    return await processor.execute()


if __name__ == "__main__":
    input_file = "input/input_1.pptx"
    output_directory = "output"
    user_input = "Create a discussion material consisting of 3 slides - Company Research, Industry Research, and Investment Hightlights"
    
    with open("input/report.md", "r") as f:
        documents = f.read()
    
    try:
        result_paths = asyncio.run(process_presentation_flow(input_file, user_input, documents, output_directory))
        print("Processing completed successfully!")
        print(f"Structure JSON: {result_paths['structure_json']}")
        print(f"Normalized PPTX: {result_paths['normalized_pptx']}")
        print(f"Generated PPTX: {result_paths['generated_pptx']}")
    except Exception as e:
        print(f"Error in processing: {e}")
