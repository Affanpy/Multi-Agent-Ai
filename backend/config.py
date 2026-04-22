import os
from typing import Dict

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 20))

# In-memory cache untuk file yang diupload (per session)
uploaded_files_cache: Dict[str, dict] = {}
