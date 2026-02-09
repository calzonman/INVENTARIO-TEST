# app/routes/settings.py
from fastapi import APIRouter, HTTPException, Body
from app.database import db
from app.models import TenantSettingsModel
from typing import List

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/{tenant_id}", response_model=TenantSettingsModel)
async def get_settings(tenant_id: str):
    settings = await db.TenantSettings.find_one({"tenant_id": tenant_id})
    if not settings:
        # Si no existe, devolvemos uno por defecto vacio
        return TenantSettingsModel(tenant_id=tenant_id, notification_emails=[])
    return settings

@router.put("/{tenant_id}")
async def update_settings(tenant_id: str, emails: List[str] = Body(..., embed=True)):
    # Upsert: Actualiza si existe, crea si no
    await db.TenantSettings.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"notification_emails": emails}},
        upsert=True
    )
    return {"message": "Configuración actualizada"}