import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, encryption_key: str = None):
        """Initialize encryption service with a key."""
        if encryption_key:
            # Use provided key
            self.key = encryption_key.encode()
        else:
            # Use environment variable or generate a key
            env_key = os.getenv("ENCRYPTION_KEY")
            if env_key:
                self.key = env_key.encode()
            else:
                # Generate a key from a password (in production, use a proper secret)
                password = os.getenv(
                    "ENCRYPTION_PASSWORD", "default-password-change-in-production"
                ).encode()
                salt = os.getenv("ENCRYPTION_SALT", "default-salt-change-in-production").encode()

                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                self.key = base64.urlsafe_b64encode(kdf.derive(password))

        self.cipher_suite = Fernet(self.key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64 encoded result."""
        if not plaintext:
            return plaintext

        try:
            encrypted_data = self.cipher_suite.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt a base64 encoded encrypted string."""
        if not encrypted_text:
            return encrypted_text

        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def is_encrypted(self, text: str) -> bool:
        """Check if a string appears to be encrypted (basic heuristic)."""
        if not text:
            return False

        try:
            # Try to decode as base64 - encrypted strings should be base64 encoded
            base64.urlsafe_b64decode(text.encode())
            # If it decodes and doesn't look like a URI, it's probably encrypted
            return not (
                text.startswith(("postgresql://", "mysql://", "sqlite://", "mssql://"))
                or "://" in text
            )
        except Exception:
            return False


# Global encryption service instance
encryption_service = EncryptionService()
