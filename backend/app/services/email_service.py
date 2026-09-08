import logging

from app.core.exceptions.exceptions import ExternalServiceError
from app.core.security import settings
from app.utils.send_email import send_email
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def send_otp_email(self,recipient_email:str,otp:int):
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
  try:
    logger.info(f"send email request recieved for id:{self.request.id}")
    send_email(payload=payload)
    logger.info(f"send email request successful for id:{self.request.id}")
  except Exception as exc:
      raise ExternalServiceError(internal_message=str(exc),public_message="Unable to send otp due to  external service error. Please  try again later") from exc
      