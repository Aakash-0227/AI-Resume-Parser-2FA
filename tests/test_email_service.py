
from unittest.mock import MagicMock

import pytest

from app.services.email_service import send_email_otp


def test_email_service(monkeypatch):
    captured = {}

    mock_server = MagicMock()

    def fake_smtp(host, port, timeout):
        captured["host"] = host
        captured["port"] = port
        captured["timeout"] = timeout
        return mock_server

    monkeypatch.setattr(
        "app.services.email_service.smtplib.SMTP",
        fake_smtp
    )

    monkeypatch.setattr(
        "app.services.email_service.os.getenv",
        lambda key, default=None: {
            "SMTP_EMAIL": "test@example.com",
            "SMTP_APP_PASSWORD": "test-password"
        }.get(key, default)
    )

    result = send_email_otp(
        recipient_email="recipient@example.com",
        otp="482619"
    )

    assert result is True
    assert captured["host"] == "smtp.gmail.com"
    assert captured["port"] == 587

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with(
        "test@example.com",
        "test-password"
    )
    mock_server.send_message.assert_called_once()
    mock_server.quit.assert_called_once()

    print("\nEmail service test passed!")
