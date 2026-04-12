# MASTER PROMPT — AI Multi-Agent Brainstorming System
> Prompt ini dirancang untuk diberikan kepada AI coding assistant (Cursor, Claude, GPT-4, Gemini, dll) agar membangun sistem multi-agent chat secara lengkap dari awal.

---

## 🎯 KONTEKS & TUJUAN

Bangun sebuah **web application** bernama **"AgentRoom"** — sebuah platform brainstorming berbasis AI di mana beberapa AI agent dengan peran berbeda bisa berdiskusi satu sama lain secara real-time di dalam sebuah ruang chat bersama, seperti grup chat.

Pengguna adalah **seorang developer** yang menggunakan ini secara personal untuk sesi brainstorming ide dan strategi. Ia mampu menjalankan server lokal dan memodifikasi kode sendiri.

---

## 🏗️ ARSITEKTUR YANG HARUS DIBANGUN

### Stack Teknologi
- **Backend**: Python + FastAPI + WebSocket
- **Frontend**: React + TailwindCSS (single-page app)
- **Database**: SQLite (via SQLAlchemy) untuk menyimpan sesi & konfigurasi agent
- **AI Providers**: OpenAI, Anthropic (Claude), Google Gemini — semua via REST API
- **Package Manager**: pip (backend), npm (frontend)

### Struktur Folder
```
agentroom/
├── backend/
│   ├── main.py               # FastAPI entry point + WebSocket handler
│   ├── models.py             # SQLAlchemy models
│   ├── database.py           # DB connection & init
│   ├── agent_runner.py       # Logic memanggil AI API per agent
│   ├── orchestrator.py       # Moderator logic — mengatur giliran bicara
│   ├── providers/
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── gemini_provider.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── ChatRoom.jsx      # Halaman grup chat utama
│   │   │   └── AgentManager.jsx  # Halaman kelola agent
│   │   ├── components/
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── AgentCard.jsx
│   │   │   └── TypingIndicator.jsx
│   │   └── hooks/
│   │       └── useWebSocket.js
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

---

## 🤖 SISTEM AGENT

### Model Data Agent
Setiap agent memiliki properti berikut yang tersimpan di database:

```python
class Agent:
    id: str                  # UUID
    name: str                # Nama agent, misal "Ari - Developer"
    avatar_emoji: str        # Emoji representasi, misal "👨‍💻"
    role: str                # Judul peran singkat, misal "Senior Software Engineer"
    soul: str                # Kepribadian/cara bicara, misal "Pragmatis, suka detail teknis, kadang sarkastik"
    system_prompt: str       # Full system prompt yang dikirim ke AI
    provider: str            # "openai" | "anthropic" | "gemini"
    model: str               # misal "gpt-4o", "claude-3-5-sonnet-20241022", "gemini-1.5-pro"
    api_key: str             # API key untuk provider tersebut (disimpan terenkripsi)
    temperature: float       # 0.0 - 1.0
    max_tokens: int          # Batas token per respons
    is_active: bool          # Apakah agent aktif di room saat ini
    order: int               # Urutan bicara default
```

### System Prompt Template per Agent
Saat memanggil AI, gunakan format system prompt berikut:

```
Kamu adalah {name}, seorang {role}.

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

KONTEKS TAMBAHAN:
{system_prompt}
```

---

## 🎮 SISTEM MODERATOR (ORCHESTRATOR)

### Konsep
Ada satu agent khusus bernama **"Moderator"** yang bertugas mengatur giliran diskusi. Moderator **tidak bicara ke user**, tapi bekerja di balik layar.

### Cara Kerja Moderator

1. Saat user mengirim pesan baru ke grup, Moderator dipanggil pertama kali.
2. Moderator membaca pesan user + daftar agent yang aktif + topik diskusi.
3. Moderator menentukan:
   - **Urutan agent** yang akan merespons (tidak harus semua, tidak harus berurutan)
   - **Konteks khusus** yang perlu diperhatikan tiap agent (opsional hint)
4. Output Moderator adalah JSON:

```json
{
  "speaking_order": ["agent_id_1", "agent_id_2", "agent_id_3"],
  "context_hints": {
    "agent_id_1": "Fokus pada aspek teknis implementasi",
    "agent_id_2": "Pertimbangkan dari sisi user experience",
    "agent_id_3": "Evaluasi dari perspektif bisnis dan monetisasi"
  },
  "reasoning": "Urutan ini dipilih karena..."
}
```

5. Backend kemudian memanggil agent satu per satu sesuai urutan, dengan menambahkan `context_hint` ke system prompt masing-masing.

### Prompt Moderator
```
Kamu adalah Moderator diskusi AI. Tugasmu adalah mengatur giliran bicara agent dalam diskusi grup.

