from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from app.models import MovementModel, KioskResponse, KioskRequest
from app.database import movement_collection, product_collection, lot_collection, db
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/movements", tags=["movements"])

# CONFIGURACIÓN
WARNING_DAYS = 30  # Días para considerar "Próximo a vencer"

# --- RUTAS ESTÁNDAR (Login Requerido) ---

@router.get("/", response_model=List[MovementModel])
async def get_movements(tenant_id: str):
    movements = await movement_collection.find({"tenant_id": tenant_id}).sort("timestamp", -1).to_list(1000)
    return movements

@router.post("/", response_model=MovementModel, status_code=status.HTTP_201_CREATED)
async def create_movement(movement: MovementModel):
    # 1. Validar Producto
    product = await product_collection.find_one({"_id": ObjectId(movement.product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if movement.product_sku == "UNK" or not movement.product_sku:
        movement.product_sku = product.get("sku", "UNK")
    if not movement.location:
        movement.location = product.get("location", "General")

    # 2. Lógica de Lotes (Entradas/Salidas Manuales)
    if movement.lot_id:
        lot = await lot_collection.find_one({"_id": ObjectId(movement.lot_id)})
        if not lot:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        
        movement.batch_number = lot["number"]
        movement.expiration_date = lot["expiry_date"]

        lot_change = movement.quantity if movement.type == 'in' else -movement.quantity
        
        if movement.type == 'out' and lot["quantity"] < movement.quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente en el Lote {lot['number']}")

        await lot_collection.update_one(
            {"_id": ObjectId(movement.lot_id)},
            {"$inc": {"quantity": lot_change}}
        )

    # 3. Actualizar Stock Global
    stock_change = movement.quantity if movement.type == 'in' else -movement.quantity
    
    if movement.type == "out" and product["current_stock"] < movement.quantity:
         raise HTTPException(status_code=400, detail="Stock total insuficiente")

    await product_collection.update_one(
        {"_id": ObjectId(movement.product_id)},
        {"$inc": {"current_stock": stock_change}}
    )

    # 4. Guardar Movimiento
    movement_dict = movement.model_dump(by_alias=True, exclude=["id"])
    if "_id" in movement_dict and movement_dict["_id"] is None:
        del movement_dict["_id"]
        
    result = await movement_collection.insert_one(movement_dict)
    created_movement = await movement_collection.find_one({"_id": result.inserted_id})
    return created_movement


# --- ENDPOINT ESPECIAL: SALIDA RÁPIDA (KIOSCO - VERSIÓN DEBUG) ---
@router.post("/kiosk-checkout", response_model=KioskResponse)
async def kiosk_checkout(req: KioskRequest):
    print(f"\n--- 🔍 INICIO DEBUG KIOSCO ---")
    print(f"1. Token recibido: '{req.badge_token}'")
    print(f"2. Raw Product Code: '{req.product_code}'")

    # 1. VALIDAR USUARIO
    user_data = await db.users.find_one({"badge_token": req.badge_token})
    
    if not user_data:
        print("❌ Error: Usuario no encontrado por token.")
        raise HTTPException(status_code=401, detail="Credencial de usuario inválida")
    
    tenant_id = user_data.get("tenant_id")
    user_id = str(user_data["_id"])
    # --- CORRECCIÓN AQUÍ: Definimos user_name ---
    user_name = user_data.get("name", "Usuario Kiosco") 
    
    print(f"3. Usuario: {user_name} | Tenant ID del Usuario: '{tenant_id}'")

    # 2. INTERPRETAR CÓDIGO
    raw_code = req.product_code.strip()
    search_code = raw_code
    forced_lot_number = None

    if '/' in raw_code:
        parts = raw_code.split('/')
        search_code = parts[0].strip()
        if len(parts) >= 2:
            forced_lot_number = parts[1].strip()
            
    print(f"4. Código a buscar (Barcode): '{search_code}'")
    if forced_lot_number:
        print(f"   Lote forzado detectado: '{forced_lot_number}'")

    # 3. BUSCAR PRODUCTO (Por Barcode estrictamente)
    query = {
        "barcode": search_code,
        "tenant_id": tenant_id
    }
    print(f"5. Ejecutando Query MongoDB: {query}")

    product = await product_collection.find_one(query)
    
    if not product:
        # Diagnóstico secundario
        exists_anywhere = await product_collection.find_one({"barcode": search_code})
        if exists_anywhere:
            print(f"❌ EL PRODUCTO EXISTE pero en otro tenant: '{exists_anywhere.get('tenant_id')}'")
            raise HTTPException(status_code=404, detail=f"Producto existe en tenant '{exists_anywhere.get('tenant_id')}', pero tú eres '{tenant_id}'")
        else:
            print(f"❌ EL PRODUCTO NO EXISTE en ninguna parte.")
            raise HTTPException(status_code=404, detail=f"Producto no encontrado (Barcode: '{search_code}')")

    print(f"✅ Producto encontrado: {product.get('name')} (ID: {product.get('_id')})")
    
    product_id = str(product["_id"])
    real_sku = product.get("sku", "UNK")
    track_batches = product.get("track_batches", False)
    
    selected_lot = None
    lot_id_str = None
    expiry_status = "ok"
    lot_expiry_date = None

    # 4. LÓGICA DE SELECCIÓN DE LOTE
    if track_batches:
        if forced_lot_number:
            print(f"6. Buscando Lote Específico: '{forced_lot_number}'")
            selected_lot = await lot_collection.find_one({
                "product_id": product_id,
                "number": forced_lot_number,
                "tenant_id": tenant_id
            })
            if not selected_lot:
                 print(f"❌ Lote no encontrado.")
                 raise HTTPException(status_code=404, detail=f"Lote '{forced_lot_number}' no encontrado")
        else:
            print(f"6. Buscando Lote por FEFO...")
            lots_cursor = lot_collection.find({
                "product_id": product_id,
                "quantity": {"$gt": 0},
                "status": "active",
                "tenant_id": tenant_id
            }).sort("expiry_date", 1).limit(1)
            
            lots = await lots_cursor.to_list(length=1)
            if not lots:
                print(f"❌ No hay lotes con stock.")
                raise HTTPException(status_code=400, detail="No hay lotes con stock disponible")
            selected_lot = lots[0]

        if selected_lot:
            print(f"✅ Lote seleccionado: {selected_lot.get('number')} | Vence: {selected_lot.get('expiry_date')}")
            lot_id_str = str(selected_lot["_id"])
            lot_expiry_date = selected_lot["expiry_date"]
            
            now = datetime.utcnow()
            if lot_expiry_date < now:
                expiry_status = "expired"
                print("⚠️ ESTADO: EXPIRED")
            elif lot_expiry_date < (now + timedelta(days=WARNING_DAYS)):
                expiry_status = "soon"
                print("⚠️ ESTADO: SOON")

    # 5. VALIDAR STOCK
    if product.get("current_stock", 0) < 1:
        raise HTTPException(status_code=400, detail="Sin stock global disponible")

    # 6. UPDATE
    batch_info = None
    if selected_lot:
        await lot_collection.update_one(
            {"_id": selected_lot["_id"]},
            {"$inc": {"quantity": -1}}
        )
        batch_info = selected_lot["number"]
    
    await product_collection.update_one(
        {"_id": product["_id"]},
        {"$inc": {"current_stock": -1}}
    )

    # 7. GUARDAR MOVIMIENTO
    new_movement = MovementModel(
        product_id=product_id,
        product_name=product["name"],
        product_sku=real_sku,
        type="out",
        quantity=1,
        user_id=user_id,
        user_name=user_name,
        location=product.get("location", "Kiosco"),
        tenant_id=tenant_id,
        lot_id=lot_id_str,
        batch_number=batch_info,
        expiration_date=lot_expiry_date
    )
    
    movement_dict = new_movement.model_dump(by_alias=True, exclude=["id"])
    if "_id" in movement_dict and movement_dict["_id"] is None: del movement_dict["_id"]
    
    await movement_collection.insert_one(movement_dict)

    print(f"✅ Retiro Exitoso. Fin del Debug.\n")
    return {
        "message": "Retiro exitoso",
        "product_name": product["name"],
        "remaining_stock": product["current_stock"] - 1,
        "lot_used": batch_info,
        "expiry_status": expiry_status,
        "expiry_date": lot_expiry_date
    }