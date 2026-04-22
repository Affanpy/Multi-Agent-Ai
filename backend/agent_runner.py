from typing import AsyncGenerator, Dict, List
from providers import get_provider
from security import decrypt_api_key
from file_handler import model_supports_vision

SYSTEM_TEMPLATE = """Kamu adalah {name}, seorang {role}.

KEPRIBADIAN & CARA BICARA:
{soul}

INSTRUKSI PENTING:
- Kamu sedang berada di sebuah ruang diskusi grup bersama agent AI lain dengan keahlian berbeda.
- Selalu jawab dari sudut pandang peranmu sebagai {role}.
- Baca dan pertimbangkan semua pesan sebelumnya dalam diskusi, termasuk respons dari agent lain.
- Tambahkan perspektif unikmu berdasarkan keahlianmu — jangan hanya mengulang yang sudah dikatakan.
- Boleh setuju, tidak setuju, atau memperluas ide dari agent lain — seperti diskusi tim nyata.
- Gunakan bahasa yang natural, bukan format laporan kaku.
- Panjang respons: 3-6 paragraf, cukup substansial tapi tidak bertele-tele.
- **PERINGATAN KRITIS TRANSSKRIP**: JANGAN PERNAH mengawali jawabanmu dengan tulisan "[{name}]:" atau prefix semacamnya! Langsung keluarkan inti jawabanmu. 
- **PERINGATAN KRITIS HALUSINASI**: DILARANG KERAS menirukan orang lain atau membuat percakapan palsu. Kamu HANYA boleh berbicara sebagai dirimu sendiri untuk 1 giliran ini! JANGAN melanjutkan percakapan atas nama agent lain.

KONTEKS TAMBAHAN DARI MODERATOR:
{moderator_hint}

KONTEKS AGENT:
{system_prompt}
"""

def _build_message_content_with_file(text: str, file_data: dict, model: str, provider: str) -> any:
    """Buat konten pesan yang mencakup file (gambar/dokumen)."""
    
    # Jika file adalah dokumen, selalu sertakan teks yang diekstrak
    if file_data.get("is_document") and file_data.get("extracted_text"):
        doc_context = f"\n\n[📄 Dokumen: {file_data['filename']}]\n---\n{file_data['extracted_text'][:3000]}\n---"
        return text + doc_context
    
    # Jika file adalah gambar
    if file_data.get("is_image") and file_data.get("base64_data"):
        if model_supports_vision(model):
            # Model mendukung vision → return format multimodal
            return {
                "type": "multimodal",
                "text": text,
                "image_base64": file_data["base64_data"],
                "content_type": file_data["content_type"]
            }
        else:
            # Model tidak mendukung vision → fallback teks
            return text + f"\n\n[📷 User mengirim gambar: {file_data['filename']}. Model ini tidak mendukung input visual. Jawab berdasarkan konteks percakapan yang ada.]"
    
    return text

async def run_agent_stream(
    agent_data: Dict,
    chat_history: List[Dict],
    moderator_hint: str = "",
    file_data: dict = None
) -> AsyncGenerator[str, None]:
    provider_name = agent_data.get("provider")
    model = agent_data.get("model")
    enc_key = agent_data.get("api_key_encrypted")
    api_key = decrypt_api_key(enc_key)
    
    if not api_key:
        yield f"[System: No API configured for {agent_data.get('name')}]"
        return
        
    system_prompt = SYSTEM_TEMPLATE.format(
        name=agent_data.get("name"),
        role=agent_data.get("role"),
        soul=agent_data.get("soul"),
        moderator_hint=moderator_hint or 'Tidak ada konteks khusus.',
        system_prompt=agent_data.get("system_prompt")
    )
    
    provider_inst = get_provider(provider_name)
    
    mapped_history = []
    for msg in chat_history:
        if msg.get("role") == "user":
            content = f"User Manusia: {msg['content']}"
            # Cek apakah pesan ini memiliki file attachment
            if msg.get("file_data") and msg == chat_history[-1]:
                # Hanya pesan terakhir yang membawa file data aktual
                content = _build_message_content_with_file(content, msg["file_data"], model, provider_name)
            
            if isinstance(content, dict) and content.get("type") == "multimodal":
                mapped_history.append({"role": "user", "content": content})
            else:
                mapped_history.append({"role": "user", "content": content})
        elif msg.get("role") == "agent":
            if str(msg.get("agent_id")) == str(agent_data["id"]):
                mapped_history.append({"role": "model", "content": msg["content"]})
            else:
                mapped_history.append({"role": "user", "content": f"{msg['name']} (Agent Timmu): {msg['content']}"})
    
    # Jika ada file data yang dikirim langsung (untuk pesan terbaru)
    if file_data and len(mapped_history) > 0:
        last_msg = mapped_history[-1]
        if last_msg["role"] == "user" and isinstance(last_msg["content"], str):
            new_content = _build_message_content_with_file(last_msg["content"], file_data, model, provider_name)
            mapped_history[-1]["content"] = new_content
    
    async for chunk in provider_inst.generate_stream(
        api_key=api_key,
        model=model,
        system_prompt=system_prompt,
        messages=mapped_history,
        temperature=agent_data.get("temperature", 0.7),
        max_tokens=agent_data.get("max_tokens", 1024)
    ):
        yield chunk
