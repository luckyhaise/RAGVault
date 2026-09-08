from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import EmailVerificationOtp


async def save_otp(session:AsyncSession,otp_hash:str,expires_at:datetime,email:str):
    otp = EmailVerificationOtp(expires_at = expires_at,otp_hash = otp_hash,email = email) 
    session.add(otp)
    await session.flush()
    return otp
async def get_saved_otp(session:AsyncSession,otp_id:UUID):
    stmt = select(EmailVerificationOtp).where(EmailVerificationOtp.id == otp_id)
    excuted = await session.execute(stmt)
    result = excuted.scalar_one_or_none()
    return result
async def delete_otp(session:AsyncSession,otp_id:UUID):
    stmt = delete(EmailVerificationOtp).where(EmailVerificationOtp.id == otp_id)
    result = await session.execute(stmt)
    
