from fastapi import APIRouter, HTTPException
from typing import List
from app.models import LocationModel
from app.database import location_collection
from bson import ObjectId

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get("/", response_model=List[LocationModel])
async def get_locations(tenant_id: str):
    return await location_collection.find({"tenant_id": tenant_id}).to_list(100)

@router.post("/", response_model=LocationModel)
async def create_location(location: LocationModel):
    new_loc = await location_collection.insert_one(location.model_dump(by_alias=True, exclude=["id"]))
    return await location_collection.find_one({"_id": new_loc.inserted_id})

@router.delete("/{id}")
async def delete_location(id: str):
    result = await location_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    return {"message": "Ubicación eliminada"}