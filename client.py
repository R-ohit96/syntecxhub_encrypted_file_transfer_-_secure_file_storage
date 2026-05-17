import socket
import os
import sys
from config import HOST, PORT, ENC_KEY, MAC_KEY
from crypto_utils import encrypt_file, decrypt_file

def send_file(sock, filepath):
    """
    Sends a file over an active socket.
    """
    filesize = os.path.getsize(filepath)
    filename = os.path.basename(filepath)
    
    # Send header
    header = f"UPLOAD|{filename}|{filesize}"
    sock.sendall(header.encode('utf-8'))
    
    # Wait for server OK
    response = sock.recv(1024).decode('utf-8')
    if response != "OK":
        print("[-] Server rejected upload.")
        return
        
    print(f"[*] Uploading encrypted file to server...")
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sock.sendall(chunk)
            
    # Wait for completion acknowledgment
    result = sock.recv(1024).decode('utf-8')
    print(f"[*] Server response: {result}")

def receive_file(sock, filename, save_path):
    """
    Receives a file over an active socket.
    """
    # Send header
    header = f"DOWNLOAD|{filename}"
    sock.sendall(header.encode('utf-8'))
    
    # Wait for server OK
    response = sock.recv(1024).decode('utf-8')
    if response.startswith("ERROR"):
        print(f"[-] {response}")
        return False
        
    parts = response.split('|')
    if parts[0] == "OK":
        filesize = int(parts[1])
        sock.sendall(b"READY")
        
        print(f"[*] Downloading encrypted file from server ({filesize} bytes)...")
        with open(save_path, 'wb') as f:
            remaining = filesize
            while remaining > 0:
                chunk_size = min(4096, remaining)
                chunk = sock.recv(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        print("[*] Download complete.")
        return True
    return False

def upload_secure(filepath):
    """
    Encrypts a local file and uploads the ciphertexts to the server.
    """
    if not os.path.exists(filepath):
        print(f"[-] File not found: {filepath}")
        return
        
    enc_filepath = filepath + ".enc"
    
    print("[*] Local phase: Encrypting file and generating HMACs...")
    try:
        encrypt_file(filepath, enc_filepath, ENC_KEY, MAC_KEY)
    except Exception as e:
        print(f"[-] Encryption failed: {e}")
        return

    print("[*] Network phase: Connecting to server...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            send_file(sock, enc_filepath)
    except ConnectionRefusedError:
        print("[-] Connection failed. Is the server running?")
    except Exception as e:
        print(f"[-] Transfer failed: {e}")
    finally:
        # Clean up local encrypted temporary file
        if os.path.exists(enc_filepath):
            os.remove(enc_filepath)

def download_secure(filename, save_path):
    """
    Downloads an encrypted file from the server and decrypts it locally.
    """
    enc_filepath = save_path + ".enc"
    
    print("[*] Network phase: Connecting to server...")
    download_success = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            download_success = receive_file(sock, filename + ".enc", enc_filepath)
    except ConnectionRefusedError:
        print("[-] Connection failed. Is the server running?")
    except Exception as e:
        print(f"[-] Transfer failed: {e}")

    if download_success and os.path.exists(enc_filepath):
        print("[*] Local phase: Verifying integrity and decrypting file...")
        try:
            decrypt_file(enc_filepath, save_path, ENC_KEY, MAC_KEY)
            print("[*] Success! File decrypted and saved to:", save_path)
        except Exception as e:
            print(f"[-] Decryption/Integrity Check failed: {e}")
            if os.path.exists(save_path):
                os.remove(save_path) # Remove partial or corrupted output
        finally:
            # Clean up local encrypted temporary file
            os.remove(enc_filepath)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python client.py upload <filepath>")
        print("  python client.py download <filename_on_server> [local_save_path]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    if cmd == "upload" and len(sys.argv) == 3:
        upload_secure(sys.argv[2])
    elif cmd == "download" and len(sys.argv) >= 3:
        filename_on_server = sys.argv[2]
        
        # If no save path is provided, default to client_downloads/ folder
        if len(sys.argv) == 4:
            save_path = sys.argv[3]
        else:
            if not os.path.exists("client_downloads"):
                os.makedirs("client_downloads")
            save_path = os.path.join("client_downloads", filename_on_server)
            
        # Ensure the directory for save_path exists
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        download_secure(filename_on_server, save_path)
    else:
        print("[-] Invalid arguments. Please check usage.")
