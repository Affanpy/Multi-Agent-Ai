import asyncio
import re
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import AsyncSessionLocal
from models import Agent, Session, Message
from config import MAX_HISTORY_MESSAGES, uploaded_files_cache
from orchestrator import determine_speaking_order
from agent_runner import run_agent_stream
from debate_manager import active_debates

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 10000  # Batas panjang pesan user


def _validate_chat_data(data: dict) -> dict | str:
    """Validasi dan sanitasi payload chat dari WebSocket.
    Returns dict yang sudah bersih, atau string error message jika invalid."""
    
    # Content: harus string non-kosong
    content = data.get("content")
    if not isinstance(content, str) or not content.strip():
        return "Content harus berupa teks yang tidak kosong."
    content = content.strip()
    if len(content) > MAX_CONTENT_LENGTH:
        return f"Pesan terlalu panjang (maks {MAX_CONTENT_LENGTH} karakter)."
    
    # is_private: harus boolean
    is_private = data.get("is_private", False)
    if not isinstance(is_private, bool):
        is_private = False
    
    # target_agent_id: opsional, harus string atau None
    target_agent_id = data.get("target_agent_id")
    if target_agent_id is not None and not isinstance(target_agent_id, str):
        target_agent_id = str(target_agent_id)
    
    # Private chat harus punya target
    if is_private and not target_agent_id:
        return "Private chat membutuhkan target_agent_id."
    
    # reply_to_agent_id: opsional, harus string atau None
    reply_to_agent_id = data.get("reply_to_agent_id")
    if reply_to_agent_id is not None and not isinstance(reply_to_agent_id, str):
        reply_to_agent_id = str(reply_to_agent_id)
    
    # moderator_enabled: harus boolean
    moderator_enabled = data.get("moderator_enabled", True)
    if not isinstance(moderator_enabled, bool):
        moderator_enabled = True
    
    # file_id: opsional, harus string atau None
    file_id = data.get("file_id")
    if file_id is not None and not isinstance(file_id, str):
        file_id = None
    
    return {
        "content": content,
        "is_private": is_private,
        "target_agent_id": target_agent_id,
        "reply_to_agent_id": reply_to_agent_id,
        "moderator_enabled": moderator_enabled,
        "file_id": file_id,
    }


async def process_chat_message(session_id, data, manager):
    """Orchestrator utama. Dipanggil dari WS handler saat type='chat'.
    Membuat fresh DB session per pesan untuk menghindari stale data."""
    
    # Validasi input
    validated = _validate_chat_data(data)
    if isinstance(validated, str):
        logger.warning(f"Invalid chat data dari session {session_id}: {validated}")
        await manager.broadcast(session_id, {"type": "error", "content": validated})
        return
    
    user_msg_content = validated["content"]
    is_private = validated["is_private"]
    target_agent_id = validated["target_agent_id"]
    moderator_enabled = validated["moderator_enabled"]
    reply_to_agent_id = validated["reply_to_agent_id"]
    file_id = validated["file_id"]
    
    # Resolve file data dari cache
    file_data = uploaded_files_cache.pop(file_id) if file_id else None
    
    async with AsyncSessionLocal() as db:
        # Simpan pesan user
        user_msg = await _save_user_message(session_id, user_msg_content, is_private, target_agent_id, db)
        
        # Resolve reply agent name untuk broadcast
        reply_agent_name = await _resolve_reply_agent_name(reply_to_agent_id, db)
        
        # Broadcast pesan user
        await _broadcast_user_message(
            session_id, user_msg_content, user_msg, file_data,
            reply_agent_name, is_private, target_agent_id, manager
        )
        
        # Jika sesi ini sedang dalam mode debat, hentikan proses biasa di sini.
        # Pesan interupsi user sudah tersimpan di DB dan akan terbaca oleh agen debat selanjutnya di background.
        if session_id in active_debates:
            return
        
        # Ambil active agents
        agent_res = await db.execute(select(Agent).where(Agent.is_active == True).order_by(Agent.order.asc()))
        active_agents = list(agent_res.scalars().all())
        if not active_agents:
            await manager.broadcast(session_id, {"type": "error", "content": "No active agents available"})
            return
            
        agents_dict = {
             a.id: {
                 "id": a.id, "name": a.name, "role": a.role, "soul": a.soul,
                 "system_prompt": a.system_prompt, "provider": a.provider,
                 "model": a.model, "api_key_encrypted": a.api_key_encrypted,
                 "temperature": a.temperature, "max_tokens": a.max_tokens,
                 "avatar_emoji": a.avatar_emoji
             } for a in active_agents
        }
        
        # Build chat history
        raw_history = await _build_chat_history(session_id, is_private, target_agent_id, agents_dict, db)
        
        # Resolve speaking order
        speaking_order, context_hints = await _resolve_speaking_order(
            session_id, is_private, target_agent_id, reply_to_agent_id,
            moderator_enabled, user_msg_content, active_agents, agents_dict,
            raw_history, manager
        )
        
        # Execute agent round
        await _execute_agent_round(
            session_id, speaking_order, agents_dict, raw_history,
            context_hints, is_private, target_agent_id, active_agents,
            file_data, db, manager
        )
        
        await manager.broadcast(session_id, {"type": "round_complete"})


