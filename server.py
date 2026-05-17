import socket
import os
from config import HOST, PORT

STORAGE_DIR = "server_storage"

def handle_client(conn, addr):
    print(f"[+] Connection established with {addr}")
    try:
        # First receive command header: UPLOAD|filename|filesize or DOWNLOAD|filename
        header = conn.recv(1024).decode('utf-8').strip()
        if not header:
            return
            
        parts = header.split('|')
        cmd = parts[0]
        
        if cmd == "UPLOAD":
            filename = parts[1]
            filesize = int(parts[2])
            conn.sendall(b"OK") # Acknowledge command
            
            filepath = os.path.join(STORAGE_DIR, filename)
            received = 0
            
            print(f"[*] Receiving file: {filename} ({filesize} bytes)")
            with open(filepath, 'wb') as f:
                remaining = filesize
                while remaining > 0:
                    chunk_size = min(4096, remaining)
                    chunk = conn.recv(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
                    
            print(f"[*] Successfully received and stored encrypted file: {filename}")
            conn.sendall(b"UPLOAD_SUCCESS")
            
        elif cmd == "DOWNLOAD":
            filename = parts[1]
            filepath = os.path.join(STORAGE_DIR, filename)
            
            if not os.path.exists(filepath):
                conn.sendall(b"ERROR|File not found on server")
                print(f"[-] Requested file not found: {filename}")
                return
                
            filesize = os.path.getsize(filepath)
            conn.sendall(f"OK|{filesize}".encode('utf-8'))
            
            # Wait for client readiness
            ack = conn.recv(1024)
            if ack == b"READY":
                print(f"[*] Sending file: {filename} ({filesize} bytes)")
                with open(filepath, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        conn.sendall(chunk)
                print(f"[*] Successfully sent encrypted file: {filename}")
                
    except Exception as e:
        print(f"[-] Error handling client {addr}: {e}")
    finally:
        conn.close()

def start_server():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
        
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow port reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[*] Secure File Storage Server listening on {HOST}:{PORT}")
        print(f"[*] Storage directory: {os.path.abspath(STORAGE_DIR)}")
        
        while True:
            conn, addr = server_socket.accept()
            handle_client(conn, addr)
    except KeyboardInterrupt:
        print("\n[*] Server shutting down.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
