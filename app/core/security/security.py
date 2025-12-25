import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, Literal, Optional, Tuple

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Create CryptContext once
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12, bcrypt__ident="2b"
)


def create_access_token(
    data: Dict[str, Any],
    created_at: datetime = datetime.utcnow(),
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
    to_encode = data.copy()
    iat = datetime.timestamp(datetime.utcnow())
    expire = created_at + (
        expires_delta or timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access", "iat": iat})
    return (
        jwt.encode(
            to_encode,
            settings.security.SECRET_KEY,
            algorithm=settings.security.ALGORITHM,
        ),
        datetime.fromtimestamp(iat),
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
        payload["iat"] = datetime.fromtimestamp(payload["iat"])
        return payload
    except ExpiredSignatureError:
        # Handle expired tokens explicitly
        raise ExpiredSignatureError(f"{token_type} token has expired")
    except JWTError:
        raise JWTError(f"Invalid {token_type} token")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


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
