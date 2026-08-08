import pytest
from app.core.security import match_password,hash_password, create_access_token , decode_access_token
from uuid import uuid4
from datetime import datetime , timedelta , UTC
from freezegun import freeze_time
from hypothesis import given , strategies as st
def test_password_hashing_and_matching():
    password = "praindtkfhsodnftasdf838932"
    hashed_password = hash_password(password=password)
    assert match_password(password=password,hashed_password=hashed_password)
    # wrong password must fail
    assert not match_password(password="sklhlhdfsdflfd",hashed_password=hashed_password)
    # Salt uniqueness test
    another_hash = hash_password(password)
    assert not hashed_password == another_hash
    



@pytest.mark.parametrize("edge_case_password", [
    "",              
    " ",             
    "a" * 100,       
    "🔒🔑💥",        
])
def test_password_edge_cases(edge_case_password):
    hashed = hash_password(password=edge_case_password)
    assert match_password(password=edge_case_password, hashed_password=hashed) is True


def test_create_and_decode_access_token():
    user_id = str(uuid4())
    token = create_access_token(user_id)
    assert decode_access_token(token=token) == user_id

def test_token_expires_after_limit():
    user_id = str(uuid4())
    token =create_access_token(user_id)
    with freeze_time(datetime.now(UTC)+timedelta(minutes=35)):
         with pytest.raises(Exception) as exinfo:
             decode_access_token(token)
         assert str(exinfo.value) == "Signature has expired."
test_token_expires_after_limit()

def test_token_salt_uniqueness():
    user_id = str(uuid4())
    token = create_access_token(user_id)
    second_token = create_access_token(user_id)
    assert  token != second_token

@given(st.integers(min_value=1,max_value=9999999999)|st.characters())
def token_edge_cases(n):
    id = str(n)
    token = create_access_token(id)
    assert decode_access_token(token) == id
token_edge_cases()