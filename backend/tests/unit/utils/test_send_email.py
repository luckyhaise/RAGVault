from unittest.mock import patch

import pytest

from app.core.config import settings
from app.core.exceptions.email_exceptions import EmailDeliveryError
from app.utils.send_email import send_email


@pytest.mark.asyncio
@patch("app.utils.send_email.resend.Emails.send")
async def test_send_email_calls_resend_with_expected_payload(mock_send):
    recipient = settings.verification_email
    otp = 123456
    subject = "Custom verification subject"

    await send_email(recipient_email=recipient, otp=otp, subject=subject,html=f""" <h1> testing send email {otp}</h1>""")

    mock_send.assert_called_once()
    payload = mock_send.call_args.args[0]
    assert payload["from"] == settings.verification_email
    assert payload["to"] == [recipient]
    assert payload["subject"] == subject
    assert str(otp) in payload["html"]


@pytest.mark.asyncio
@patch("app.utils.send_email.resend.Emails.send")
async def test_send_email_raises_email_delivery_error_on_failure(mock_send):
    mock_send.side_effect = Exception("resend unavailable")

    with pytest.raises(EmailDeliveryError) as excinfo:
        await send_email(recipient_email=settings.verification_email, otp=111111,subject="Custom verification subject", html=""" <h1> testing send email </h1>""")

    assert excinfo.value.error_code == "EMAIL_DELIVERY_ERROR"
    assert excinfo.value.status_code == 503
    assert "resend unavailable" in excinfo.value.internal_message
