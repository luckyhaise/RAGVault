from fastapi import APIRouter , Depends , Form  
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions.database_errors import DataError , translate_database_error, SQLAlchemyError
from app.schemas.user_schema import User_Create , UserCreateResponse
from app.services.user_services import create_account_service
user_router = APIRouter(tags=["Users"],prefix="/user")

@user_router.post(path="/create",response_model=UserCreateResponse)
async def create_account(user:User_Create,session:AsyncSession=Depends(get_db)):

        user_account = await create_account_service(session=session,user=user)
        return user_account

      




