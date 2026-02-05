from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models import LotModel
from app.database import lot_collection, product_collection # Asegúrate de exportar lot_collection en database.py
from bson import ObjectId

router = APIRouter(
    prefix="/lots",
    tags=["lots"]
)

@router.get("/", response_model=List[LotModel])
async def get_lots(tenant_id: str, product_id: str = None):
    query = {"tenant_id": tenant_id, "quantity": {"$gt": 0}} # Solo lotes con stock
    if product_id:
        query["product_id"] = product_id
    
    lots = await lot_collection.find(query).sort("expiry_date", 1).to_list(1000)
    return lots

@router.post("/", response_model=LotModel, status_code=status.HTTP_201_CREATED)
async def create_lot(lot: LotModel):
    # Verificar que producto existe
    product = await product_collection.find_one({"_id": ObjectId(lot.product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    lot_dict = lot.model_dump(by_alias=True, exclude=["id"])
    new_lot = await lot_collection.insert_one(lot_dict)
    created_lot = await lot_collection.find_one({"_id": new_lot.inserted_id})
    return created_lot