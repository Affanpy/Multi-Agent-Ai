from typing import AsyncGenerator, Dict, List
from providers import get_provider
from security import decrypt_api_key

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

async def run_agent_stream(
    agent_data: Dict,
    chat_history: List[Dict],
    moderator_hint: str = ""
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
    
    provider_inst = get_provider(provider_name)
    
    mapped_history = []
    for msg in chat_history:
        if msg.get("role") == "user":
            mapped_history.append({"role": "user", "content": f"User Manusia: {msg['content']}"})
        elif msg.get("role") == "agent":
            if str(msg.get("agent_id")) == str(agent_data["id"]):
                mapped_history.append({"role": "model", "content": msg["content"]})
            else:
                mapped_history.append({"role": "user", "content": f"{msg['name']} (Agent Timmu): {msg['content']}"})
    
    async for chunk in provider_inst.generate_stream(
        api_key=api_key,
        model=model,
        system_prompt=system_prompt,
        messages=mapped_history,
        temperature=agent_data.get("temperature", 0.7),
        max_tokens=agent_data.get("max_tokens", 1024)
    ):
        yield chunk
