from fastapi import APIRouter, HTTPException, UploadFile, File as FastAPIFile

from config import uploaded_files_cache
from file_handler import process_uploaded_file, SUPPORTED_IMAGE_TYPES, SUPPORTED_DOC_TYPES

router = APIRouter(prefix="/api", tags=["uploads"])


@router.post("/upload")
async def upload_file(file: UploadFile = FastAPIFile(...)):
    content_type = file.content_type or ""
    
    if content_type not in SUPPORTED_IMAGE_TYPES and content_type not in SUPPORTED_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipe file tidak didukung: {content_type}. Gunakan gambar (PNG/JPG/WebP) atau dokumen (PDF/DOCX/TXT).")
    
    file_bytes = await file.read()
    
    # Max 10MB
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 10MB")
    
    file_data = process_uploaded_file(file.filename, content_type, file_bytes)
    
    # Simpan ke cache dengan unique ID
    file_id = uploaded_files_cache.generate_file_id(file.filename)
    uploaded_files_cache.put(file_id, file_data)
    
    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "content_type": content_type,
        "is_image": file_data["is_image"],
        "is_document": file_data["is_document"],
        "has_extracted_text": bool(file_data["extracted_text"]),
        "text_preview": (file_data["extracted_text"][:200] + "...") if file_data["extracted_text"] and len(file_data["extracted_text"]) > 200 else file_data.get("extracted_text"),
        "base64_preview": file_data["base64_data"][:100] + "..." if file_data["base64_data"] else None
    }


@router.get("/providers")
async def get_providers():
    return {
        "providers": [
             {"id": "openai", "name": "OpenAI"},
             {"id": "anthropic", "name": "Anthropic"},
             {"id": "gemini", "name": "Google Gemini"}
        ]
    }
