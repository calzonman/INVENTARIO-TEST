# app/services/email.py
import os
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv

load_dotenv()

# Configuración obtenida del .env
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

async def send_expiry_alert(destinatario: str, lotes_vencidos: List[dict]):
    """
    Envía un correo con la tabla de lotes vencidos.
    """
    
    # Construcción simple de una tabla HTML
    rows = ""
    for lote in lotes_vencidos:
        rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{lote['product_sku']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{lote['number']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{lote['quantity']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: red;">{lote['expiry_date'].strftime('%Y-%m-%d')}</td>
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
        recipients=[destinatario],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)