# Project 2: Encrypted File Transfer & Secure File Storage

This project implements a secure, End-to-End Encrypted (E2EE) file transfer and storage system between a client and a server using Python. 

## Features
- **E2E Encryption**: Files are encrypted on the client using AES-256-CBC before transmission. The server never sees the plaintext data.
- **Data Integrity**: Every chunk of data is signed using HMAC-SHA256 (Encrypt-then-MAC pattern).
- **Chunking**: Large files are processed in 64KB chunks to maintain a low memory footprint.
- **Secure Storage**: The server stores only the encrypted payloads (`.enc` files) on disk.
- **TCP Sockets**: Raw TCP sockets are used to transmit the encrypted streams.

## Setup and Execution

1. Ensure required packages are installed:
   ```bash
   pip install cryptography
   ```

2. Start the Server:
   ```bash
   python server.py
   ```
   The server will listen on `127.0.0.1:65432` and store files in the `server_storage` directory.

3. Upload a file via Client:
   ```bash
   python client.py upload path/to/your/file.txt
   ```
   The client will encrypt the file locally to a `.enc` file, transfer the ciphertexts to the server, and delete the local temporary `.enc` file.

4. Download a file via Client:
   ```bash
   python client.py download file.txt downloaded_file.txt
   ```
   The client will download `file.txt.enc` from the server, verify the HMAC integrity of all chunks, decrypt it, and save it as `downloaded_file.txt`.

---

## Threat Model & Mitigations

### 1. Man-in-the-Middle (MitM) Attacks
- **Threat**: An attacker intercepts network traffic between the client and server to read or tamper with the files.
- **Mitigation**: 
  - **Confidentiality**: Files are encrypted with AES-256 before leaving the client. The attacker only intercepts ciphertexts.
  - **Integrity**: Every chunk is signed with HMAC-SHA256 (Encrypt-then-MAC). If an attacker tampers with the bytes in transit, the client's HMAC verification will fail upon decryption.
  
### 2. Server Compromise (Malicious Server)
- **Threat**: The server is breached or the server administrator attempts to read user files.
- **Mitigation**: 
  - Since this system uses End-to-End Encryption, the server never possesses the encryption (`ENC_KEY`) or authentication (`MAC_KEY`) keys. 
  - The server only holds `.enc` files. The data remains strictly confidential and tamper-evident even if the entire server disk is dumped.

### 3. Key Management Vulnerabilities
- **Threat**: Keys are hardcoded or poorly managed, allowing attackers to reverse-engineer them, or users losing keys, leading to permanent data loss.
- **Mitigation**: 
  - In a production environment, `ENC_KEY` and `MAC_KEY` should never be hardcoded. They should be securely derived from a strong user passphrase using a memory-hard Key Derivation Function (KDF) like **Argon2** or **PBKDF2**.
  - Secure enclaves or OS-level keychains should be used to manage derived keys.

### 4. Replay & Traffic Analysis Attacks
- **Threat**: An attacker captures a valid file upload and replays it later to overwrite newer files with older versions. Alternatively, an attacker observes metadata (e.g., file sizes, connection times) to infer user activity.
- **Mitigation**:
  - Wrapping the underlying TCP connection in **TLS (Transport Layer Security)** would provide Perfect Forward Secrecy, hide metadata (like `UPLOAD|filename|filesize` headers), and mitigate replay attacks at the network level.
