import os
import json
import re
import logging
from typing import List, Dict, Any
from providers import get_provider

# Setup logging
logger = logging.getLogger(__name__)

MODERATOR_PROVIDER = os.getenv("MODERATOR_PROVIDER", "anthropic")
MODERATOR_MODEL = os.getenv("MODERATOR_MODEL", "claude-3-5-haiku-20241022")
MODERATOR_API_KEY = os.getenv("MODERATOR_API_KEY")

MODERATOR_PROMPT = """Kamu adalah Moderator diskusi AI. Tugasmu adalah mengatur giliran bicara agent dalam diskusi grup.

Daftar agent aktif:
{agent_list_json}

Pesan terbaru dari user:
"{user_message}"

Riwayat diskusi singkat (3 pesan terakhir):
{recent_history}

Tentukan urutan agent yang harus merespons pesan ini. Pilih berdasarkan relevansi keahlian mereka terhadap topik. Tidak semua agent harus bicara — pilih yang paling relevan (minimal 1, maksimal semua). 

Berikan output HANYA dalam format JSON berikut, tanpa penjelasan tambahan atau markdown block:
{{
  "speaking_order": ["agent_id"],
  "context_hints": {{"agent_id": "hint singkat"}},
  "reasoning": "alasan singkat pemilihan urutan"
}}"""

async def determine_speaking_order(
    active_agents: List[Dict],
    user_message: str,
    recent_history: List[Dict]
) -> Dict[str, Any]:
    agents_summary = [{"id": str(a["id"]), "name": a["name"], "role": a["role"]} for a in active_agents]
    history_str = json.dumps(recent_history, ensure_ascii=False, indent=2)
    agents_str = json.dumps(agents_summary, ensure_ascii=False, indent=2)
    
    system_prompt = MODERATOR_PROMPT.format(
        agent_list_json=agents_str,
        user_message=user_message,
        recent_history=history_str
    )
    
    if not MODERATOR_API_KEY:
        return {
             "speaking_order": [str(a["id"]) for a in active_agents],
             "context_hints": {},
             "reasoning": "Fallback order because Moderator API key is missing."
        }

    try:
        provider_inst = get_provider(MODERATOR_PROVIDER)
    except ValueError:
        return {"speaking_order": [str(a["id"]) for a in active_agents], "context_hints": {}}

    try:
        response_text = await provider_inst.generate(
            api_key=MODERATOR_API_KEY,
            model=MODERATOR_MODEL,
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": "Tentukan urutannya sekarang dalam JSON murni."}],
            temperature=0.2,
            max_tokens=600
        )
        
        # Ekstraksi JSON — gunakan non-greedy match untuk menghindari tangkapan berlebih
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            return dict(data)
        else:
            logger.error(f"Moderator memberikan respons non-JSON: {response_text}")
            raise ValueError("No JSON block found in response")
            
    except Exception as e:
        logger.error(f"Error calling moderator: {e}")
        return {
             "speaking_order": [str(a["id"]) for a in active_agents],
             "context_hints": {},
             "reasoning": f"Error running moderator: {str(e)}"
        }

SUMMARY_PROMPT = """Kamu adalah asisten yang ahli merangkum diskusi.

Berikut adalah transkrip lengkap diskusi antara user dan beberapa AI agent:

{chat_transcript}

Buatkan rangkuman komprehensif dari diskusi di atas dalam format Markdown berikut:

## 📊 Rangkuman Diskusi

### 📌 Topik Utama
(Jelaskan topik utama yang dibahas dalam 1-2 kalimat)

### 💡 Poin-Poin Kunci
(Daftar poin kunci dari setiap agent, sertakan nama agent)

### ✅ Keputusan / Kesepakatan
(Hal-hal yang sudah disepakati atau diputuskan, jika ada)

### ⏳ Belum Terselesaikan
(Hal-hal yang masih diperdebatkan atau perlu ditindaklanjuti, jika ada)

### 🎯 Rekomendasi
(Saran atau langkah selanjutnya berdasarkan diskusi)

Pastikan rangkuman ringkas tetapi mencakup semua informasi penting. Gunakan bahasa yang sama dengan diskusi (biasanya Indonesia)."""

async def generate_summary(chat_history: list) -> str:
    transcript_parts = []
    for m in chat_history:
        if m["role"] == "user":
            transcript_parts.append(f"**User**: {m['content']}")
        else:
            name = m.get("name", "Agent")
            transcript_parts.append(f"**{name}**: {m['content']}")
    
    transcript = "\n\n".join(transcript_parts)
    system_prompt = SUMMARY_PROMPT.format(chat_transcript=transcript)
    
    if not MODERATOR_API_KEY:
        return "⚠️ Tidak dapat menghasilkan rangkuman: API key moderator belum dikonfigurasi."

    try:
        provider_inst = get_provider(MODERATOR_PROVIDER)
    except ValueError:
        return "⚠️ Provider moderator tidak dikenali."

    try:
        response_text = await provider_inst.generate(
            api_key=MODERATOR_API_KEY,
            model=MODERATOR_MODEL,
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": "Rangkum diskusi di atas sekarang."}],
            temperature=0.3,
            max_tokens=2000
        )
        return response_text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"⚠️ Gagal menghasilkan rangkuman: {str(e)}"
