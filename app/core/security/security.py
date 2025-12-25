import random
import string
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal, Optional, Tuple

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Create CryptContext once - with fallback to direct bcrypt
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    # Test if it works
    pwd_context.hash("test")
    USE_PASSLIB = True
except Exception as e:
    print(f"Warning: passlib bcrypt initialization failed: {e}")
    print("Falling back to direct bcrypt usage")
    pwd_context = None
    USE_PASSLIB = False


def create_access_token(
    data: Dict[str, Any],
    created_at: datetime = None,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, datetime]:
    """
    Create a new access token

    Args:
        data: Payload to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    # Use current UTC time if created_at is not provided
    if created_at is None:
        created_at = datetime.now(timezone.utc).replace(tzinfo=None)

    to_encode = data.copy()

    # Use time.time() for proper UTC timestamps that match JWT expectations
    import time

    iat = time.time()  # Current UTC timestamp
    exp = (
        iat
        + (
            expires_delta or timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)
        ).total_seconds()
    )

    to_encode.update({"exp": exp, "type": "access", "iat": iat})
    return (
        jwt.encode(
            to_encode,
            settings.security.SECRET_KEY,
            algorithm=settings.security.ALGORITHM,
        ),
        datetime.fromtimestamp(iat),  # Return the actual timestamp used
    )


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    """
    Create a new refresh token

    Returns:
        Tuple of (token string, expiration datetime)
    """
    to_encode = data.copy()
    iat = datetime.timestamp(datetime.utcnow())
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=settings.security.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh", "iat": iat})
    return (
        jwt.encode(
            to_encode,
            settings.security.SECRET_KEY,
            algorithm=settings.security.ALGORITHM,
        ),
        datetime.fromtimestamp(iat),
    )


def create_verification_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    """
    Create a new verification token

    Args:
        data: Payload to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    iat = datetime.timestamp(datetime.utcnow())
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.security.VERIFICATION_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "verification", "iat": iat})
    return (
        jwt.encode(
            to_encode,
            settings.security.SECRET_KEY,
            algorithm=settings.security.ALGORITHM,
        ),
        datetime.fromtimestamp(iat),
    )


def verify_token(
    token: str, token_type: Literal["access", "refresh", "verification"]
) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token

    Args:
        token: The token to verify

    Returns:
        Decoded payload if valid, None if invalid

    Raises:
        JWTError: If token is malformed
        ExpiredSignatureError: If token has expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.security.SECRET_KEY,
            algorithms=[settings.security.ALGORITHM],
        )
        if payload.get("type") != token_type:
            raise JWTError(f"Invalid {token_type} token")
        # Keep iat as Unix timestamp for consistency
        return payload
    except ExpiredSignatureError:
        # Handle expired tokens explicitly
        raise ExpiredSignatureError(f"{token_type} token has expired")
    except JWTError:
        raise JWTError(f"Invalid {token_type} token")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Note: bcrypt has a 72-byte limit, so we truncate longer passwords.
    This is a security best practice as recommended by bcrypt documentation.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    try:
        # Ensure password is a string
        if not isinstance(password, str):
            password = str(password)

        # bcrypt has a 72-byte limit, truncate if necessary
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # Use passlib if available, otherwise direct bcrypt
        if USE_PASSLIB and pwd_context:
            with suppress(Exception):
                return pwd_context.hash(password)

        # Direct bcrypt implementation
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    except Exception as e:
        print(f"Password hashing error: {e}")
        print(
            f"Password: '{password}' (length: {len(password)} chars, {len(password.encode('utf-8'))} bytes)"
        )
        raise ValueError(f"Failed to hash password: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Note: bcrypt has a 72-byte limit, so we truncate longer passwords
    the same way as during hashing.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Ensure password is a string
        if not isinstance(plain_password, str):
            plain_password = str(plain_password)

        # Apply the same truncation as during hashing
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # Use passlib if available, otherwise direct bcrypt
        if USE_PASSLIB and pwd_context:
            with suppress(Exception):
                return pwd_context.verify(plain_password, hashed_password)

        # Direct bcrypt verification
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_password)

    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def create_otp(length: int = 6) -> Dict[str, Any]:
    """
    Generate a random OTP

    Args:
        length: Length of the OTP

    Returns:
        Random OTP
    """
    random_digits = string.digits
    OTP = "".join(random.SystemRandom().choice(random_digits) for _ in range(length))
    return {
        "otp": OTP,
        "created_at": datetime.utcnow(),
        "expire_at": datetime.utcnow()
        + timedelta(minutes=settings.security.RESET_PASSWORD_OTP_EXPIRE_MINUTES),
    }
