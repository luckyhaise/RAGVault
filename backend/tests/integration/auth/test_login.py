import pytest
from app.core.security import decode_access_token 
from app.services.user_services import login_service , User_Login , create_account_service , User_Create , find_user_by_user_name , UnauthorizedError
from conftest import db_session, TEST_ACCOUNTS
from app.models.models import Users
from uuid import UUID
import random
from app.models.models import Users

@pytest.mark.parametrize(
      ("user_name","email","password"),[
         *((account["user_name"], None, account["password"]) for account in TEST_ACCOUNTS),
         *((None, account["email"], account["password"]) for account in TEST_ACCOUNTS),
      ]
)
@pytest.mark.asyncio
async def test_login_service_rejects_user_id_and_email_not_found(user_name,email,password,db_session:db_session):
    with pytest.raises(UnauthorizedError) as excinfo:
          await login_service(session=db_session,user=User_Login(user_name=user_name,password=password,email=email)) 
    assert "Account Not found"  in excinfo.value.internal_message 
    



@pytest.mark.parametrize(
      ("user_name","email","password"),[
         *((account["user_name"], None, account["password"]) for account in TEST_ACCOUNTS),
         *((None, account["email"], account["password"]) for account in TEST_ACCOUNTS),
      ]
)
@pytest.mark.asyncio
async def test_login_service_works_with_username_and_email(db_session:db_session, user_name,email,password):
    account = next(
        a for a in TEST_ACCOUNTS
        if a["user_name"] == user_name or a["email"] == email
    )
    existing = await find_user_by_user_name(session=db_session, user_name=account["user_name"])
    if existing is None:
        
        await create_account_service(session=db_session, user=User_Create(**account))

    login_token = await login_service(session=db_session,user=User_Login(user_name=user_name,email=email,password=password))
    assert login_token
    id = decode_access_token(login_token)
    user = await db_session.get(Users, UUID(id))
    assert user is not None
    if user_name is not None:
        assert user.user_name == user_name
    if email is not None:
        assert user.email == email



@pytest.mark.parametrize(
      ("user_name","password"),[
         *((account["user_name"], str(account["password"]) + "1" ) for account in TEST_ACCOUNTS),

      ]
)
@pytest.mark.asyncio
async def test_login_service_rejects_wrong_passwords(db_session:db_session,user_name,password):

     
          
     with pytest.raises(UnauthorizedError) as excinfo:
          await login_service(session=db_session,user=User_Login(user_name=user_name,password=password)) 
     assert excinfo.value.internal_message  == f"Incorrect password input user_name: {user_name} , password: {password}"
     