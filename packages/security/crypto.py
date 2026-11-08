"""
Cryptographic envelope encryption, blind indexing, and verification digests.
Ensures zero plaintext identifiers or passwords in logs, traces, or unencrypted storage.
"""
import os
import hmac
import hashlib
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Default keys for local dev / testing if env vars not provided
DEFAULT_MASTER_KEY = b"\x01" * 32
DEFAULT_BLIND_INDEX_KEY = b"\x02" * 32


class EnvelopeVault:
    def __init__(self, master_key: bytes | None = None, blind_index_key: bytes | None = None):
        raw_key = master_key or os.getenv("APP_MASTER_ENCRYPTION_KEY")
        if isinstance(raw_key, str):
            self.master_key = hashlib.sha256(raw_key.encode()).digest()
        elif isinstance(raw_key, bytes):
            self.master_key = raw_key
        else:
            self.master_key = DEFAULT_MASTER_KEY

        raw_blind = blind_index_key or os.getenv("APP_BLIND_INDEX_KEY")
        if isinstance(raw_blind, str):
            self.blind_index_key = hashlib.sha256(raw_blind.encode()).digest()
        elif isinstance(raw_blind, bytes):
            self.blind_index_key = raw_blind
        else:
            self.blind_index_key = DEFAULT_BLIND_INDEX_KEY

        self.aesgcm = AESGCM(self.master_key)

    def encrypt(self, plaintext: str, associated_data: str = "") -> str:
        """Encrypt plaintext string using AES-256-GCM. Returns format: v1:nonce:ciphertext_b64."""
        nonce = os.urandom(12)
        ad = associated_data.encode("utf-8") if associated_data else None
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), ad)
        return f"v1:{b64encode(nonce).decode('ascii')}:{b64encode(ciphertext).decode('ascii')}"

    def decrypt(self, encrypted_envelope: str, associated_data: str = "") -> str:
        """Decrypt payload produced by encrypt."""
        parts = encrypted_envelope.split(":")
        if len(parts) != 3 or parts[0] != "v1":
            raise ValueError("Invalid envelope encryption format")
        nonce = b64decode(parts[1])
        ciphertext = b64decode(parts[2])
        ad = associated_data.encode("utf-8") if associated_data else None
        plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, ad)
        return plaintext_bytes.decode("utf-8")

    def compute_blind_index(self, value: str, scope: str = "") -> str:
        """Compute tenant/subject-scoped HMAC-SHA256 blind index for exact searchability."""
        normalized = value.strip().lower()
        scoped_message = f"{scope}:{normalized}".encode("utf-8")
        return hmac.new(self.blind_index_key, scoped_message, hashlib.sha256).hexdigest()

    @staticmethod
    def hash_verification_token(token: str, salt: str = "salt_v1") -> str:
        """Produce secure one-way hash of verification challenge token."""
        return hashlib.sha256(f"{salt}:{token}".encode("utf-8")).hexdigest()

    @staticmethod
    def secure_compare(val_a: str, val_b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        return hmac.compare_digest(val_a.encode("utf-8"), val_b.encode("utf-8"))


# Singleton default vault
vault = EnvelopeVault()
