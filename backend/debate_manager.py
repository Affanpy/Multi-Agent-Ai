import asyncio
import re
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import AsyncSessionLocal
from models import Message, Agent
from agent_runner import run_agent_stream

active_debates: Dict[str, asyncio.Task] = {}

async def run_debate_loop(
    session_id: str, 
    topic: str, 
    agents_config: List[Dict[str, Any]], 
    max_rounds: int,
    manager
):
    try:
        # Pemanasan / Notifikasi awal ke frontend
        await manager.broadcast(session_id, {
            "type": "debate_system",
            "content": f"⚔️ **Arena Debat Dimulai!**\n**Topik:** {topic}\n**Ronde:** {max_rounds}"
        })
        
        # Simpan topik sebagai pesan sistem/user pertama jika belum ada konteks
        async with AsyncSessionLocal() as db:
            intro_msg = Message(
                session_id=session_id,
                role="user",
                content=f"[MODE DEBAT DIMULAI] Topik yang harus diperdebatkan: {topic}\nMari kita mulai ronde pertama.",
                is_private=False
            )
            db.add(intro_msg)
            await db.commit()
            
            # Broadcast intro
            await manager.broadcast(session_id, {
                "type": "user_message",
                "content": intro_msg.content,
                "timestamp": intro_msg.timestamp.isoformat(),
                "is_private": False
            })

        for round_idx in range(1, max_rounds + 1):
            await manager.broadcast(session_id, {
                "type": "debate_system",
                "content": f"🔔 **Ronde {round_idx} dimulai!**"
            })
            
            for agent_c in agents_config:
                agent_id = agent_c["agent_id"]
                stance = agent_c.get("stance", "bebas")
                
                async with AsyncSessionLocal() as db:
                    # Ambil data agen
                    agent_res = await db.execute(select(Agent).where(Agent.id == agent_id))
                    agent_db = agent_res.scalars().first()
                    if not agent_db:
                        continue
                        
                    # Ambil history terbaru (agar interupsi user terbaca)
                    history_res = await db.execute(select(Message).where(Message.session_id == session_id, Message.is_private == False).order_by(Message.timestamp.desc()).limit(20))
                    chat_history_db = list(reversed(list(history_res.scalars().all())))
                    
                    # Fetch all agents for name resolution
                    all_agents_res = await db.execute(select(Agent))
                    agents_dict = {a.id: {"name": a.name, "avatar_emoji": a.avatar_emoji} for a in all_agents_res.scalars().all()}
                    
                    raw_history = []
                    for m in chat_history_db:
                        if m.role == "user":
                            raw_history.append({"role": "user", "name": "User", "content": m.content})
                        elif m.role == "agent":
                            agent_name = agents_dict[m.agent_id]["name"] if m.agent_id in agents_dict else "Agent"
                            raw_history.append({"role": "agent", "agent_id": str(m.agent_id), "name": agent_name, "content": m.content})

                # Siapkan hint berdasarkan mode
                hint = f"Kamu sedang berada dalam Arena Debat. Topik debat: '{topic}'. Ini adalah Ronde {round_idx} dari {max_rounds}. "
                if stance == "pro":
                    hint += "Kamu BERADA DI PIHAK PRO/SETUJU. Pertahankan argumenmu dengan kuat!"
                elif stance == "kontra":
                    hint += "Kamu BERADA DI PIHAK KONTRA/TIDAK SETUJU. Serang argumen pro dengan tajam!"
                else:
                    hint += "Berdebatlah secara bebas sesuai dengan kepribadian dan pengetahuanmu."

                agent_info = {
                    "id": str(agent_db.id),
                    "name": agent_db.name,
                    "role": agent_db.role,
                    "soul": agent_db.soul,
                    "system_prompt": agent_db.system_prompt,
                    "provider": agent_db.provider,
                    "model": agent_db.model,
                    "api_key_encrypted": agent_db.api_key_encrypted,
                    "temperature": agent_db.temperature,
                    "max_tokens": agent_db.max_tokens,
                    "avatar_emoji": agent_db.avatar_emoji
                }

                # Broadcast agent is typing
                await manager.broadcast(session_id, {
                    "type": "agent_typing",
                    "agent_id": str(agent_db.id),
                    "agent_name": agent_db.name,
                    "agent_emoji": agent_db.avatar_emoji
                })

                collected_tokens = []
                try:
                    async for token in run_agent_stream(agent_info, raw_history, hint):
                        collected_tokens.append(token)
                        await manager.broadcast(session_id, {
                            "type": "agent_stream",
                            "agent_id": str(agent_db.id),
                            "token": token,
                            "is_private": False,
                            "target_agent_id": None
                        })
                        await asyncio.sleep(0.01)
                except Exception as e:
                    error_msg = f"\n[System: {agent_info['name']} mengalami gangguan koneksi API.]"
                    collected_tokens.append(error_msg)
                    await manager.broadcast(session_id, {
                        "type": "agent_stream",
                        "agent_id": str(agent_db.id),
                        "token": error_msg,
                        "is_private": False,
                        "target_agent_id": None
                    })

                full_message = "".join(collected_tokens)
                
                # Post-processing: hapus prefix halusinasi (sama seperti chat_service)
                full_message = _post_process_debate_message(full_message, agents_dict)
                
                # Simpan jawaban ke DB dan ambil timestamp di dalam session context
                async with AsyncSessionLocal() as db:
                    new_msg = Message(
                        session_id=session_id,
                        role="agent",
                        agent_id=agent_db.id,
                        content=full_message,
                        is_private=False
                    )
                    db.add(new_msg)
                    await db.commit()
                    # Ambil timestamp di sini, selagi masih dalam session context
                    msg_timestamp = new_msg.timestamp.isoformat()

                # Broadcast finalization (pakai timestamp yang sudah di-capture)
                await manager.broadcast(session_id, {
                    "type": "agent_done",
                    "agent_id": str(agent_db.id),
                    "agent_name": agent_info["name"],
                    "agent_emoji": agent_info["avatar_emoji"],
                    "full_message": full_message,
                    "timestamp": msg_timestamp,
                    "is_private": False,
                    "target_agent_id": None
                })

                # Jeda sejenak sebelum agen berikutnya
                await asyncio.sleep(2)

        # Penutup
        await manager.broadcast(session_id, {
            "type": "debate_system",
            "content": f"🏁 **Arena Debat Selesai!** Semua ronde telah dirampungkan."
        })
        
    except asyncio.CancelledError:
        await manager.broadcast(session_id, {
            "type": "debate_system",
            "content": f"🛑 **Debat dihentikan oleh pengguna.**"
        })
    finally:
        if session_id in active_debates:
            del active_debates[session_id]