Daftar agent aktif:
{agent_list_json}

Pesan terbaru dari user:
"{user_message}"

Riwayat diskusi singkat (3 pesan terakhir):
{recent_history}

Tentukan urutan agent yang harus merespons pesan ini. Pilih berdasarkan relevansi keahlian mereka terhadap topik. Tidak semua agent harus bicara — pilih yang paling relevan (minimal 2, maksimal semua).

Berikan output HANYA dalam format JSON berikut, tanpa penjelasan tambahan:
{
  "speaking_order": ["agent_id"],
  "context_hints": {"agent_id": "hint singkat"},
  "reasoning": "alasan singkat pemilihan urutan"
}
```

---

## 💬 ALUR CHAT REAL-TIME (WebSocket)

### Flow Lengkap

```
User kirim pesan
       ↓
Backend terima via WebSocket
       ↓
Simpan pesan user ke DB
       ↓
Broadcast ke frontend: {type: "user_message", ...}
       ↓
Panggil Moderator API → dapat speaking_order
       ↓
Broadcast ke frontend: {type: "moderator_decision", speaking_order: [...]}
       ↓
Loop: untuk setiap agent_id dalam speaking_order:
  │
  ├─ Broadcast: {type: "agent_typing", agent_id: "..."}
  │
  ├─ Bangun context: semua pesan sebelumnya + hint dari moderator
  │
  ├─ Panggil API provider agent tersebut (stream jika memungkinkan)
  │
  ├─ Broadcast token per token: {type: "agent_stream", agent_id: "...", token: "..."}
  │
  ├─ Saat selesai: Broadcast {type: "agent_done", agent_id: "...", full_message: "..."}
  │
  └─ Simpan respons agent ke DB sebagai bagian dari history
       ↓
Setelah semua agent selesai:
Broadcast: {type: "round_complete"}
```

### Format Pesan WebSocket

```typescript
// Dari client ke server
interface ClientMessage {
  type: "chat" | "ping";
  content?: string;
  session_id: string;
}

// Dari server ke client
interface ServerMessage {
  type: "user_message" | "agent_typing" | "agent_stream" | "agent_done" | "moderator_decision" | "round_complete" | "error";
  agent_id?: string;
  agent_name?: string;
  agent_emoji?: string;
  content?: string;
  token?: string;
  speaking_order?: string[];
  session_id?: string;
  timestamp?: string;
}
```

---

## 🖥️ UI/UX FRONTEND

### Halaman 1: Chat Room (`/`)

**Layout**: Split panel
- **Kiri (25%)**: Sidebar daftar agent aktif di room, masing-masing tampil dengan emoji, nama, role, dan status (idle/typing/done)
- **Kanan (75%)**: Area chat utama

**Area Chat**:
- Setiap bubble pesan agent memiliki:
  - Header: `[emoji] Nama Agent — Role`
  - Body: teks respons (dengan streaming efek ketik)
  - Footer: timestamp + provider badge (misal "GPT-4o" atau "Claude")
- Pesan user tampil di sisi kanan dengan warna berbeda
- Saat agent sedang mengetik: tampilkan animated typing indicator dengan nama agent
- Saat moderator memutuskan urutan: tampilkan notifikasi kecil "🎯 Moderator mengatur giliran: Ari → Budi → Citra"

**Input Area**:
- Textarea dengan tombol kirim
- Toggle: "Kirim ke semua" vs "Sebut agent tertentu" (dengan @mention)
- Tombol: "Mulai Sesi Baru" dan "Simpan Sesi"

### Halaman 2: Agent Manager (`/agents`)

**Fitur**:
- Daftar semua agent yang pernah dibuat
- Tombol "Tambah Agent Baru" → buka form/modal
- Form agent berisi semua field: nama, emoji, role, soul, system prompt, provider, model, api key, temperature, max_tokens
- Toggle aktif/nonaktif agent per sesi
- Drag-and-drop untuk mengatur urutan default
- Preview: tombol "Test Agent" untuk kirim pesan test dan lihat respons

### Halaman 3: Session History (`/sessions`)

- Daftar sesi diskusi yang tersimpan (judul otomatis dari pesan pertama user)
- Klik sesi → load ulang seluruh history
- Tombol export ke Markdown

---

## 🔌 API ENDPOINTS (Backend)

```
GET    /api/agents              → list semua agent
POST   /api/agents              → buat agent baru
PUT    /api/agents/{id}         → update agent
DELETE /api/agents/{id}         → hapus agent
POST   /api/agents/{id}/test    → test agent dengan pesan singkat

