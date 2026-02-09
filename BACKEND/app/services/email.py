import os
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# --- CAMBIO AQUÍ: 'destinatarios' ahora es List[str] ---
async def send_expiry_alert(destinatarios: List[str], lotes_vencidos: List[dict]):
    """
    Envía un correo con la tabla de lotes vencidos a MÚLTIPLES destinatarios.
    """
    
    rows = ""
    for lote in lotes_vencidos:
        # Formateo seguro de fecha
        fecha_str = str(lote.get('expiry_date', 'N/A'))
        if hasattr(lote.get('expiry_date'), 'strftime'):
            fecha_str = lote['expiry_date'].strftime('%Y-%m-%d')

        rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{lote.get('product_sku', 'N/A')}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{lote.get('number', 'N/A')}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{lote.get('quantity', 0)}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: red;">{fecha_str}</td>
        </tr>
        """

    html_content = f"""
    <html>
        <body>
            <h2>⚠️ Alerta de Stock Vencido</h2>
            <p>El sistema ha detectado los siguientes lotes vencidos que aún tienen stock:</p>
            <table style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ddd;">SKU</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Lote</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Stock</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Vencimiento</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <p>Por favor, gestione estos lotes lo antes posible.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="[ALERTA] Lotes Vencidos Detectados",
        recipients=destinatarios,  # <--- Pasamos la lista completa aquí
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)