
import logging

import requests

from app.core.config import settings
from app.core.exceptions.email_exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)




BREVO_API_KEY = settings.brevo_api_key
BREVO_URL = "https://api.brevo.com/v3/smtp/email"

def send_email(payload:str|dict ) -> bool:
    """Sends a transactional OTP email using the Brevo HTTP API."""
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    
    payload = payload
    
    try:
        response = requests.post(BREVO_URL, json=payload, headers=headers)
        
        if response.status_code in [200, 201, 202]:
            logger.info("Email sent sucessfully")
            return True
        else:
            raise EmailDeliveryError(
                internal_message=f"Failed to send email. Status code: {response.status_code}, Response: {response.text}",
                public_message="Failed to send email, Try again later",
                status_code=response.status_code,
            )
            
    except EmailDeliveryError:
        raise
    except Exception as e:
        raise EmailDeliveryError(
            internal_message=f"An error occurred while calling Brevo API: {e}",
            public_message="Failed to send email, Try again later", 
        ) from e

