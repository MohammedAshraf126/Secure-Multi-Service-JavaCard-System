# Secure Multi-Service JavaCard System

This project demonstrates a secure multi-service smart card system implemented using JavaCard applets and Python-based readers. The system focuses on providing secure access to various services (Banking, Voting, Transport, Electricity) by employing mutual authentication and digital signatures to protect data integrity and authenticity.

## Project Overview

The core idea is to consolidate different user-specific data onto a single smart card, which can then interact securely with various service readers. Each service applet on the card and its corresponding reader application are designed to perform a robust mutual authentication process using AES encryption. Furthermore, sensitive data retrieved from the card is digitally signed using ECDSA to ensure its authenticity and integrity.

## Features

* **Mutual Authentication:** Secure challenge-response protocol between the smart card and each service reader using AES encryption, preventing unauthorized access.
* **Data Confidentiality:** Sensitive data exchanged during authentication is encrypted using AES.
* **Data Authenticity & Integrity:** All critical data retrieved from the smart card is digitally signed using ECDSA, ensuring it originated from the legitimate card and has not been tampered with.
* **Modular Design:** Separate JavaCard applets for each service (Banking, Voting, Transport, Electricity), allowing for easy extension and management.
* **Python Reader Applications:** Command-line interfaces for interacting with the smart card, demonstrating the full communication and cryptographic workflows.

## Services Implemented

1.  **Banking Service:** Manages user balance and transaction history.
2.  **Voting Service:** Allows users to cast votes if eligible.
3.  **Transport Service:** Facilitates ticket purchases for public transport.
4.  **Electricity Service:** Enables charging of electricity meters.

## Authentication Process

The system employs a **challenge-response mutual authentication** protocol based on AES encryption. This ensures that both the smart card and the reader verify each other's authenticity before any sensitive data is exchanged.

### Mutual Authentication Steps:

1.  **Reader Selects Applet:** The reader initiates communication by selecting the specific service applet on the smart card.
2.  **Reader Requests Card Nonce:** The reader sends a `GET NONCE` command. The card responds with a random 16-byte nonce (challenge to the reader).
3.  **Reader Encrypts Challenge & Sends to Card:** The reader concatenates the received `card_nonce` with its `STATIC_READER_NONCE`. This 32-byte block is encrypted using the shared secret AES key (ECB mode) and sent to the card via `MUTUAL AUTH` command.
4.  **Card Decrypts & Verifies Reader's Challenge:** The card decrypts the data. If the first 16 bytes match its original nonce, the reader is authenticated.
5.  **Card Responds to Reader's Challenge:** The card prepares `STATIC_READER_NONCE || cardID`, encrypts it with the shared AES key, and sends it back via `RESPOND AUTH` command.
6.  **Reader Decrypts & Verifies Card's Response:** The reader decrypts the card's response. If the first 16 bytes match its `STATIC_READER_NONCE`, the card is authenticated.

Once both sides are mutually authenticated, secure data exchange can proceed.

## Cryptographic Technologies Used

* **AES (Advanced Encryption Standard) in ECB Mode:** Symmetric encryption for mutual authentication.
* **ECDSA (Elliptic Curve Digital Signature Algorithm):** Asymmetric cryptography for digital signatures, ensuring data authenticity and integrity. Each applet has its own ECDSA key pair.
* **SHA-256 (Secure Hash Algorithm 256-bit):** Hashing algorithm used in conjunction with ECDSA for signature generation and verification.

## Project Structure
- Secure-Multi-Service-JavaCard-System/
  - src/
    - javacard-applets/
      - com/
        - Moh/
          - transport/
            - transport.java
          - voting/
            - Myvoting1.java
        - Metwally/
          - Banking/
            - Banking.java
          - Electricity/
            - Electricity.java
    - python-readers/
      - bank_reader.py
      - Electricity_reader.py
      - transport_reader.py
      - voting_reader.py
  - data/
    - user_account.json
    - electricity_db.json
    - transport_db.json
    - DB_Voting.json
  - docs/
    - architecture.md
    - setup.md
    - usage.md
  - .gitignore
  - LICENSE
  - README.md
