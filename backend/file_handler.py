import os
import base64
import io
from PyPDF2 import PdfReader
from docx import Document

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
SUPPORTED_DOC_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}

# Model yang mendukung input visual
VISION_MODELS = {
    "gemini-2.0-flash", "gemini-2.5-flash-preview-05-20", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash",
    "gemini-2.0-flash-lite", "gemini-2.5-pro",
    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview",
    "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229",
    "claude-sonnet-4-20250514", "claude-3-7-sonnet-20250219"
}

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    text = "\n".join([p.text for p in doc.paragraphs])
    return text.strip()

def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore").strip()

def process_uploaded_file(filename: str, content_type: str, file_bytes: bytes) -> dict:
    """Proses file yang diupload dan kembalikan info yang diperlukan."""
    result = {
        "filename": filename,
        "content_type": content_type,
        "is_image": content_type in SUPPORTED_IMAGE_TYPES,
        "is_document": content_type in SUPPORTED_DOC_TYPES,
        "extracted_text": None,
        "base64_data": None,
    }
    
    if result["is_image"]:
        result["base64_data"] = base64.b64encode(file_bytes).decode("utf-8")
    
    if result["is_document"]:
        try:
            if content_type == "application/pdf":
                result["extracted_text"] = extract_text_from_pdf(file_bytes)
            elif "wordprocessingml" in content_type:
                result["extracted_text"] = extract_text_from_docx(file_bytes)
            elif content_type == "text/plain":
                result["extracted_text"] = extract_text_from_txt(file_bytes)
        except Exception as e:
            result["extracted_text"] = f"[Gagal mengekstrak teks: {str(e)}]"
    
    return result

def model_supports_vision(model: str) -> bool:
    """Cek apakah model mendukung input gambar."""
    model_lower = model.lower()
    for vm in VISION_MODELS:
        if vm.lower() in model_lower or model_lower in vm.lower():
            return True
    return False
