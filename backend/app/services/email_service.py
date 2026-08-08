from app.utils.send_email import send_email
import asyncio 
from app.core.security import settings

async def send_otp_email(recipient_email:str,otp:int):
   await send_email(recipient_email=recipient_email,otp=otp,html=f"""
             <h2> Email Verification</h2>
             <p> Your RAGVault verification code is : </p>
             <h3>{otp}</h3>
             <p>This Code expires in 10 minutes</p>
             <p>Ignore if you haven't created a account in RAGVault</p> 
         
        

            """,subject="Ragvault ")
