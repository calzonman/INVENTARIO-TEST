import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from dotenv import load_dotenv  # Importamos dotenv
from app.database import db
from app.models import UserModel

# CARGAR VARIABLES DE ENTORNO
load_dotenv()

# CONFIGURACIÓN SEGURA
# Si no encuentra la variable en el .env, usa un valor por defecto (útil para dev) pero avisa
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Esto asegura que no arranque en producción sin clave
    print("⚠️ ADVERTENCIA: SECRET_KEY no está definida en .env") 
    SECRET_KEY = "insecure_dev_key" 

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

# Contexto de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# DEPENDENCIA: Obtener usuario actual desde el Token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") # El email es el identificador (subject)
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Buscar usuario en BD
    user_data = await db.users.find_one({"email": email})
    if user_data is None:
        raise credentials_exception
        
    return UserModel(**user_data)

# DEPENDENCIA: Solo Admins
async def get_current_admin(current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return current_user