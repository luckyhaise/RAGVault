import pytest
from app.schemas.user_schema import User_Login, User_Create, UserCreateResponse
from pydantic_core import ValidationError
from pydantic import ValidationError
from uuid import UUID, uuid4


VALID_PASSWORD = "Some_password1"


def test_user_login_accepts_username_only():
    data = {
        "user_name": "avinash_panda",
        "email": None,
        "password": VALID_PASSWORD,
    }

    validated = User_Login(**data)

    assert validated.user_name == "avinash_panda"
    assert validated.email is None
    assert validated.password == VALID_PASSWORD


def test_user_login_accepts_email_only():
    data = {
        "user_name": None,
        "email": "abcd234@gmail.com",
        "password": VALID_PASSWORD,
    }

    validated = User_Login(**data)

    assert validated.user_name is None
    assert str(validated.email) == "abcd234@gmail.com"
    assert validated.password == VALID_PASSWORD


def test_user_login_rejects_missing_username_and_email():
    data = {
        "user_name": None,
        "email": None,
        "password": VALID_PASSWORD,
    }

    with pytest.raises(ValidationError) as exc_info:
        User_Login(**data)

    errors = exc_info.value.errors()

    assert len(errors) == 1
    assert errors[0]["loc"] == ()
    assert errors[0]["msg"] == (
        "Value error, Provide either email or username"
    )


def test_user_login_rejects_username_and_email_together():
    data = {
        "user_name": "avinash_panda",
        "email": "abcd234@gmail.com",
        "password": VALID_PASSWORD,
    }

    with pytest.raises(ValidationError) as exc_info:
        User_Login(**data)

    errors = exc_info.value.errors()

    assert len(errors) == 1
    assert errors[0]["loc"] == ()
    assert errors[0]["msg"] == (
        "Value error, Provide only username or email"
    )


def test_user_login_rejects_invalid_email():
    data = {
        "user_name": None,
        "email": "abcdgmail.com",
        "password": VALID_PASSWORD,
    }

    with pytest.raises(ValidationError) as exc_info:
        User_Login(**data)

    errors = exc_info.value.errors()

    assert errors[0]["loc"] == ("email",)


@pytest.mark.parametrize(
    "password",
    [
        "",
        "a" * 129,
    ],
)
def test_user_login_rejects_invalid_password_length(password):
    data = {
        "user_name": "avinash_panda",
        "email": None,
        "password": password,
    }

    with pytest.raises(ValidationError) as exc_info:
        User_Login(**data)

    errors = exc_info.value.errors()

    assert errors[0]["loc"] == ("password",)


def test_user_login_rejects_invalid_username():
    data = {
        "user_name": "avinash panda!",
        "email": None,
        "password": VALID_PASSWORD,
    }

    with pytest.raises(ValidationError) as exc_info:
        User_Login(**data)

    errors = exc_info.value.errors()

    assert errors[0]["loc"] == ("user_name",)

def create_data_for_account_creation(fields:list=None):
    data =  {
        "user_name":"Avinash_panda",
        "password": "Abcddf_dc932@$",
        "email"   : "avinishpanda124@gmail.com",
        "phone" : "+919876543210",
        "name" : "avinish panda"
    
    }
    if fields:
       return {k:data[k] for k in fields}
    return data


def check_user_create_accepts_valid_data():
    data = create_data_for_account_creation()
    validated = User_Create(**data)
    assert validated.email == data["email"]
    assert validated.name == data["name"]
    assert validated.password == data["password"]
    assert validated.phone == data["phone"]
    assert validated.user_name == data["user_name"]

def check_user_create_rejects_invalid_user_name():
    data = create_data_for_account_creation()
    data["user_name"] = "avinashpanda`"
    with pytest.raises(ValidationError) as excinfo: 

        User_Create(**data)

    assert (excinfo.value.errors()[0]["loc"]) == ('user_name',)

@pytest.mark.parametrize(

   "invalid_phone",[
       "919987654321",
       "+11928",
       "+11298734897433345",
       "adljfasdfeasdf",
       "",
    

   ])
def test_user_create_rejects_invalid_phone_number(invalid_phone):
    data  = create_data_for_account_creation()
    data["phone"] = invalid_phone
    with pytest.raises(ValidationError) as excinfo :
        User_Create(**data)
    assert excinfo.value.errors()[0].get("loc") == ("phone",)

@pytest.mark.parametrize(
    "invalid_email",[
        "avinishpanda",
        "9087shdf3",
        "dsfsdf@mail",

    ]

)
def test_user_create_rejects_invalid_email(invalid_email):
    data = create_data_for_account_creation()
    data["email"] = invalid_email
    with pytest.raises(ValidationError) as excinfo:
        User_Create(**data)
    assert excinfo.value.errors()[0].get("loc") == ("email",)

@pytest.mark.parametrize(
    "fields",[
        "phone",
        "email",
        "password",
        "user_name",
        "name",
    ]
)
def test_create_user_rejects_missing_fields(fields):
    data = create_data_for_account_creation()
    data[fields] = None
    with pytest.raises(ValidationError):
        User_Create(**data)
@pytest.mark.parametrize(
        "invaild_password",[
            "Some_password9`",
            "some_password9",
            "SOME_PASSWORD9",
            "Some_password",
            "SomePassword9"
            ""
        ]
)
def test_create_user_rejects_invaild_password(invaild_password):
    data = create_data_for_account_creation()
    data["password"]  = invaild_password
    with pytest.raises(ValidationError) as excinfo:
        User_Create(**data)
    assert excinfo.value.errors()[0].get("loc") == ("password",)


def test_user_create_response_accepts_valid_data():
    data = {
        "email": "user@example.com",
        "id": uuid4(),
        "name": "Test User",
    }

    validated = UserCreateResponse(**data)

    assert validated.email == data["email"]
    assert validated.id == data["id"]
    assert validated.name == data["name"]


def test_user_create_response_accepts_data_from_attributes():
    class UserCreateResponseAttributes:
        pass

    attrs = UserCreateResponseAttributes()
    attrs.email = "user@example.com"
    attrs.id = uuid4()
    attrs.name = "Attribute User"

    validated = UserCreateResponse.model_validate(attrs)

    assert validated.email == attrs.email
    assert validated.id == attrs.id
    assert validated.name == attrs.name
