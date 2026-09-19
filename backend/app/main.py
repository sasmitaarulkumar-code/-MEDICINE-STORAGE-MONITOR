from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
import app.models  # Ensures all 10 models are registered
from app.routers import auth, storage, telemetry, medicines, alerts, reports, demo
from app.websocket_manager import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if not exist
    Base.metadata.create_all(bind=engine)
    print("[MEDGUARD] SQLite Database initialized & tables verified.")
    yield
    print("[MEDGUARD] Shutting down backend.")

app = FastAPI(
    title="MEDGUARD — Intelligent Medicine Storage Monitor API",
    description="IoT & AI-powered real-time cold chain monitoring, early failure warning, and medicine impact tracking platform.",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(storage.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix=settings.API_V1_STR)
app.include_router(medicines.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)

# Real-time WebSocket Endpoint
@app.websocket("/api/v1/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive receive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Static files and Web Dashboard Mounts
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=FileResponse)
def landing_page():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "system": "MEDGUARD",
        "tagline": "Intelligent Medicine Storage Monitoring & Early Warning System",
        "status": "OPERATIONAL",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/dashboard", response_class=FileResponse)
def operational_dashboard():
    dash_path = os.path.join(static_dir, "dashboard.html")
    if os.path.exists(dash_path):
        return FileResponse(dash_path)
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "medguard-core-api"}

