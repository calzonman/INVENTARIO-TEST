# app/services/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import db # Asegúrate que esto importe tu objeto database de motor
from app.services.email import send_expiry_alert
from datetime import datetime

scheduler = AsyncIOScheduler()

async def check_expired_lots():
    """
    Tarea programada: Busca lotes vencidos no notificados y envía alerta.
    """
    print(f"⏰ [Scheduler] Ejecutando revisión de vencimientos: {datetime.now()}")
    
    now = datetime.utcnow()
    
    # 1. Buscar lotes: Vencidos + Con Stock + No notificados
    query = {
        "expiry_date": {"$lt": now},
        "quantity": {"$gt": 0},
        "alert_sent": False # Solo los que no hemos avisado
    }
    
    expired_lots_cursor = db.Lotes.find(query)
    expired_lots = await expired_lots_cursor.to_list(length=100)
    
    if not expired_lots:
        print("✅ [Scheduler] No hay nuevos lotes vencidos.")
        return

    print(f"⚠️ [Scheduler] Se encontraron {len(expired_lots)} lotes vencidos.")

    # 2. Enviar Email (Para MVP enviamos a un admin fijo o variable de entorno)
    # En producción, aquí buscarías el email del admin del tenant correspondiente.
    import os
    admin_email = os.getenv("ADMIN_EMAIL_NOTIFY", "tu_email_real@gmail.com")
    
    try:
        await send_expiry_alert(admin_email, expired_lots)
        print("📧 [Scheduler] Correo enviado exitosamente.")
        
        # 3. Marcar lotes como notificados para no repetir el correo mañana
        lot_ids = [lote["_id"] for lote in expired_lots]
        await db.lots.update_many(
            {"_id": {"$in": lot_ids}},
            {"$set": {"alert_sent": True}}
        )
        print("📝 [Scheduler] Lotes actualizados (flag alert_sent=True).")
        
    except Exception as e:
        print(f"❌ [Scheduler] Error enviando alerta: {e}")

def start_scheduler():
    # Ejecuta la tarea todos los días a las 8:00 AM (o cada minuto para probar si pones 'minutes=1')
    #scheduler.add_job(check_expired_lots, 'cron', hour=8, minute=0)
    # Para pruebas rápidas, descomenta la siguiente línea (ejecuta cada 30 segs):
    scheduler.add_job(check_expired_lots, 'interval', seconds=300)
    
    scheduler.start()