async def _save_user_message(session_id, content, is_private, target_agent_id, db):
    """Simpan pesan user ke DB + update judul session."""
    user_msg = Message(
        session_id=session_id, 
        role="user", 
        content=content, 
        is_private=is_private, 
        target_agent_id=target_agent_id
    )
    db.add(user_msg)
    
    res_session = await db.execute(select(Session).where(Session.id == session_id))
    sess = res_session.scalars().first()
    if sess and sess.title == "New Session":
         sess.title = content[:30] + ("..." if len(content) > 30 else "")
    
    await db.commit()
    return user_msg


async def _resolve_reply_agent_name(reply_to_agent_id, db):
    """Resolve nama agen untuk reply indicator."""
    if not reply_to_agent_id:
        return None
    _reply_res = await db.execute(select(Agent).where(Agent.id == reply_to_agent_id))
    _reply_agent = _reply_res.scalars().first()
    return _reply_agent.name if _reply_agent else None


async def _broadcast_user_message(session_id, content, user_msg, file_data, reply_agent_name, is_private, target_agent_id, manager):
    """Broadcast pesan user ke semua client."""
    await manager.broadcast(session_id, {
        "type": "user_message",
        "content": content,
        "timestamp": user_msg.timestamp.isoformat(),
        "is_private": is_private,
        "target_agent_id": target_agent_id,
        "reply_to_agent_name": reply_agent_name,
        "file_info": {
            "filename": file_data["filename"],
            "is_image": file_data["is_image"],
            "is_document": file_data["is_document"],
            "base64_data": file_data.get("base64_data") if file_data.get("is_image") else None,
            "content_type": file_data.get("content_type")
        } if file_data else None
    })


async def _build_chat_history(session_id, is_private, target_agent_id, agents_dict, db):
    """Bangun riwayat chat dari DB."""
    history_res = await db.execute(
        select(Message).where(Message.session_id == session_id)
        .order_by(Message.timestamp.desc()).limit(MAX_HISTORY_MESSAGES)
    )
    chat_history_db = list(reversed(list(history_res.scalars().all())))
    
    raw_history = []
    for m in chat_history_db:
        # Filter cerdas memori privat
        if m.is_private:
            if not is_private or str(m.target_agent_id) != str(target_agent_id):
                continue
                
        if m.role == "user":
            raw_history.append({"role": "user", "name": "User", "content": m.content})
        elif m.role == "agent":
            agent_name = agents_dict[m.agent_id]["name"] if m.agent_id in agents_dict else "Agent"
            raw_history.append({"role": "agent", "agent_id": str(m.agent_id), "name": agent_name, "content": m.content})
    
    return raw_history


