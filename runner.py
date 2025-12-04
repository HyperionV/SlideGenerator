from slide_library.storage import SlideStorageAdapter
from slide_library.ingestion import SlideIngestionService
import asyncio
from pathlib import Path
from slide_library import SlideStorageAdapter, SlideRetrievalService

async def ingest_presentation():
    # Initialize storage
    storage = SlideStorageAdapter()
    await storage.initialize()

    # Ingest presentation
    ingestion = SlideIngestionService(storage)
    slides = await ingestion.ingest_presentation("legacy/input/input_1.pptx")

    print(f"✅ Ingested {len(slides)} slides")
    for slide in slides:
        print(f"  📄 {slide.slide_id[:8]}... - {slide.description[:60]}...")

    await storage.close()


async def debug_download_slide(storage: SlideStorageAdapter, s3_key: str, output_dir: str = "output"):
    """
    Debug feature: Download the selected slide's source file to output folder.
    
    Args:
        storage: SlideStorageAdapter instance
        s3_key: S3 key of the file to download
        output_dir: Output directory (default: "output")
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Extract filename stem and ensure .pptx extension
    filename_stem = Path(s3_key).stem
    local_path = output_path / f"{filename_stem}.pptx"
    
    try:
        await storage.s3.download_file(s3_key, local_path)
        print(f"✅ Downloaded: {s3_key} -> {local_path}")
        return local_path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise


async def search_slides():
    storage = SlideStorageAdapter()
    await storage.initialize()

    retrieval = SlideRetrievalService(storage)

    results = await retrieval.search_slides(
        query="financial performance with revenue chart",
        limit=5
    )

    print(f"🔍 Found {len(results)} slides:")
    for metadata, score in results:
        print(f"  📊 Score: {score:.2f}")
        print(f"\tslide_id: {metadata.slide_id}")
        print(f"\tdescription: {metadata.description[:80]}...")
        print(f"\tsource_presentation: {metadata.source_presentation}")
    
    # Debug: Download the first result's source file
    if results:
        print("\n🐛 Debug: Downloading first result's source file...")
        first_metadata, _ = results[0]
        s3_key = first_metadata.storage_ref.s3_key
        await debug_download_slide(storage, s3_key)

    await storage.close()

# asyncio.run(search_slides())
asyncio.run(ingest_presentation())