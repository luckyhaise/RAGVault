from app.utils.send_email import send_email

from app.core.security import settings
from app.workers.celery_app import celery_app


@celery_app.task
def send_otp_email(recipient_email:str,otp:int):
  payload = {
        "sender": {
            "name": "Ragvault Security",
            "email": settings.verification_email  
        },
        "to": [
            {
                "email": recipient_email
            }
        ],
        "subject": "Your Ragvault Verification Code",
        "htmlContent": f"""
        <html>
            <body>
                <h2>Verification Code</h2>
                <p>Your secure one-time password (OTP) is: <strong>{otp}</strong></p>
                <p>This code will expire in 5 minutes.</p>
            </body>
        </html>
        """
    }
  send_email(payload=payload)