async def _resolve_speaking_order(session_id, is_private, target_agent_id, reply_to_agent_id, moderator_enabled, user_msg_content, active_agents, agents_dict, raw_history, manager):
    """Tentukan urutan agen yang akan merespons."""
    if is_private:
         speaking_order = [target_agent_id] if target_agent_id in agents_dict else []
         context_hints = {target_agent_id: "PERINGATAN KRITIS: Kamu ditarik ke obrolan 1-on-1 private. Jawab langsung secara spesifik pesannya, ini rahasia, ABAIKAN jalannya grup."}
    elif reply_to_agent_id and reply_to_agent_id in agents_dict:
         # Reply langsung: bypass moderator, hanya agen target yang menjawab
         speaking_order = [reply_to_agent_id]
         reply_agent_name = agents_dict[reply_to_agent_id]["name"]
         context_hints = {reply_to_agent_id: f"User secara khusus membalas pesanmu dan mengarahkan pertanyaan ini langsung padamu. Jawab secara langsung dan fokus."}
         # Update broadcast agar frontend tahu ini reply
         await manager.broadcast(session_id, {
              "type": "moderator_decision",
              "speaking_order": speaking_order,
              "reasoning": f"User membalas langsung ke {reply_agent_name}"
         })
    elif not moderator_enabled:
         # Mode Sequential: Semua agen menjawab berurutan tanpa moderator
         speaking_order = [a.id for a in active_agents]
         context_hints = {}
         await manager.broadcast(session_id, {
              "type": "moderator_decision",
              "speaking_order": speaking_order,
              "reasoning": "Moderator dinonaktifkan — semua agen menjawab berurutan."
         })
    else:
         mod_decision = await determine_speaking_order(
              active_agents=[agents_dict[aid] for aid in agents_dict],
              user_message=user_msg_content,
              recent_history=raw_history[-10:]
         )
         speaking_order = mod_decision.get("speaking_order", [])
         context_hints = mod_decision.get("context_hints", {})
         await manager.broadcast(session_id, {
              "type": "moderator_decision",
              "speaking_order": speaking_order,
              "reasoning": mod_decision.get("reasoning", "")
         })
    
    return speaking_order, context_hints


async def _execute_agent_round(session_id, speaking_order, agents_dict, raw_history, context_hints, is_private, target_agent_id, active_agents, file_data, db, manager):
    """Eksekusi streaming untuk setiap agen dalam urutan."""
    for aid in speaking_order:
         if aid not in agents_dict: continue
         
         agent_info = agents_dict[aid]
         await manager.broadcast(session_id, {
             "type": "agent_typing",
             "agent_id": aid,
             "agent_name": agent_info["name"],
             "agent_emoji": agent_info["avatar_emoji"]
         })
         
         hint = context_hints.get(aid, "")
         collected_tokens = []
         
         try:
             async for token in run_agent_stream(agent_info, raw_history, hint, file_data=file_data):
                  collected_tokens.append(token)
                  await manager.broadcast(session_id, {
                       "type": "agent_stream",
                       "agent_id": aid,
                       "token": token,
                       "is_private": is_private,
                       "target_agent_id": target_agent_id
                  })
                  await asyncio.sleep(0.01)
         except Exception as e:
             # Fix #5: Error Handling Graceful Fallback
             error_msg = f"\n[System: {agent_info['name']} mengalami gangguan koneksi API. Berlanjut ke agen berikutnya...]"
             collected_tokens.append(error_msg)
             await manager.broadcast(session_id, {
                 "type": "agent_stream",
                 "agent_id": aid,
                 "token": error_msg,
                 "is_private": is_private,
                 "target_agent_id": target_agent_id
             })
         
         full_message = "".join(collected_tokens)
         
         # Fix #2: Post-Processing Regex Filter untuk membuang Prefix Halusinasi
         full_message = _post_process_agent_message(full_message, active_agents)
         
         agent_msg = Message(
             session_id=session_id, 
             role="agent", 
             agent_id=aid, 
             content=full_message,
             is_private=is_private,
             target_agent_id=target_agent_id
         )
         db.add(agent_msg)
         await db.commit()
         
         raw_history.append({
             "role": "agent",
             "agent_id": str(aid),
             "name": agent_info["name"],
             "content": full_message
         })
         
         await manager.broadcast(session_id, {
              "type": "agent_done",
              "agent_id": aid,
              "agent_name": agent_info["name"],
              "agent_emoji": agent_info["avatar_emoji"],
              "full_message": full_message,
              "timestamp": agent_msg.timestamp.isoformat(),
              "is_private": is_private,
              "target_agent_id": target_agent_id
         })


def _post_process_agent_message(full_message, active_agents):
    """Bersihkan prefix halusinasi dari respons agen."""
    all_names = [a.name for a in active_agents]
    for name in all_names:
        # Hapus pola seperti [Nama]: atau Nama: atau **Nama**: di awal baris baru
        pattern = rf'(?m)^\s*\[?{re.escape(name)}\]?\s*[::]\s*|^\s*\*{{1,2}}{re.escape(name)}\*{{1,2}}\s*[::]\s*'
        full_message = re.sub(pattern, '', full_message, flags=re.IGNORECASE).strip()
        
    # Bersihkan format pemisah seperti '---' di awal pesan yang sering terbawa
    full_message = re.sub(r'^(?:---\s*|\n)+', '', full_message).strip()
    
    return full_message
