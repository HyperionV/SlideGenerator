"""
Slide Library Composition Orchestrator

Orchestrates dynamic presentation composition by coordinating planning,
retrieval, merging, and content generation.
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
import sys

from .load_and_merge import PPTXSlideManager
from .slide_generation import PresentationProcessor

from .schemas import PresentationPlan, SlideOutlineItem
from .planner import SlidePlannerAgent
from .retrieval import SlideRetrievalService
from .storage import SlideStorageAdapter

logger = logging.getLogger(__name__)

# Backoff retry configuration
MAX_RETRIES = 3
BACKOFF_BASE = 2.0  # Exponential backoff base (seconds)


class SlideCompositionOrchestrator:
    """
    Orchestrates dynamic presentation composition.
    
    Workflow:
    1. Generate presentation plan (SlidePlannerAgent)
    2. For each slide in plan:
       - Retrieve matching slide (with backoff retry)
       - If all retries fail: use default template
    3. Merge slides into single presentation
    4. Generate content (PresentationProcessor)
    5. Return final PPTX
    """
    
    def __init__(
        self,
        planner: SlidePlannerAgent,
        retriever: SlideRetrievalService,
        storage: SlideStorageAdapter,
        default_template_path: Optional[str] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            planner: Slide planner agent
            retriever: Slide retrieval service
            storage: Storage adapter
            default_template_path: Path to default template slide (optional)
        """
        self.planner = planner
        self.retriever = retriever
        self.storage = storage
        self.default_template_path = default_template_path
        
        print("SlideCompositionOrchestrator initialized")
    
    async def compose_presentation(
        self,
        user_context: str,
        user_prompt: str,
        output_dir: str = "output",
        num_slides: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Complete dynamic composition pipeline.
        
        Args:
            user_context: Background context/documents
            user_prompt: User's presentation request
            output_dir: Output directory for final PPTX
            num_slides: Optional desired number of slides
            
        Returns:
            Dict with output file paths
        """
        print("Starting dynamic presentation composition")
        
        # Step 1: Generate presentation plan
        print("Step 1: Generating presentation plan")
        plan = await self.planner.generate_plan(
            user_context=user_context,
            user_prompt=user_prompt,
            num_slides=num_slides
        )
        
        print(f"Plan generated: {len(plan.slides)} slides")
        print(f"Theme: {plan.overall_theme}")
        
        # Step 2: Retrieve slides for each outline item
        print("Step 2: Retrieving slides")
        slide_paths = []
        
        for outline_item in plan.slides:
            print(f"Retrieving slide {outline_item.position}: {outline_item.description}")
            
            # Retrieve with backoff retry
            slide_path = await self._retrieve_slide_with_retry(outline_item)
            
            if slide_path:
                slide_paths.append(slide_path)
                print(f"✅ Retrieved slide {outline_item.position}")
            else:
                print(f"⚠️  No slide found for position {outline_item.position}")
        
        if not slide_paths:
            raise ValueError("No slides retrieved - cannot create presentation")
        
        print(f"Retrieved {len(slide_paths)}/{len(plan.slides)} slides")
        
        # Step 3: Merge slides
        print("Step 3: Merging slides")
        merged_path = await self._merge_slides(slide_paths, output_dir)
        
        # Step 4: Generate content
        print("Step 4: Generating content")
        result = await self._generate_content(
            merged_pptx_path=merged_path,
            plan=plan,
            user_context=user_context,
            output_dir=output_dir
        )
        
        print("✅ Dynamic composition complete")
        return result
    
    async def _retrieve_slide_with_retry(
        self,
        outline_item: SlideOutlineItem
    ) -> Optional[Path]:
        """
        Retrieve a slide with exponential backoff retry.
        
        Retry strategy:
        1. Try retrieval
        2. If fails: Wait BACKOFF_BASE^attempt seconds, retry
        3. After MAX_RETRIES: Use default template
        
        Args:
            outline_item: Slide specification
            
        Returns:
            Path to retrieved/default slide, or None
        """
        for attempt in range(MAX_RETRIES):
            try:
                # Search for matching slide
                results = await self.retriever.search_slides_simple(
                    query=outline_item.description,
                    limit=1
                )
                
                if results:
                    # Download slide
                    metadata = results[0]
                    _, slide_path = await self.storage.get_slide_by_id(metadata.slide_id)
                    print(f"Retrieved: {metadata.description[:50]}...")
                    return slide_path
                else:
                    print(f"No results for: {outline_item.description}")
                    
                    # Exponential backoff
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BACKOFF_BASE ** attempt
                        print(f"Retry {attempt + 1}/{MAX_RETRIES} after {wait_time}s")
                        await asyncio.sleep(wait_time)
                    
            except Exception as e:
                print(f"Retrieval attempt {attempt + 1} failed: {e}")
                
                # Exponential backoff
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_BASE ** attempt
                    print(f"Retry {attempt + 1}/{MAX_RETRIES} after {wait_time}s")
                    await asyncio.sleep(wait_time)
        
        # All retries failed - use default template
        print(f"All retries failed for: {outline_item.description}")
        
        if self.default_template_path and Path(self.default_template_path).exists():
            print(f"Using default template: {self.default_template_path}")
            return Path(self.default_template_path)
        else:
            print("No default template available")
            return None
    
    async def _merge_slides(
        self,
        slide_paths: List[Path],
        output_dir: str
    ) -> Path:
        """
        Merge slides into a single presentation.
        
        Args:
            slide_paths: List of paths to single-slide PPTX files
            output_dir: Output directory
            
        Returns:
            Path to merged presentation
        """
        from spire.presentation import Presentation
        
        # Create new presentation
        merged_prs = Presentation()
        
        # Copy dimensions from first slide
        if slide_paths:
            from load_and_merge import PPTXLoader
            first_loader = PPTXLoader(str(slide_paths[0]))
            PPTXSlideManager.copy_presentation_dimensions(
                first_loader.get_presentation(),
                merged_prs
            )
            first_loader.dispose()
        
        # Copy each slide
        for slide_path in slide_paths:
            loader = PPTXLoader(str(slide_path))
            PPTXSlideManager.copy_slide(
                source_prs=loader.get_presentation(),
                source_slide_index=0,  # Single-slide PPTX
                target_prs=merged_prs
            )
            loader.dispose()
        
        # Remove default blank slide if present
        if merged_prs.Slides.Count > len(slide_paths):
            merged_prs.Slides.RemoveAt(0)
        
        # Save merged presentation
        output_path = Path(output_dir) / "merged_template.pptx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        PPTXSlideManager.save_presentation(merged_prs, str(output_path))
        merged_prs.Dispose()
        
        print(f"Merged {len(slide_paths)} slides to: {output_path}")
        return output_path
    
    async def _generate_content(
        self,
        merged_pptx_path: Path,
        plan: PresentationPlan,
        user_context: str,
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate content for merged presentation.
        
        Uses existing PresentationProcessor in fixed mode.
        
        Args:
            merged_pptx_path: Path to merged template
            plan: Presentation plan
            user_context: User context
            output_dir: Output directory
            
        Returns:
            Dict with output file paths
        """
        # Enrich context with plan information
        enriched_context = f"""Presentation Plan:
Theme: {plan.overall_theme}
Audience: {plan.target_audience}

Slides:
"""
        for slide in plan.slides:
            enriched_context += f"{slide.position}. {slide.description}\n   Guidelines: {slide.content_guidelines}\n"
        
        enriched_context += f"\n\nContext:\n{user_context}"
        
        # Use PresentationProcessor in fixed mode
        processor = PresentationProcessor(
            pptx_path=str(merged_pptx_path),
            user_input=plan.overall_theme,
            documents=enriched_context,
            output_dir=output_dir
        )
        
        result = await processor.execute()
        
        print(f"Content generation complete: {result}")
        return result
