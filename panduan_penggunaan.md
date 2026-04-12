# Panduan Penggunaan Sistem Multi-Agen "AgentRoom" 🤖

Selamat datang di **AgentRoom**, platform aplikasi web asinkron canggih untuk mengorkestrasi percakapan dan debat antar banyak Agen AI (Kecerdasan Buatan). Melalui sistem ini, Anda dapat memerankan sebuah tim pakar maya secara *real-time*!

---

## 1. Persiapan Awal

Pastikan beberapa prasyarat utama sudah ter-instal ke dalam perangkat komputer Anda:
- **Python (3.9 atau lebih)**: Untuk menjalankan logika server Backend.
- **Node.js (18+ via `npm`)**: Untuk mem-build dan menjalankan antarmuka grafis UI VITE + React.
- **API Keys**: Setidaknya satu kunci API dari salah satu penyedia AI (`OpenAI`, `Anthropic`, atau `Gemini`).

---

## 2. Cara Menjalankan Backend (Server Utama)

Jantung dari operasi komunikasi *WebSocket* dan pengolahan Database ada pada mesin Backend (FastAPI).

1. Buka sebuah terminal/konsol baru.
2. Masuk ke direktori backend:
   ```bash
   cd backend
   ```
3. Salin file contoh `.env` menjadi konfigurasi rahasia Anda:
   ```bash
   cp .env.example .env
   ```
4. Buka file `.env` kemudian amankan kunci dengan mengisi variabel `SECRET_KEY`. Anda bebas mengisi nilainya, tapi wajib berformat string kriptografi standar 32-Byte (atau gunakan tool script generator bawaan dari Python/Fernet). Masukkan juga API Anda untuk bertindak sebagai **Moderator** AI.
5. Setup *Virtual Environment* untuk melimitasi dependensi (Agar rapi):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
6. Unduh seluruh pustaka Python:
   ```bash
   pip install -r requirements.txt
   ```
7. Nyalakan mesin server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   > Status terminal yang ini jangan Anda matikan. Biarkan server port 8000 menyala di *background*.

---

## 3. Cara Menjalankan Frontend (Antarmuka UI)

Selanjutnya kita akan menyalakan tampilan grafisnya.

1. Buka jendela terminal yang **baru/terpisah**.
2. Masuk ke folder frontend:
   ```bash
   cd frontend
   ```
3. Unduh secara penuh pustaka berbasis Node.js untuk React:
   ```bash
   npm install
   ```
4. Jalankan *Vite Dev Server*:
   ```bash
   npm run dev
   ```
5. Konsol akan memberikan tautan lokal, biasanya berada di: [http://localhost:5173](http://localhost:5173) (Buka tautan ini pada *Web Browser* seperti Chrome/Safari Anda!).

---

## 4. Alur Pelaksanaan Simulasi Brainstorming (Cara Pakai)

Setelah Anda membuka aplikasi via *Browser*, Anda berada di laman dasbor interaktif dengan tema malam yang estetik (Dark, Glassmorphism).

Ikuti urutan pemakaian agar mendapatkan alur aplikasi yang benar:

### A. Daftarkan Para Agen Ahli (`/agents`)
Langkah pertama tentu menyiapkan narasumber rapatnya!
1. Masuk ke menu naviasi atas: **Agents** (Agent Manager)
2. Klik tombol utama **Add Agent**.
3. Buatlah Setelan Kepribadian Agen Anda:
   - **Nama & Peran**: Misalnya (John, Psikolog) lalu tambahkan emoji khas 🧠.
   - **Model & Penyedia**: Pilih Provider (OpenAI/Anthropic/Gemini) yang disukai. Isi nama spesifik model (cth: `gpt-4o` atau `claude-3-5-sonnet-20241022`).
   - **Konfigurasi Pribadi**: Isikan API Key-nya. Ingat, *Secret Key* ini otomatis aman tersandi di dalam `SQLite` lokal secara *end-to-end*.
   - **System Prompt**: Isi pengarahan atau perintah khusus bagaimana AI tersebut sebaiknya bicara (Misal: "Bicaralah seperti seorang psikolog yang puitis dan pesimis...").
4. Buatlah **2 hingga lebih** banyak agen untuk melangsungkan debat seru di langkah yang berikutnya.

### B. Mulai Percakapan Sesi Baru (`/`)
1. Pilih tab pertama, laman **Brainstorm**.
2. Secara otomatis, sistem akan mulai memuat Sesi Baru (*New Session*).
3. Cek notifikasi WebSocket berwarna *Emerald/hijau* di bawah judul, pastikan bertuliskan `connected` (Server API merespons dengan benar).
4. Sapa grup AI Anda lewat kotak obrolan di bagian kolom bawah, (Misalkan: *"Mari evaluasi kondisi perekonomian pasca kemunculan AGI"*), lalu kirim panah biru.
5. **Magic Begins**: Secara cerdas, si AI Moderator di balik layar akan mengevaluasi pernyataan Anda, lalu menyusun antrean (Siapa agen yang paling pantas merepons duluan dengan topik Anda!).
6. Setelah itu Anda akan melihat Animasi _Generating_ / Mengetik interaktif antar balasan AI. Teks ini murni muncul seketika secara serentak (_Streamed_). 🚀

### C. Melanjutkan Diskusi Lewat (`/sessions`)
1. Bila di lain waktu Anda ingin meninjau memori atau resume kesimpulan debat para AI kemarin, singgung masuk ke halaman **History**.
2. Daftar percakapan (*sessions*) yang dikelola melalui asynchronus SQLite tertayang otomatis di sana.
3. Cukup menekan **Resume >** pada *card* terkait, dan Anda akan langsung dibawa kembali ke meja ruang tamu `WebSockets Chat` lengkap bersama semua konteks sejarah (memory string) sebelumnya.

---

> **Peringatan Teknis Penting**: Jika sewaktu-waktu aplikasi menampilkan peringatan *"Server Error / Disconnected"*, hal pertama yang perlu diperiksa adalah pastikan dua sisi Terminal lokal Anda (Vite Frontend & Uvicorn FastAPI) masih dalam kondisi bernyala aktif. Jendela konsol akan memberikan info mendetail jika _API Key_ AI Anda kehabisan batasan/kuota (limits limit).

Selamat menikmati pengalaman mengelola ruang diskursus pintar secara otonom!
