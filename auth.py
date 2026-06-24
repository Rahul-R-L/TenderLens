import os
import bcrypt
import secrets
import resend

from dotenv import load_dotenv


# ============================================
# LOAD ENV
# ============================================

load_dotenv()

RESEND_API_KEY = os.getenv(
    "RESEND_API_KEY"
)

APP_URL = os.getenv(
    "APP_URL"
)

APP_NAME = os.getenv(
    "APP_NAME",
    "TenderLens"
)

resend.api_key = (
    RESEND_API_KEY
)

# ============================================
# HASH PASSWORD
# ============================================

def hash_password(

    password

):

    return bcrypt.hashpw(

        password.encode(),

        bcrypt.gensalt()

    ).decode()
    
# ============================================
# VERIFY PASSWORD
# ============================================

def verify_password(

    password,

    password_hash

):

    return bcrypt.checkpw(

        password.encode(),

        password_hash.encode()

    )
    

# ============================================
# GENERATE TOKEN
# ============================================

def generate_token():

    return secrets.token_urlsafe(
        32
    )
    
    
# ============================================
# SEND VERIFICATION EMAIL
# ============================================

def send_verification_email(

    email,

    token

):

    verify_link = (

        f"{APP_URL}"
        f"/verify"
        f"?token={token}"

    )

    html = f"""
    <h2>
        Welcome to {APP_NAME}
    </h2>

    <p>

        Please verify your email
        address by clicking
        the link below.

    </p>

    <p>

        <a href="{verify_link}">
            Verify Email
        </a>

    </p>

    <p>

        As an early adopter,
        you will receive
        complimentary access
        to TenderLens Pro
        during the launch period.

    </p>
    """

    resend.Emails.send({

        "from":
        f"{APP_NAME} <noreply@tenderlens.in>",

        "to":
        [email],

        "subject":
        f"Verify your {APP_NAME} account",

        "html":
        html
    })

    return True
    
    
# ============================================
# SEND PASSWORD RESET EMAIL
# ============================================

def send_password_reset_email(

    email,

    reset_code

):

    html = f"""
    <h2>Password Reset Request</h2>

    <p>

        Your TenderLens password reset code is:

    </p>

    <h1>{reset_code}</h1>

    <p>

        This code can only be used once.

    </p>

    <p>

        If you did not request a password reset,
        please ignore this email.

    </p>
    """

    resend.Emails.send({

        "from":
        f"{APP_NAME} <noreply@tenderlens.in>",

        "to":
        [email],

        "subject":
        "TenderLens Password Reset",

        "html":
        html

    })

    return True
