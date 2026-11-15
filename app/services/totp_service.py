
import base64
import io

import pyotp
import qrcode


ISSUER_NAME = "ResumeAI"


def generate_totp_secret() -> str:
    """Generate a unique secret for a user."""
    return pyotp.random_base32()


def generate_provisioning_uri(
    email: str,
    secret: str
) -> str:
    """Generate the authenticator enrollment URI."""
    totp = pyotp.TOTP(secret)

    return totp.provisioning_uri(
        name=email,
        issuer_name=ISSUER_NAME
    )


def generate_qr_code(provisioning_uri: str) -> str:
    """Generate a QR code and return it as a Base64 PNG."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    encoded_image = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return f"data:image/png;base64,{encoded_image}"


def verify_totp_code(
    secret: str,
    otp: str
) -> bool:
    """Verify a six-digit authenticator code."""
    if not otp or not otp.isdigit() or len(otp) != 6:
        return False

    totp = pyotp.TOTP(secret)

    return totp.verify(
        otp,
        valid_window=1
    )
