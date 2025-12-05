"""
Slide Library Unified Orchestrator

Unified interface for all slide library operations with mode-based execution.
Supports: ingest, search, compose, and generate modes.
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Literal

from utils.load_and_merge import PPTXLoader, PPTXSlideManager
from core.slide_generation import PresentationProcessor
from utils.schemas import (
    PresentationPlan, 
    SlideOutlineItem,
    SlideLibraryMetadata
)
from core.planner import SlidePlannerAgent
from core.retrieval import SlideRetrievalService
from core.storage import SlideStorageAdapter
from core.ingestion import SlideIngestionService

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BACKOFF_BASE = 2.0  # Exponential backoff base (seconds)

# Mode type
Mode = Literal["ingest", "search", "compose", "generate"]


class SlideLibraryOrchestrator:
    """
    Unified orchestrator for all slide library operations.
    
    Modes:
    - 'ingest': Ingest presentations into the library
    - 'search': Search for slides semantically
    - 'compose': Compose presentations from library slides (dynamic mode)
    - 'generate': Generate content for existing template (fixed mode)
    
    This provides a single, consistent interface for all slide library functionality.
    """
    
    def __init__(
        self,
        storage: Optional[SlideStorageAdapter] = None,
        default_template_path: Optional[str] = None,
        auto_initialize: bool = True
    ):
        """
        Initialize unified orchestrator.
        
        Args:
            storage: Storage adapter (if None, creates new instance)
            default_template_path: Path to default template slide (optional)
            auto_initialize: Whether to auto-initialize storage on first use
        """
        self.storage = storage
        self.default_template_path = default_template_path
        self.auto_initialize = auto_initialize
        self._initialized = False
        
        # Lazy-initialized services
        self._ingestion = None
        self._retrieval = None
        self._planner = None
        
        logger.info("SlideLibraryOrchestrator initialized")
    
    async def _ensure_initialized(self):
        """Ensure storage and services are initialized."""
        if self._initialized:
            return
        
        # Create storage if not provided
        if self.storage is None:
            self.storage = SlideStorageAdapter()
        
        # Initialize storage
        if self.auto_initialize:
            await self.storage.initialize()
        
        # Initialize services
        self._ingestion = SlideIngestionService(self.storage)
        self._retrieval = SlideRetrievalService(self.storage)
        self._planner = SlidePlannerAgent()
        
        self._initialized = True
        logger.info("Orchestrator services initialized")
    
    async def execute(
        self,
        mode: Mode,
        **kwargs
    ) -> Any:
        """
        Execute operation based on mode.
        
        Args:
            mode: Operation mode ('ingest', 'search', 'compose', 'generate')
            **kwargs: Mode-specific parameters
            
        Returns:
            Mode-specific results
            
        Raises:
            ValueError: If mode is invalid or required parameters missing
        """
        await self._ensure_initialized()
        
        if mode == "ingest":
            return await self._execute_ingest(**kwargs)
        elif mode == "search":
            return await self._execute_search(**kwargs)
        elif mode == "compose":
            return await self._execute_compose(**kwargs)
        elif mode == "generate":
            return await self._execute_generate(**kwargs)
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be one of: ingest, search, compose, generate")
    
    async def _execute_ingest(
        self,
        pptx_path: str,
        **kwargs
    ) -> List[SlideLibraryMetadata]:
        """
        Execute ingestion mode.
        
        Args:
            pptx_path: Path to presentation file
            
        Returns:
            List of ingested slide metadata
        """
        logger.info(f"[INGEST] Ingesting presentation: {pptx_path}")
        
        slides = await self._ingestion.ingest_presentation(pptx_path)
        
        logger.info(f"[INGEST] ✅ Ingested {len(slides)} slides")
        return slides
    
    async def _execute_search(
        self,
        query: str,
        limit: int = 5,
        retrieval_limit: int = 20,
        return_scores: bool = True,
        **kwargs
    ) -> List[Tuple[SlideLibraryMetadata, float]] | List[SlideLibraryMetadata]:
        """
        Execute search mode.
        
        Args:
            query: Search query
            limit: Maximum results to return
            retrieval_limit: Candidates to retrieve before reranking
            return_scores: Whether to return relevance scores
            
        Returns:
            List of (metadata, score) tuples or just metadata
        """
        logger.info(f"[SEARCH] Query: '{query}' (limit: {limit})")
        
        if return_scores:
            results = await self._retrieval.search_slides(
                query=query,
                limit=limit,
                retrieval_limit=retrieval_limit
            )
        else:
            results = await self._retrieval.search_slides_simple(
                query=query,
                limit=limit
            )
        
        logger.info(f"[SEARCH] ✅ Found {len(results)} slides")
        return results
    
    async def _execute_compose(
        self,
        user_context: str,
        user_prompt: str,
        output_dir: str = "output",
        num_slides: Optional[int] = None,
        **kwargs
    ) -> Dict[str, str]:
        """
        Execute compose mode (dynamic composition from library).
        
        Args:
            user_context: Background context/documents
            user_prompt: User's presentation request
            output_dir: Output directory
            num_slides: Desired number of slides (optional)
            
        Returns:
            Dict with output file paths
        """
        logger.info(f"[COMPOSE] Starting dynamic composition")
        logger.info(f"[COMPOSE] Prompt: {user_prompt}")
        
        # Step 1: Generate presentation plan
        logger.info("[COMPOSE] Step 1/4: Generating plan")
        plan = await self._planner.generate_plan(
            user_context=user_context,
            user_prompt=user_prompt,
            num_slides=num_slides
        )
        
        logger.info(f"[COMPOSE] Plan: {len(plan.slides)} slides - {plan.overall_theme}")
        
        # Step 2: Retrieve slides
        logger.info("[COMPOSE] Step 2/4: Retrieving slides")
        slide_paths = []
        
        for outline_item in plan.slides:
            slide_path = await self._retrieve_slide_with_retry(outline_item)
            if slide_path:
                slide_paths.append(slide_path)
                logger.info(f"[COMPOSE] ✅ Slide {outline_item.position}")
            else:
                logger.warning(f"[COMPOSE] ⚠️  No slide for position {outline_item.position}")
        
        if not slide_paths:
            raise ValueError("No slides retrieved - cannot create presentation")
        
        logger.info(f"[COMPOSE] Retrieved {len(slide_paths)}/{len(plan.slides)} slides")
        
        # Step 3: Merge slides
        logger.info("[COMPOSE] Step 3/4: Merging slides")
        merged_path = Path(output_dir) / "merged_template.pptx"
        
        target_loader = PPTXLoader(str(slide_paths[0]))
        target_prs = target_loader.get_presentation()
        
        for slide_path in slide_paths[1:]:
            loader = PPTXLoader(str(slide_path))
            PPTXSlideManager.copy_slide(
                source_prs=loader.get_presentation(),
                source_slide_index=0,
                target_prs=target_prs
            )
            loader.dispose()
        
        PPTXSlideManager.save_presentation(target_prs, str(merged_path))
        target_loader.dispose()
        logger.info(f"Merged {len(slide_paths)} slides to: {merged_path}")
        
        # Step 4: Generate content
        logger.info("[COMPOSE] Step 4/4: Generating content")
        result = await self._generate_content(
            merged_pptx_path=merged_path,
            plan=plan,
            user_context=user_context,
            output_dir=output_dir
        )
        
        logger.info("[COMPOSE] ✅ Composition complete")
        return result
    
    async def _execute_generate(
        self,
        pptx_path: str,
        user_input: str,
        documents: str = "",
        output_dir: str = "output",
        **kwargs
    ) -> Dict[str, str]:
        """
        Execute generate mode (fixed template generation).
        
        Args:
            pptx_path: Path to template PPTX
            user_input: User's content request
            documents: Context documents
            output_dir: Output directory
            
        Returns:
            Dict with output file paths
        """
        logger.info(f"[GENERATE] Processing template: {pptx_path}")
        logger.info(f"[GENERATE] User input: {user_input}")
        
        processor = PresentationProcessor(
            pptx_path=pptx_path,
            user_input=user_input,
            documents=documents,
            output_dir=output_dir
        )
        
        result = await processor.execute()
        
        logger.info("[GENERATE] ✅ Generation complete")
        return result
    
    async def _retrieve_slide_with_retry(
        self,
        outline_item: SlideOutlineItem
    ) -> Optional[Path]:
        """
        Retrieve a slide with exponential backoff retry.
        
        Args:
            outline_item: Slide specification
            
        Returns:
            Path to retrieved/default slide, or None
        """
        for attempt in range(MAX_RETRIES):
            try:
                results = await self._retrieval.search_slides_simple(
                    query=outline_item.description,
                    limit=1
                )
                
                if results:
                    metadata = results[0]
                    _, slide_path = await self.storage.get_slide_by_id(metadata.slide_id)
                    logger.debug(f"Retrieved: {metadata.description[:50]}...")
                    return slide_path
                else:
                    logger.debug(f"No results for: {outline_item.description}")
                    
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BACKOFF_BASE ** attempt
                        logger.debug(f"Retry {attempt + 1}/{MAX_RETRIES} after {wait_time}s")
                        await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Retrieval attempt {attempt + 1} failed: {e}")
                
                if attempt < MAX_RETRIES - 1:
                    wait_time = BACKOFF_BASE ** attempt
                    await asyncio.sleep(wait_time)
        
        # All retries failed - use default template
        logger.warning(f"All retries failed for: {outline_item.description}")
        
        if self.default_template_path and Path(self.default_template_path).exists():
            logger.info(f"Using default template: {self.default_template_path}")
            return Path(self.default_template_path)
        else:
            logger.warning("No default template available")
            return None
    
    async def _generate_content(
        self,
        merged_pptx_path: Path,
        plan: PresentationPlan,
        user_context: str,
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate content for merged presentation.
        
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
        
        # Use PresentationProcessor
        processor = PresentationProcessor(
            pptx_path=str(merged_pptx_path),
            user_input=plan.overall_theme,
            documents=enriched_context,
            output_dir=output_dir
        )
        
        result = await processor.execute()
        
        logger.info(f"Content generation complete")
        return result
    
    async def close(self):
        """Close storage connections."""
        if self.storage and self._initialized:
            await self.storage.close()
            logger.info("Orchestrator closed")