GET    /api/sessions            → list semua sesi
GET    /api/sessions/{id}       → detail sesi + semua pesan
POST   /api/sessions            → buat sesi baru
DELETE /api/sessions/{id}       → hapus sesi

GET    /api/providers           → list provider yang tersedia + model yang didukung

WS     /ws/{session_id}         → WebSocket koneksi utama chat
```

---

## ⚙️ KONFIGURASI & KEAMANAN

### File `.env`
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./agentroom.db
MODERATOR_PROVIDER=anthropic
MODERATOR_MODEL=claude-3-5-haiku-20241022
MODERATOR_API_KEY=your-key-here
MAX_HISTORY_MESSAGES=20        # Berapa pesan terakhir yang dikirim sebagai konteks
MAX_AGENTS_PER_ROUND=5         # Batas agent per putaran
```

### Keamanan API Key
- API key agent disimpan terenkripsi di DB menggunakan `cryptography` library (Fernet)
- Jangan pernah expose API key ke frontend
- Semua call ke AI provider dilakukan dari backend

### Context Window Management
- Batasi history yang dikirim ke tiap agent dengan `MAX_HISTORY_MESSAGES`
- Jika history panjang, gunakan summarization: panggil AI untuk merangkum pesan-pesan lama menjadi satu blok "Summary sebelumnya"

---

## 🚀 INSTRUKSI SETUP & RUN

Buat `README.md` yang berisi:

```markdown
## Setup

### Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env dengan API key kamu
python main.py

### Frontend
cd frontend
npm install
npm run dev

### Buka di browser
http://localhost:5173
```

---

## 📦 DEPENDENCIES

### Backend (`requirements.txt`)
```
fastapi
uvicorn[standard]
websockets
sqlalchemy
aiosqlite
openai
anthropic
google-generativeai
cryptography
python-dotenv
pydantic
httpx
```

### Frontend (`package.json` dependencies)
```json
{
  "react": "^18",
  "react-router-dom": "^6",
  "tailwindcss": "^3",
  "lucide-react": "latest",
  "zustand": "latest"
}
```

---

## ✅ ACCEPTANCE CRITERIA

Aplikasi dinyatakan selesai jika:

1. ✅ User bisa membuat agent baru dengan mengisi form lengkap (nama, role, soul, provider, model, API key)
2. ✅ Minimal 3 provider didukung: OpenAI, Anthropic, Gemini
3. ✅ Saat user kirim pesan di chat room, Moderator menentukan urutan bicara secara otomatis
4. ✅ Agent merespons satu per satu secara berurutan dengan streaming (teks muncul bertahap)
5. ✅ Setiap agent mendapat konteks penuh dari pesan sebelumnya (termasuk respons agent lain)
6. ✅ Ada typing indicator saat agent sedang generate respons
7. ✅ Sesi diskusi tersimpan di SQLite dan bisa di-load ulang
8. ✅ UI responsif dan bisa dijalankan di localhost tanpa koneksi internet (kecuali untuk API call)
9. ✅ API key tidak pernah muncul di frontend atau console log
10. ✅ Ada halaman Agent Manager untuk CRUD agent

---

## 💡 CATATAN UNTUK AI YANG MENGERJAKAN

- Prioritas utama adalah **fungsionalitas real-time chat** — pastikan WebSocket bekerja dengan baik sebelum mengerjakan fitur lain.
- Gunakan `asyncio` di backend untuk handle concurrent API calls jika dibutuhkan.
- Untuk streaming respons AI, gunakan fitur streaming dari masing-masing SDK provider dan pipe token-nya melalui WebSocket ke frontend.
- Jika ada bagian yang ambigu, **pilih solusi yang paling sederhana** dan tambahkan komentar TODO untuk iterasi berikutnya.
- Buat kode yang **mudah dimodifikasi** — pengguna adalah developer yang ingin bisa edit sendiri.
- Tambahkan **komentar penjelasan** di bagian-bagian kritis seperti orchestrator, WebSocket handler, dan context builder.