def start_debate_task(session_id: str, data: dict, manager):
    """Mulai task background debat. Hentikan jika ada yang sedang berjalan."""
    stop_debate_task(session_id)
    
    topic = data.get("topic", "Topik Bebas")
    agents_config = data.get("agents_config", [])
    max_rounds = data.get("max_rounds", 3)
    
    task = asyncio.create_task(run_debate_loop(
        session_id=session_id,
        topic=topic,
        agents_config=agents_config,
        max_rounds=max_rounds,
        manager=manager
    ))
    active_debates[session_id] = task

def stop_debate_task(session_id: str):
    if session_id in active_debates:
        active_debates[session_id].cancel()
        del active_debates[session_id]


def _post_process_debate_message(full_message: str, agents_dict: dict) -> str:
    """Bersihkan prefix halusinasi dari respons agen debat."""
    all_names = [info["name"] for info in agents_dict.values()]
    for name in all_names:
        pattern = rf'(?m)^\s*\[?{re.escape(name)}\]?\s*[::]\s*|^\s*\*{{1,2}}{re.escape(name)}\*{{1,2}}\s*[::]\s*'
        full_message = re.sub(pattern, '', full_message, flags=re.IGNORECASE).strip()
    
    full_message = re.sub(r'^(?:---\s*|\n)+', '', full_message).strip()
    return full_message
