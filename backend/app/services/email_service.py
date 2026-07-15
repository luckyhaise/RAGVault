import logging
import resend
from app.core.config import settings
from app.core.exceptions.email_exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)

# set api key for the service
resend.api_key = settings.resend_api_key

async def send_email(recipient_email:str,otp:int,subject:str="Verify your RAGVault email"):
    try:
     resend.Emails.send(
        {
           "from": settings.verification_email,
           "to": [recipient_email],
           "subject" : subject,
           "html" : f"""
             <h2> Email Verification</h2>
             <p> Your RAGVault verification code is : </p>
             <h3>{otp}</h3>
             <p>This Code expires in 10 minutes</p>
             <p>Ignore if you haven't created a account in RAGVault</p> 
         
        

            """
        }
     )
     logger.info("Verification email sent | recipient=%s", recipient_email)
    except Exception as exc:
       logger.error("Failed to send verification email | recipient=%s | error=%s", recipient_email, exc)
       raise EmailDeliveryError(
          internal_message=str(exc)
       )
