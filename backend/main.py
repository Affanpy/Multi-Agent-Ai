from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import agents, sessions, uploads
from ws.handler import router as ws_router

import os

app = FastAPI(title="AgentRoom API")

# CORS: Ambil allowed origins dari env, default ke localhost dev ports
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_db()


# Mount routers
app.include_router(agents.router)
app.include_router(sessions.router)
app.include_router(uploads.router)
app.include_router(ws_router)
