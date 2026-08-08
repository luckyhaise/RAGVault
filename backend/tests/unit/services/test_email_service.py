import pytest
from unittest.mock import patch

from app.core.config import settings
from app.core.exceptions.email_exceptions import EmailDeliveryError
from app.services.email_service import send_email