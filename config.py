import os

# Server configuration
HOST = '127.0.0.1'
PORT = 65432

# Cryptography configuration
CHUNK_SIZE = 64 * 1024  # 64 KB chunks

# In a real-world scenario, these should be derived from a user password via a KDF (e.g. PBKDF2/Argon2)
# and never hardcoded. Used here for demonstration.
import hashlib
MASTER_KEY = hashlib.sha256(b"SuperSecretMasterPassword").digest()
ENC_KEY = MASTER_KEY  # 32 bytes for AES-256
MAC_KEY = hashlib.sha256(b"SuperSecretMacPassword").digest() # 32 bytes for HMAC-SHA256
