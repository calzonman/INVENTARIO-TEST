from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from app.database import db
from app.models import UserModel, UserCreate, UserLogin, Token
from app.security import get_password_hash, verify_password, create_access_token, get_current_user, get_current_admin, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import uuid # <--- Importar UUID

router = APIRouter(prefix="/users", tags=["Users"])

# 1. REGISTRAR USUARIO (Crea cuenta + Hash Password + BADGE TOKEN)
@router.post("/register", response_model=UserModel)
async def register_user(user: UserCreate):
    # Verificar si ya existe
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Encriptar contraseña
    hashed_pw = get_password_hash(user.password)
    
    # Generar Token Único para Kiosco (QR)
    new_badge_token = str(uuid.uuid4())
    
    # Crear diccionario base
    new_user_dict = user.model_dump()
    del new_user_dict['password']
    new_user_dict['hashed_password'] = hashed_pw
    new_user_dict['badge_token'] = new_badge_token # <--- Guardamos el token
    
    # Instanciamos el modelo
    new_user = UserModel(**new_user_dict)
    
    # Limpieza de _id para Mongo
    user_to_insert = new_user.model_dump(by_alias=True, exclude=["id"])
    if "_id" in user_to_insert and user_to_insert["_id"] is None:
        del user_to_insert["_id"]

    result = await db.users.insert_one(user_to_insert)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return created_user

# 2. LOGIN (Genera JWT)
@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    user_data = await db.users.find_one({"email": form_data.email})
    if not user_data:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    user = UserModel(**user_data)
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "tenant": user.tenant_id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_name": user.name,
        "user_role": user.role,
        "user_id": str(user.id)
    }

@router.get("/me", response_model=UserModel)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[UserModel])
async def get_users(tenant_id: str, current_user: UserModel = Depends(get_current_admin)):
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="No puedes ver usuarios de otra organización")
    users = await db.users.find({"tenant_id": tenant_id}).to_list(100)
    return users