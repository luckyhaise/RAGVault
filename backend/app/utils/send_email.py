import resend
import logging
from app.core.config import settings
from app.core.exceptions.email_exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)
# set api key for the service
resend.api_key = settings.resend_api_key

async def send_email(recipient_email:str,html:str,subject:str,otp:int=None):
    try:
     resend.Emails.send(
        {
           "from": settings.verification_email,
           "to": [recipient_email],
           "subject" : subject,
           "html" : html
        }
     )
     logger.info("Verification email sent | recipient=%s", recipient_email)
    except Exception as exc:
       logger.error("Failed to send verification email | recipient=%s | error=%s", recipient_email, exc)
       raise EmailDeliveryError(
          internal_message=str(exc)
       )

# def send_10_mails_to_myself():
#    for _ in range(2):
#       send_email(recipient_email="dublucky2@gmail.com",subject="big boy lucky",html=""" 

#         <h1>BIG BOY LUCKy </h1>
# """)
# send_10_mails_to_myself()