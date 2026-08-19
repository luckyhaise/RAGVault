from app.repositories.users_repository import  find_user_by_user_name
from app.services.user_services import create_account_service , User_Create


TEST_ACCOUNTS = [
    {
        "user_name": "Some_username1",
        "phone": f"+91{'9' * 10}",
        "email": "someemail@mail.com",
        "name": "Some Name",
        "password": "Some_password1",
    },
    {
        "user_name": "alice.walker92",
        "phone": "+14155552671",
        "email": "alice.walker@example.com",
        "name": "Alice Walker",
        "password": "Walk3r@path",
    },
    {
        "user_name": "bob-martin",
        "phone": "+447911123456",
        "email": "bob.martin@mail.org",
        "name": "Bob Martin",
        "password": "Mart1n#code",
    },
  
]

async def ensure_user(db_session,i:int=None):
    index = i if i is not None else 0
    account = TEST_ACCOUNTS[index]
    existing = await find_user_by_user_name(session=db_session, user_name=account["user_name"])
    if existing is None:
        return await create_account_service(session=db_session, user=User_Create(**account))
    return existing
