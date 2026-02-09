from pydantic import BaseModel, Field, EmailStr, ConfigDict, GetJsonSchemaHandler
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

# --- IMPLEMENTACIÓN DE OBJECTID COMPATIBLE CON PYDANTIC V2 ---
class PyObjectId(str):
    """
    Clase personalizada para manejar ObjectIds de MongoDB en Pydantic v2.
    """
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.str_schema(),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> Any:
        return handler(core_schema.str_schema())

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# --- MODELO DE PRODUCTO ---
class ProductModel(MongoBaseModel):
    sku: str
    barcode: str
    name: str
    description: Optional[str] = None
    category: str
    current_stock: int = 0
    min_stock: int = 5
    unit_price: float
    location: str
    tenant_id: str
    track_batches: bool = Field(default=False)

# --- MODELO DE LOTE ---
class LotModel(MongoBaseModel):
    product_id: str
    product_sku: str
    number: str
    quantity: int
    expiry_date: datetime
    tenant_id: str
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    alert_sent: bool = Field(default=False) # Para notificaciones

# --- MODELO DE MOVIMIENTO ---
class MovementModel(MongoBaseModel):
    product_id: str
    product_name: str
    product_sku: Optional[str] = "UNK"
    type: str  # 'in' | 'out'
    quantity: int
    user_id: str
    user_name: str
    location: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str
    lot_id: Optional[str] = None 
    batch_number: Optional[str] = None 
    expiration_date: Optional[datetime] = None

# --- MODELO DE USUARIO (Actualizado) ---
class UserModel(MongoBaseModel):
    name: str
    email: EmailStr
    role: str = "operator"
    tenant_id: str
    hashed_password: str
    disabled: bool = False
    badge_token: Optional[str] = None  # <--- NUEVO: Token para QR de Kiosco

# --- MODELO PARA CREAR USUARIO ---
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    tenant_id: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_role: str
    user_id: str

class LocationModel(MongoBaseModel):
    code: str
    name: str
    description: Optional[str] = None
    tenant_id: str

# --- MODELO PARA REQUEST DE KIOSCO ---
class KioskRequest(BaseModel):
    badge_token: str    
    product_code: str   

class KioskResponse(BaseModel):
    message: str
    product_name: str
    remaining_stock: int
    lot_used: Optional[str] = None
    # --- NUEVOS CAMPOS ---
    expiry_status: str = "ok" # 'ok', 'soon', 'expired'
    expiry_date: Optional[datetime] = None

# --- Lista para correos electronicos ---
from typing import List

class TenantSettingsModel(MongoBaseModel):
    tenant_id: str
    notification_emails: List[EmailStr] = []  # Lista de correos para alertas
    low_stock_threshold: int = 10             # Podemos guardar esto también aquí