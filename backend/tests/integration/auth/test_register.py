from app.services.user_services import create_account_service , User_Create , match_password , find_user_by_user_name , login_service 
from app.core.exceptions.exceptions import DataBaseError
from account_helper import ensure_user , TEST_ACCOUNTS
import pytest
from sqlalchemy.ext.asyncio import AsyncSession 

def create_user():
    return dict(TEST_ACCOUNTS[0])


@pytest.mark.parametrize("user", TEST_ACCOUNTS)
@pytest.mark.asyncio
async def test_create_account_services(db_session:AsyncSession, user):
    existing = await find_user_by_user_name(session=db_session, user_name=user["user_name"])
    if existing is None:
        account = await create_account_service(session=db_session,user=User_Create(**user))
    else:
        account = existing
    assert account.user_name == user["user_name"]
    assert match_password(password=user["password"],hashed_password=account.password)
    assert account.phone == user["phone"]
    assert account.name == user["name"]
    assert account.email == user["email"]
    user1 = await find_user_by_user_name(session=db_session,user_name=user["user_name"])
    assert user1 is not None
    assert user1.id == account.id

@pytest.mark.asyncio
async def test_create_account_rejects_emails_aready_present(db_session:AsyncSession):
    user = create_user()
    # Adding 9 at the end of everyfield to change them except for email
    for key in user:
        if key != "email":
         user[key] = f"{user[key]}9"
    with pytest.raises(DataBaseError) as excinfo:

       user1 = await create_account_service(session=db_session,user=User_Create(**user))
    assert excinfo.value.error_code == "EMAIL_ALREADY_EXISTS" 
    assert "uq_email" in excinfo.value.internal_message

@pytest.mark.asyncio
async def test_create_account_rejects_phone_already_present(db_session:AsyncSession):
   user = create_user()
   for key in user:
      if key != "phone":
         user[key] = "S"+ str(user[key])
   with pytest.raises(DataBaseError) as excinfo:
      user1 = await create_account_service(session=db_session,user=User_Create(**user))
   assert excinfo.value.error_code == "PHONE_NUMBER_ALREADY_EXISTS"
   assert "uq_phone" in excinfo.value.internal_message
@pytest.mark.asyncio
async def test_create_account_rejects_username_already_present(db_session:AsyncSession):
   user = create_user()
   for key in user:
      if key == "email":
         user[key] = "s" +  str(user[key])
      if key not in  ["user_name", "email"]:
         user[key] = str(user[key])[:-1] + "1" 

   with pytest.raises(DataBaseError) as excinfo:
         user1 = await create_account_service(session=db_session,user=User_Create(**user))
   assert excinfo.value.error_code == "USERNAME_ALREADY_EXISTS"
   assert "uq_user_name" in excinfo.value.internal_message 
