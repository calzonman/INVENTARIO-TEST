from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models import ProductModel
from app.database import product_collection
from bson import ObjectId

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

# 1. Obtener todos los productos (Para la tabla del Dashboard)
@router.get("/", response_model=List[ProductModel])
async def get_products(tenant_id: str):
    products = await product_collection.find({"tenant_id": tenant_id}).to_list(1000)
    return products

# 2. Crear un nuevo producto
@router.post("/", response_model=ProductModel, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductModel):
    # Verificamos si ya existe el código de barras en este tenant
    existing_product = await product_collection.find_one({
        "barcode": product.barcode, 
        "tenant_id": product.tenant_id
    })
    if existing_product:
        raise HTTPException(status_code=400, detail="El código de barras ya existe")

    new_product = await product_collection.insert_one(
        product.model_dump(by_alias=True, exclude=["id"])
    )
    created_product = await product_collection.find_one({"_id": new_product.inserted_id})
    return created_product

# 3. Buscar producto por Código de Barras (Para el Escáner)
@router.get("/scan/{barcode}", response_model=ProductModel)
async def scan_product(barcode: str, tenant_id: str):
    product = await product_collection.find_one({
        "barcode": barcode, 
        "tenant_id": tenant_id
    })
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

# 4. Eliminar producto
@router.delete("/{id}")
async def delete_product(id: str):
    delete_result = await product_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return {"message": "Producto eliminado"}
    raise HTTPException(status_code=404, detail="Producto no encontrado")