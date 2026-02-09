from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import db
from app.services.email import send_expiry_alert
from datetime import datetime
import os

scheduler = AsyncIOScheduler()

# Reemplaza tu función check_expired_lots con esta versión Multi-Tenant
async def check_expired_lots():
    print(f"⏰ [Scheduler] Revisando vencimientos...")
    now = datetime.utcnow()
    
    # 1. Buscar TODOS los lotes vencidos
    query = {
        "expiry_date": {"$lt": now},
        "quantity": {"$gt": 0},
        "alert_sent": False
    }
    
    cursor = db.Lotes.find(query)
    all_expired = await cursor.to_list(length=1000)
    
    if not all_expired:
        return

    # 2. Agrupar por Tenant (Empresa)
    # Estructura: { "tenant_123": [lote1, lote2], "tenant_456": [lote3] }
    lots_by_tenant = {}
    for lote in all_expired:
        t_id = lote.get("tenant_id")
        if t_id:
            if t_id not in lots_by_tenant:
                lots_by_tenant[t_id] = []
            lots_by_tenant[t_id].append(lote)

    # 3. Procesar cada empresa por separado
    for tenant_id, lotes in lots_by_tenant.items():
        # A) Buscar configuración de esa empresa
        settings = await db.TenantSettings.find_one({"tenant_id": tenant_id})
        
        destinatarios = []
        if settings and "notification_emails" in settings:
            destinatarios = settings["notification_emails"]
        
        # Fallback: Si no configuraron nada, enviar al admin general del .env (opcional)
        if not destinatarios:
            admin_env = os.getenv("ADMIN_EMAIL_NOTIFY")
            if admin_env: destinatarios = [admin_env]

        if destinatarios:
            print(f"📧 Enviando alerta a {tenant_id}: {destinatarios}")
            try:
                await send_expiry_alert(destinatarios, lotes)
                
                # B) Marcar como enviados SOLO para estos lotes
                ids = [l["_id"] for l in lotes]
                await db.Lotes.update_many(
                    {"_id": {"$in": ids}},
                    {"$set": {"alert_sent": True}}
                )
            except Exception as e:
                print(f"❌ Error enviando a {tenant_id}: {e}")
        else:
            print(f"⚠️ Tenant {tenant_id} tiene lotes vencidos pero NO tiene correos configurados.")

def start_scheduler():
    # Ejecuta cada 24 horas (ajusta 'seconds=60' si quieres probarlo rápido en la demo)
    scheduler.add_job(check_expired_lots, 'interval', seconds=10)
    scheduler.start()