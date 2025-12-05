"""
Slide Library - Unified Runner

Demonstrates the unified SlideLibraryOrchestrator interface for all operations.
"""

import asyncio
from orchestrator import SlideLibraryOrchestrator


async def example_ingest():
    """Example 1: Ingest presentations into the library."""
    print("\n" + "="*60)
    print("EXAMPLE 1: INGEST MODE")
    print("="*60 + "\n")
    
    orchestrator = SlideLibraryOrchestrator()
    
    try:
        # Ingest presentation
        slides = await orchestrator.execute(
            mode="ingest",
            pptx_path="input/input_1.pptx"
        )
        
        print(f"\n✅ Ingested {len(slides)} slides:")
        for slide in slides:
            print(f"  📄 {slide.slide_id[:8]}... - {slide.description[:60]}...")
    
    finally:
        await orchestrator.close()


async def example_search():
    """Example 2: Search for slides semantically."""
    print("\n" + "="*60)
    print("EXAMPLE 2: SEARCH MODE")
    print("="*60 + "\n")
    
    orchestrator = SlideLibraryOrchestrator()
    
    try:
        # Search with scores
        results = await orchestrator.execute(
            mode="search",
            query="showcasing technology and features",
            limit=1,
            retrieval_limit=5,
            return_scores=True
        )
        
        print(f"\n🔍 Found {len(results)} slides:")
        for metadata, score in results:
            print(f"\n  📊 Score: {score:.2f}")
            print(f"     slide_id: {metadata.slide_id}")
            print(f"     description: {metadata.description[:80]}...")
            print(f"     source: {metadata.source_presentation}")
    
    finally:
        await orchestrator.close()


async def example_compose():
    """Example 3: Compose presentation from library (dynamic mode)."""
    print("\n" + "="*60)
    print("EXAMPLE 3: COMPOSE MODE (Dynamic)")
    print("="*60 + "\n")
    
    orchestrator = SlideLibraryOrchestrator(
        default_template_path="templates/default_slide.pptx"  # Optional fallback
    )

    with open("input/report.md", "r") as f:
        user_context = f.read()
    
    try:
        # Compose presentation from library
        result = await orchestrator.execute(
            mode="compose",
            user_context=user_context,
            user_prompt="Create a 2-slide investor update deck containing a slide for financial performance (should contain a chart) and a slide for introduction about MOI Cosmetics",
            output_dir="output",
            num_slides=2
        )
        
        print(f"\n✅ Generated presentation:")
        print(f"   Normalized: {result.get('normalized_pptx')}")
        print(f"   Structure: {result.get('structure_json')}")
        print(f"   Reasoning: {result.get('reasoning_json')}")
        print(f"   Final: {result.get('generated_pptx')}")
    
    finally:
        await orchestrator.close()


async def example_generate():
    """Example 4: Generate content for template (fixed mode)."""
    print("\n" + "="*60)
    print("EXAMPLE 4: GENERATE MODE (Fixed Template)")
    print("="*60 + "\n")
    
    orchestrator = SlideLibraryOrchestrator()
    
    try:
        # Generate content for existing template
        result = await orchestrator.execute(
            mode="generate",
            pptx_path="templates/my_template.pptx",
            user_input="Create Q4 investor update with financial highlights",
            documents="""
            Q4 2024 Performance:
            - Revenue: $10M (25% YoY growth)
            - New product: AI analytics platform
            - Market: Expanded to APAC
            """,
            output_dir="output"
        )
        
        print(f"\n✅ Generated presentation:")
        print(f"   Normalized: {result.get('normalized_pptx')}")
        print(f"   Structure: {result.get('structure_json')}")
        print(f"   Reasoning: {result.get('reasoning_json')}")
        print(f"   Final: {result.get('generated_pptx')}")
    
    finally:
        await orchestrator.close()


async def example_all_in_one():
    """Example 5: Use single orchestrator instance for multiple operations."""
    print("\n" + "="*60)
    print("EXAMPLE 5: UNIFIED INTERFACE - All Operations")
    print("="*60 + "\n")
    
    # Single orchestrator instance for all operations
    orchestrator = SlideLibraryOrchestrator()
    
    try:
        # 1. Ingest
        print("\n[1/3] Ingesting presentation...")
        slides = await orchestrator.execute(
            mode="ingest",
            pptx_path="input/input_1.pptx"
        )
        print(f"✅ Ingested {len(slides)} slides")
        
        # 2. Search
        print("\n[2/3] Searching slides...")
        results = await orchestrator.execute(
            mode="search",
            query="technology features",
            limit=3,
            return_scores=False  # Just metadata, no scores
        )
        print(f"✅ Found {len(results)} slides")
        for i, metadata in enumerate(results, 1):
            print(f"  {i}. {metadata.description[:60]}...")
        
        # 3. Compose (if library has enough slides)
        if len(results) >= 3:
            print("\n[3/3] Composing presentation...")
            result = await orchestrator.execute(
                mode="compose",
                user_context="Q4 update with tech highlights",
                user_prompt="Create 3-slide tech overview",
                output_dir="output",
                num_slides=3
            )
            print(f"✅ Generated: {result.get('generated_pptx')}")
        else:
            print("\n[3/3] Skipping compose (not enough slides in library)")
    
    finally:
        await orchestrator.close()


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    # Run individual examples (uncomment the one you want to test)
    
    # asyncio.run(example_ingest())
    # asyncio.run(example_search())
    asyncio.run(example_compose())
    # asyncio.run(example_generate())
    # asyncio.run(example_all_in_one())
