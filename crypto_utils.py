import os
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from config import CHUNK_SIZE

def encrypt_chunk(data: bytes, enc_key: bytes, mac_key: bytes) -> bytes:
    """
    Encrypts a single chunk of data using AES-256-CBC and computes HMAC-SHA256 (Encrypt-then-MAC).
    """
    # Generate random IV
    iv = os.urandom(16)
    
    # Pad data to 16 bytes (PKCS7)
    pad_len = 16 - (len(data) % 16)
    padded_data = data + bytes([pad_len] * pad_len)
    
    # Encrypt
    cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Compute HMAC over IV + Ciphertext
    h = hmac.new(mac_key, iv + ciphertext, hashlib.sha256)
    mac = h.digest()
    
    # Format: IV (16 bytes) + MAC (32 bytes) + Ciphertext
    return iv + mac + ciphertext

def decrypt_chunk(encrypted_data: bytes, enc_key: bytes, mac_key: bytes) -> bytes:
    """
    Verifies HMAC and decrypts a single chunk.
    """
    iv = encrypted_data[:16]
    mac = encrypted_data[16:48]
    ciphertext = encrypted_data[48:]
    
    # Verify HMAC
    h = hmac.new(mac_key, iv + ciphertext, hashlib.sha256)
    expected_mac = h.digest()
    
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("HMAC verification failed! Data integrity compromised.")
        
    # Decrypt
    cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove padding
    pad_len = padded_data[-1]
    return padded_data[:-pad_len]

def encrypt_file(input_filepath, output_filepath, enc_key, mac_key):
    """
    Reads a file in chunks, encrypts each chunk, and writes to output.
    """
    with open(input_filepath, 'rb') as f_in, open(output_filepath, 'wb') as f_out:
        while True:
            chunk = f_in.read(CHUNK_SIZE)
            if not chunk:
                break
            
            encrypted_chunk = encrypt_chunk(chunk, enc_key, mac_key)
            # Write 4-byte length prefix to frame the chunks in the file stream
            f_out.write(len(encrypted_chunk).to_bytes(4, byteorder='big'))
            f_out.write(encrypted_chunk)

def decrypt_file(input_filepath, output_filepath, enc_key, mac_key):
    """
    Reads framed encrypted chunks, decrypts them, and writes plaintext to output.
    """
    with open(input_filepath, 'rb') as f_in, open(output_filepath, 'wb') as f_out:
        while True:
            length_bytes = f_in.read(4)
            if not length_bytes:
                break
            
            chunk_length = int.from_bytes(length_bytes, byteorder='big')
            encrypted_chunk = f_in.read(chunk_length)
            
            if len(encrypted_chunk) != chunk_length:
                raise ValueError("Incomplete chunk read. File may be corrupted.")
                
            plaintext = decrypt_chunk(encrypted_chunk, enc_key, mac_key)
            f_out.write(plaintext)
