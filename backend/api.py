# uvicorn api:app --reload --host 0.0.0.0 --port 8000

from fastapi import BackgroundTasks, FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from utils.schemas import SlideLibraryMetadata
import os
import tempfile
from pathlib import Path

from orchestrator import SlideLibraryOrchestrator


app = FastAPI(title="Slide Agent API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = SlideLibraryOrchestrator()


async def _ensure_storage():
    # Ensure storage backends are ready before direct access
    await orchestrator._ensure_initialized()  # noqa: SLF001


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    retrieval_limit: int = 20
    return_scores: bool = True


class ComposeRequest(BaseModel):
    user_context: str
    user_prompt: str
    output_dir: str = "output"
    num_slides: int | None = None


class GenerateRequest(BaseModel):
    user_input: str
    documents: str = ""
    output_dir: str = "output"


@app.get("/health")
async def health():
    return {"status": "ok"}


async def _save_upload(file: UploadFile, suffix: str = "") -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    fd, path = tempfile.mkstemp(suffix=suffix or "")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(await file.read())
        return path
    except Exception:
        os.remove(path)
        raise


@app.post("/slides/ingest")
async def ingest_slide(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported")

    temp_path = await _save_upload(file, suffix=".pptx")
    try:
        slides = await orchestrator.execute(mode="ingest", pptx_path=temp_path)
        return {"count": len(slides), "slides": [s.model_dump() for s in slides]}
    finally:
        os.remove(temp_path)


@app.post("/slides/search")
async def search_slides(payload: SearchRequest):
    results = await orchestrator.execute(
        mode="search",
        query=payload.query,
        limit=1,
        retrieval_limit=5,
        return_scores=payload.return_scores,
    )

    if payload.return_scores:
        return [
            {"metadata": meta.model_dump(), "score": score}
            for meta, score in results
        ]
    return [meta.model_dump() for meta in results]


@app.get("/slides")
async def list_slides(skip: int = 0, limit: int = 50):
    await _ensure_storage()
    limit = max(1, min(limit, 200))

    collection = orchestrator.storage.mongo.get_collection(  # type: ignore[attr-defined]
        orchestrator.storage.collection_name,  # type: ignore[attr-defined]
        orchestrator.storage.database_name,  # type: ignore[attr-defined]
    )

    cursor = (
        collection.find({}, sort=[("updated_at", -1)])
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)

    # Normalize Mongo ObjectIds and ensure JSON-safe payloads
    items = []
    for doc in docs:
        doc.pop("_id", None)
        try:
            items.append(SlideLibraryMetadata(**doc).model_dump())
        except Exception:
            # Fallback: best-effort serialization
            doc["slide_id"] = str(doc.get("slide_id") or doc.get("id") or "")
            items.append(doc)

    return {"count": len(items), "items": items}


@app.get("/slides/{slide_id}/download")
async def download_slide(slide_id: str):
    await _ensure_storage()
    try:
        metadata, local_path = await orchestrator.storage.get_slide_by_id(slide_id)  # type: ignore[attr-defined]
    except ValueError:
        raise HTTPException(status_code=404, detail="Slide not found") from None

    background = BackgroundTasks()
    background.add_task(Path(local_path).unlink, missing_ok=True)

    return FileResponse(
        path=local_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=orchestrator.storage.get_download_filename(metadata),  # type: ignore[attr-defined]
        background=background,
    )


@app.get("/slides/{slide_id}/preview")
async def download_preview(slide_id: str):
    await _ensure_storage()

    doc = await orchestrator.storage.mongo.read(  # type: ignore[attr-defined]
        collection_name=orchestrator.storage.collection_name,  # type: ignore[attr-defined]
        query={"slide_id": slide_id},
        database_name=orchestrator.storage.database_name,  # type: ignore[attr-defined]
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Slide not found")

    preview_key = doc.get("preview")
    if not preview_key:
        raise HTTPException(status_code=404, detail="No preview available")

    local_path = Path(f"temp/previews/{Path(preview_key).name or slide_id}.png")
    await orchestrator.storage.s3.download_file(preview_key, local_path)  # type: ignore[attr-defined]

    background = BackgroundTasks()
    background.add_task(local_path.unlink, missing_ok=True)

    return FileResponse(
        path=local_path,
        media_type="image/png",
        filename=f"{slide_id}.png",
        background=background,
    )


@app.post("/generation/compose")
async def compose(payload: ComposeRequest):
    result = await orchestrator.execute(
        mode="compose",
        user_context=payload.user_context,
        user_prompt=payload.user_prompt,
        output_dir=payload.output_dir,
        num_slides=payload.num_slides,
    )
    return result


@app.post("/generation/generate")
async def generate(
    payload: str = Form(...),
    template: UploadFile = File(...),
):
    if not template.filename.lower().endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Template must be a .pptx file")

    temp_path = await _save_upload(template, suffix=".pptx")
    try:
        try:
            payload_data = GenerateRequest.model_validate_json(payload)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid payload JSON") from None

        result = await orchestrator.execute(
            mode="generate",
            pptx_path=temp_path,
            user_input=payload_data.user_input,
            documents=payload_data.documents,
            output_dir=payload_data.output_dir,
        )
        return result
    finally:
        os.remove(temp_path)


@app.get("/files")
async def download_file(path: str):
    # Serve files only from within the project directory (e.g., output/)
    root = Path.cwd().resolve()
    target = (Path(path).resolve())
    if not str(target).startswith(str(root)):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    background = BackgroundTasks()
    return FileResponse(
        path=target,
        filename=target.name,
        background=background,
    )


@app.on_event("shutdown")
async def shutdown_event():
    await orchestrator.close()

