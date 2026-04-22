from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import agents, sessions, uploads
from ws.handler import router as ws_router

app = FastAPI(title="AgentRoom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
