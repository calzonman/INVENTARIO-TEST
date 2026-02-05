import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.environ.get("MONGODB_URL")
DB_NAME = os.environ.get("DB_NAME")

if not MONGODB_URL:
    raise ValueError("No se ha definido la variable MONGODB_URL en el archivo .env")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]

# Colecciones (Mapeo directo a tu BD)
product_collection = db.get_collection("Productos")
lot_collection = db.get_collection("Lotes")       # Requerido por el PRD para trazabilidad [cite: 35]
movement_collection = db.get_collection("Movimientos") # Para auditoría [cite: 40]
user_collection = db.get_collection("Usuarios")
location_collection = db.get_collection("Ubicaciones")