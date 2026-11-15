
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app.services.otp_service as otp_service
from app.main import app


# --------------------------------------------------
# SHARED TEST CLIENT
# --------------------------------------------------

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# --------------------------------------------------
# TEST 1: RESUME PARSING AND DATABASE STORAGE
# --------------------------------------------------

def test_resume_parsing(client):

    resume_path = Path("uploads/sample_resume.pdf")

    assert resume_path.exists(), (
        f"Resume file not found: {resume_path.resolve()}"
    )

    with resume_path.open("rb") as resume_file:
        response = client.post(
            "/api/v1/resume/parse",
            files={
                "file": (
                    resume_path.name,
                    resume_file,
                    "application/pdf"
                )
            }
        )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["message"] == "Resume parsed and saved successfully"
    assert data["filename"] == resume_path.name
    assert "extracted_data" in data

    extracted_data = data["extracted_data"]

    assert extracted_data["name"]
    assert extracted_data["email"]
    assert extracted_data["skills"]
    assert extracted_data["qualification"]

    print("\nResume parsing test passed!")
    print("Qualification:", extracted_data["qualification"])
    print("Extracted skills:", extracted_data["skills"])


# --------------------------------------------------
# TEST 2: COMPLETE USER ONBOARDING WORKFLOW
# --------------------------------------------------

def test_complete_onboarding_flow(client, monkeypatch):

    captured = {}

    # Mock email delivery; no real email will be sent
    def fake_send_email_otp(recipient_email, otp):
        captured["otp"] = otp

    monkeypatch.setattr(
        otp_service,
        "send_email_otp",
        fake_send_email_otp
    )

    email = f"e2e_{uuid4().hex}@example.com"
    password = "E2E-Test-Password-123!"

    # 1. USER REGISTRATION

    registration_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "E2E Test User",
            "email": email,
            "phone": "9876543210",
            "password": password
        }
    )

    assert registration_response.status_code == 201, (
        registration_response.text
    )

    assert "otp" in captured

    print("\nRegistration successful!")

    # 2. EMAIL OTP VERIFICATION

    verification_response = client.post(
        "/api/v1/auth/verify-2fa",
        json={
            "email": email,
            "channel": "email",
            "otp": captured["otp"]
        }
    )

    assert verification_response.status_code == 200, (
        verification_response.text
    )

    verification_data = verification_response.json()

    assert verification_data["is_active"] is True
    assert verification_data["is_verified"] is True

    print("Email OTP verification successful!")

    # 3. USER LOGIN

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200, (
        login_response.text
    )

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    print("User login successful!")

    # 4. EXISTING USER PROFILE RETRIEVAL

    user_response = client.get(
        "/api/v1/users/me",
        headers=headers
    )

    assert user_response.status_code == 200, user_response.text

    user_data = user_response.json()

    assert user_data["email"] == email
    assert user_data["is_active"] is True
    assert user_data["is_verified"] is True

    print("User profile retrieval successful!")

    # 5. NEW PROFILE API: GET

    profile_response = client.get(
        "/api/v1/profile",
        headers=headers
    )

    assert profile_response.status_code == 200, (
        profile_response.text
    )

    profile_data = profile_response.json()

    assert profile_data["email"] == email
    assert profile_data["is_active"] is True
    assert profile_data["is_verified"] is True
    assert profile_data["skills"] == []

    print("GET Profile API successful!")

    # 6. NEW PROFILE API: PATCH

    update_response = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "full_name": "E2E Updated User",
            "phone": "9876543210"
        }
    )

    assert update_response.status_code == 200, (
        update_response.text
    )

    updated_data = update_response.json()

    assert updated_data["full_name"] == "E2E Updated User"
    assert updated_data["phone"] == "9876543210"

    print("PATCH Profile API successful!")

    # 7. VERIFY PROFILE UPDATE PERSISTENCE

    persisted_response = client.get(
        "/api/v1/profile",
        headers=headers
    )

    assert persisted_response.status_code == 200, (
        persisted_response.text
    )

    persisted_data = persisted_response.json()

    assert persisted_data["full_name"] == "E2E Updated User"
    assert persisted_data["phone"] == "9876543210"

    print("Profile persistence verification successful!")

    # 8. STUDENT DASHBOARD ACCESS

    dashboard_response = client.get(
        "/api/v1/dashboard/redirect",
        headers=headers
    )

    assert dashboard_response.status_code == 200, (
        dashboard_response.text
    )

    dashboard_data = dashboard_response.json()

    assert dashboard_data["dashboard"] == "student"
    assert dashboard_data["redirect_url"] == "/dashboard/student"
    assert dashboard_data["user"]["is_active"] is True
    assert dashboard_data["user"]["is_verified"] is True

    print("Student dashboard access successful!")

    # FINAL RESULT

    print("\n========================================")
    print("COMPLETE ONBOARDING INTEGRATION PASSED!")
    print("========================================")
