# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# IMPORTAR SERVICIO SCHEDULER
from app.services.scheduler import start_scheduler

# IMPORTAR RUTAS
from app.routes import products, movements, users, locations, lots, settings

# --- LIFESPAN (NUEVO) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica al iniciar
    start_scheduler()
    print("🚀 Scheduler de notificaciones iniciado.")
    yield
    # Lógica al apagar (si fuera necesaria)
    print("🛑 Apagando sistema...")

app = FastAPI(
    title="Sistema de Inventario SaaS",
    description="Backend para gestión de trazabilidad y lotes",
    version="1.0.0",
    lifespan=lifespan # <--- CONECTAR AQUÍ
)

# Configuración de CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://inventario-test.vercel.app",
    "https://inventario-test.vercel.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTRAR ROUTERS
app.include_router(products.router)
app.include_router(movements.router)
app.include_router(users.router)      
app.include_router(locations.router)
app.include_router(lots.router)
app.include_router(settings.router) 

@app.get("/")
async def root():
    return {"message": "API de Inventario Operativa 🚀"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)