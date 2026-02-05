# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# IMPORTAR SERVICIO SCHEDULER
from app.services.scheduler import start_scheduler

# IMPORTAR RUTAS
from app.routes import products, movements, users, locations, lots

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    print("🚀 Scheduler iniciado.")
    yield
    print("🛑 Apagando sistema...")

app = FastAPI(
    title="Sistema de Inventario SaaS",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORRECCIÓN CRÍTICA DE CORS ---
# Usamos regex para permitir localhost y cualquier subdominio de Vercel/Railway
# Esto soluciona el error de "bloqueo por credenciales"
origin_regex = r"^(http://localhost:\d+|https://.*\.vercel\.app|https://.*\.railway\.app)$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origin_regex, # <--- ESTA ES LA CLAVE
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

@app.get("/")
async def root():
    return {"message": "API Operativa"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)