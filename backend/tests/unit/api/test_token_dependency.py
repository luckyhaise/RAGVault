import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies.validate_token import validate_token_and_get_user_id


@pytest.mark.asyncio
@patch("app.api.dependencies.validate_token.decode_access_token")
async def test_validate_token_returns_user_id(mock_decode):
    mock_decode.return_value = "user_123"

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid_token",
    )

    result = await validate_token_and_get_user_id(credentials)

    assert result == "user_123"
    mock_decode.assert_called_once_with(token="valid_token")


@pytest.mark.asyncio
@patch("app.api.dependencies.validate_token.decode_access_token")
async def test_validate_token_invalid_token(mock_decode):
    mock_decode.side_effect = Exception("Invalid token")

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid_token",
    )

    with pytest.raises(HTTPException) as excinfo:
        await validate_token_and_get_user_id(credentials)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid token"

    mock_decode.assert_called_once_with(token="invalid_token")