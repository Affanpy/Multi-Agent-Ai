import os
import time
import uuid
import logging
from typing import Dict

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 20))

# File cache config
FILE_CACHE_TTL_SECONDS = 600  # 10 menit
FILE_CACHE_MAX_ITEMS = 50


class FileCache:
    """In-memory cache untuk file yang diupload, dengan TTL dan max size."""
    
    def __init__(self, ttl: int = FILE_CACHE_TTL_SECONDS, max_items: int = FILE_CACHE_MAX_ITEMS):
        self._store: Dict[str, dict] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl
        self._max_items = max_items
    
    def generate_file_id(self, filename: str) -> str:
        """Generate unique file ID menggunakan UUID."""
        return f"file-{uuid.uuid4().hex[:12]}-{filename}"
    
    def put(self, file_id: str, file_data: dict):
        """Simpan file ke cache. Jalankan cleanup jika perlu."""
        self._cleanup_expired()
        
        # Jika masih penuh setelah cleanup, hapus yang paling lama
        if len(self._store) >= self._max_items:
            oldest_id = min(self._timestamps, key=self._timestamps.get)
            self._remove(oldest_id)
            logger.warning(f"File cache penuh, menghapus entry terlama: {oldest_id}")
        
        self._store[file_id] = file_data
        self._timestamps[file_id] = time.time()
    
    def pop(self, file_id: str) -> dict | None:
        """Ambil dan hapus file dari cache. Return None jika tidak ada atau expired."""
        if not file_id or file_id not in self._store:
            return None
        
        # Cek apakah expired
        if time.time() - self._timestamps.get(file_id, 0) > self._ttl:
            self._remove(file_id)
            logger.info(f"File cache expired: {file_id}")
            return None
        
        data = self._store.pop(file_id, None)
        self._timestamps.pop(file_id, None)
        return data
    
    def _remove(self, file_id: str):
        self._store.pop(file_id, None)
        self._timestamps.pop(file_id, None)
    
    def _cleanup_expired(self):
        """Hapus semua entry yang sudah expired."""
        now = time.time()
        expired = [fid for fid, ts in self._timestamps.items() if now - ts > self._ttl]
        for fid in expired:
            self._remove(fid)
        if expired:
            logger.info(f"File cache cleanup: {len(expired)} expired entries dihapus")


# Global instance
uploaded_files_cache = FileCache()
