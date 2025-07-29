1. Mutual Authentication Process
Our system employs a challenge-response mutual authentication protocol based on AES encryption. This ensures that both the smart card and the reader verify each other's authenticity before any sensitive data is exchanged. The process unfolds in these steps:

Step 1: Reader Selects Applet: The reader initiates communication by sending an APDU command (SELECT Applet) to select the specific service applet (e.g., Banking, Voting, Transport, Electricity) on the smart card.

Step 2: Reader Requests Card Nonce: The reader then sends a GET NONCE command (APDU 80 CA 00 00 05) to the selected applet. The smart card responds by generating and sending a unique, random 16-byte nonce (a "number once") to the reader. This nonce acts as the card's challenge to the reader.

Step 3: Reader Encrypts Challenge and Sends to Card: The reader takes the card_nonce received from the card and concatenates it with its own pre-defined STATIC_READER_NONCE (a 16-byte nonce known only to the reader). It then encrypts this 32-byte plaintext block using the shared secret AES key (AES in ECB mode). The resulting ciphertext is sent back to the card via the MUTUAL AUTH command (APDU 80 11 00 00). This is the reader's challenge to the card.

Step 4: Card Decrypts and Verifies Reader's Challenge: Upon receiving the encrypted data, the smart card decrypts it using its copy of the shared AES key. It then verifies if the first 16 bytes of the decrypted data match its own nonce that it sent in Step 2. If they match, the card has successfully authenticated the reader.

Step 5: Card Responds to Reader's Challenge: If the card successfully authenticates the reader, it proceeds to respond to the reader's challenge. It prepares a new plaintext block by concatenating the STATIC_READER_NONCE (which it received and verified in the previous step) with its own internal cardID. It encrypts this 32-byte block using the shared AES key and sends the ciphertext back to the reader via the RESPOND AUTH command (APDU 80 12 00 00 00).

Step 6: Reader Decrypts and Verifies Card's Response: The reader receives the card's encrypted response and decrypts it using its shared AES key. It then extracts the first 16 bytes and compares them to its original STATIC_READER_NONCE. If they match, the reader has successfully authenticated the card.

Once both the card and the reader have successfully authenticated each other, the authState on the card changes to STATE_CLIENTAUTHENTICATED, allowing for subsequent secure data exchanges.

2. Cryptographic Technologies Used
AES (Advanced Encryption Standard) in ECB (Electronic Codebook) Mode:

Purpose: Used for symmetric encryption and decryption during the mutual authentication process. It ensures the confidentiality of the nonces exchanged between the card and the reader.

Mechanism: Both the smart card and the reader share the same secret AES key (AES_KEY). Data is encrypted and decrypted in 16-byte blocks.

Note: While ECB mode is simple, its use for larger data sets can reveal patterns if plaintext blocks repeat. For this project's specific challenge-response, where unique nonces are used, its application is acceptable for authentication. However, for general data encryption, modes like CBC, CTR, or GCM are typically preferred due to better security properties against pattern exposure.

ECDSA (Elliptic Curve Digital Signature Algorithm):

Purpose: Used for digital signatures to ensure the authenticity and integrity of sensitive data retrieved from the smart card (e.g., bankData, VoterData, ElectricityData, transportData). This prevents an attacker from tampering with the data or impersonating the card.

Key Pair: Each applet on the smart card generates an ECDSA key pair:

Private Key: Stored securely on the smart card and used to sign the data.

Public Key: Exported to the reader and used to verify the signature.

Signing Process (on Card): The smart card uses its private key to generate a digital signature over the hash (SHA-256) of the data it's sending.

Verification Process (on Reader): The reader receives the data and its corresponding signature. It re-computes the hash of the received data and then uses the card's public key to verify if the signature is valid for that hash. If the verification succeeds, the reader is assured that:

The data originated from the authentic smart card (authenticity).

The data has not been altered since it was signed by the card (integrity).

SHA-256 (Secure Hash Algorithm 256-bit):

Purpose: Used as the hashing algorithm for ECDSA signatures. It generates a fixed-size 256-bit hash (or digest) of the data.

Role in Signatures: The digital signature is generated over this hash, not the raw data itself. This makes the signature process efficient and helps detect even minor changes to the data.

3. JavaCard Platform
JavaCard Applets: The core logic for each service (Banking, Voting, Transport, Electricity) resides in separate JavaCard applets (Banking.java, Myvoting1.java, transport.java, Electricity.java). These applets run on the JavaCard Operating System (JCOS) and interact with the physical hardware of the smart card.

APDU (Application Protocol Data Unit): The standard communication protocol used between the smart card reader and the JavaCard applet. Commands (C-APDU) are sent from the reader, and responses (R-APDU) are sent back from the card.

Javacard API: The applets utilize the JavaCard API for cryptographic operations (javacard.security.*, javacardx.crypto.*) and general applet management (javacard.framework.*).

4. Python Reader Applications
smartcard library: Used in the Python scripts (bank_reader.py, voting_reader.py, transport_reader.py, Electricity_reader.py) to interact with the smart card reader hardware and transmit/receive APDUs.

pycryptodome library: Used for implementing the cryptographic operations on the reader side, including AES encryption/decryption and ECDSA signature verification. This library is crucial for mirroring the cryptographic functions performed by the JavaCard applets.

json library: Used for parsing and managing the local databases (user_account.json, electricity_db.json, transport_db.json, DB_Voting.json) that store user-specific information relevant to each service.
