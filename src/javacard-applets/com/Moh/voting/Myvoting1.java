/** 
 * Copyright (c) 1998, 2024, Oracle and/or its affiliates. All rights reserved.
 * 
 */


package com.moh.voting;
import javacard.framework.*;
import javacard.security.*; // Import for KeyBuilder and AESKey
import javacardx.crypto.*; // Import for Cipher

/**
 * Applet class that includes AES ECB encryption functionality.
 *
 * @author <user> (modified by AI)
 */
public class Myvoting1 extends Applet {

    // --- Constants ---
    // Original instruction code
    private static final byte SERVICE_ID = (byte) 0xCA;
    // New instruction code for AES encryption
    private static final byte INS_ENCRYPT_AES_ECB = (byte) 0x10; // Choose an unused INS code
    // New instructio code for AES decryption
    private static final byte INS_DECRYPT_AES_ECB = (byte) 0x11;
    // Response Auth instruction
    private static final byte INS_RESPOND_AUTH = (byte) 0x12;
    // New instruction codes for puplic key and signing bank data
    
    // Voting Data Command 
    private static final byte INS_GET_VOTER_DATA = (byte) 0x13;
    
    // AES Key size (128 bits / 16 bytes)
    private static final short AES_KEY_LENGTH_BYTES = (short) 16;
    // AES Block size (128 bits / 16 bytes)
    private static final short AES_BLOCK_SIZE = (short) 16;
    // --- MODIFIED: New instructions for ECDSA signature ---
    private static final byte INS_GET_voting_DATA_SIGNATURE = (byte) 0x51;
    private static final byte INS_GET_PUBLIC_KEY = (byte) 0x52;

    // --- Member Variables ---
    private static final byte[] nonce = new byte[]{0x01, 0x02, 0x03, 0x04, 0x05, 0x11, 0x12, 0x13, 0x14, 0x15, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26};
    private static final byte[] cardID = new byte[]{0x01, 0x04, 0x03, 0x02, 0x05, 0x11, 0x12, 0x13, 0x15, 0x14, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26};
    
    
    //--------------Voter Data---------------
     private static final byte[] VoterData = new byte[]{ 
    		 (byte) 0x7f, (byte) 0x73, (byte) 0x27, (byte) 0xf0, (byte) 0x74, (byte) 0x7c, (byte) 0xc4, (byte) 0xb7, 
    		 (byte) 0xe6, (byte) 0x55, (byte) 0xf2, (byte) 0x48, (byte) 0x57, (byte) 0xdf, (byte) 0x89, (byte) 0x10, 
    		 (byte) 0x94, (byte) 0xd1, (byte) 0x09, (byte) 0x24, (byte) 0xbc, (byte) 0x30, (byte) 0x07, (byte) 0xdf, 
    		 (byte) 0x1a, (byte) 0xc7, (byte) 0x1c, (byte) 0xaa, (byte) 0x83, (byte) 0x20, (byte) 0x41, (byte) 0x70, 
    		 (byte) 0xb4, (byte) 0x96, (byte) 0x51, (byte) 0x78, (byte) 0xd0, (byte) 0x30, (byte) 0x1a, (byte) 0xbd, 
    		 (byte) 0xde, (byte) 0x3f, (byte) 0xe1, (byte) 0xa1, (byte) 0xef, (byte) 0x74, (byte) 0x16, (byte) 0x17, 
    		 (byte) 0x3a, (byte) 0x0f, (byte) 0x48, (byte) 0xd1, (byte) 0x5c, (byte) 0x26, (byte) 0xe3, (byte) 0x1b, 
    		 (byte) 0x5f, (byte) 0x8e, (byte) 0x70, (byte) 0xc1, (byte) 0xcb, (byte) 0xd3, (byte) 0x13, (byte) 0x39, 
    		 (byte) 0x34, (byte) 0x27, (byte) 0xd7, (byte) 0x25, (byte) 0x2d, (byte) 0x63, (byte) 0x17, (byte) 0x1a, 
    		 (byte) 0xf6, (byte) 0x19, (byte) 0x12, (byte) 0x0c, (byte) 0x93, (byte) 0x5d, (byte) 0xa3, (byte) 0x2f, 
    		 (byte) 0x28, (byte) 0xf1, (byte) 0x11, (byte) 0x9a, (byte) 0x44, (byte) 0xd2, (byte) 0x57, (byte) 0xe4, 
    		 (byte) 0x48, (byte) 0x68, (byte) 0xab, (byte) 0x06, (byte) 0x87, (byte) 0x68, (byte) 0x78, (byte) 0xd8, 
    		 (byte) 0x28, (byte) 0x6a, (byte) 0x20, (byte) 0xf3, (byte) 0x7c, (byte) 0x5c, (byte) 0x60, (byte) 0x08, 
    		 (byte) 0xae, (byte) 0x0a, (byte) 0x79, (byte) 0xe5, (byte) 0x6b, (byte) 0x1a, (byte) 0x22, (byte) 0x9e, 
    		 (byte) 0x5e, (byte) 0xcd, (byte) 0xe6, (byte) 0xfc, (byte) 0x88, (byte) 0x84, (byte) 0x1d, (byte) 0xba, 
    		 (byte) 0x3f, (byte) 0x7f, (byte) 0x50, (byte) 0x81, (byte) 0x63, (byte) 0x86, (byte) 0x21, (byte) 0xcb, 
    		 (byte) 0xa5, (byte) 0xe9, (byte) 0x8c, (byte) 0x4c, (byte) 0x07, (byte) 0x53, (byte) 0x7b, (byte) 0x75, 
    		 (byte) 0x3c, (byte) 0x89, (byte) 0x5a, (byte) 0x6d, (byte) 0x47, (byte) 0x66, (byte) 0x9f, (byte) 0x8d, 
    		 (byte) 0xb4, (byte) 0xd7, (byte) 0x2e, (byte) 0x6c, (byte) 0xc8, (byte) 0x7f, (byte) 0x90, (byte) 0x2a, 
    		 (byte) 0xca, (byte) 0xba, (byte) 0x8f, (byte) 0xcd, (byte) 0xa2, (byte) 0xb0, (byte) 0x64, (byte) 0xdd, 
    		 (byte) 0x82, (byte) 0x4d, (byte) 0x5f, (byte) 0x50, (byte) 0xf9, (byte) 0xb0, (byte) 0x9c, (byte) 0x63, 
    		 (byte) 0xa0, (byte) 0x28, (byte) 0x99, (byte) 0x7e, (byte) 0x86, (byte) 0x3b, (byte) 0xc8, (byte) 0xbf, 
    		 (byte) 0x48, (byte) 0x07, (byte) 0xc0, (byte) 0x81, (byte) 0x2f, (byte) 0xf4, (byte) 0xdd, (byte) 0x14, 
    		 (byte) 0x11, (byte) 0xe1, (byte) 0x4c, (byte) 0xb0, (byte) 0xeb, (byte) 0xd3, (byte) 0xb7, (byte) 0xca

};

    // AES Key object
    private AESKey aesKey;
    // Cipher object for AES operations
    private Cipher aesEcbCipher;
    // --- MODIFIED: New members for ECDSA signature ---
    private KeyPair ecdsaKeyPair;
    private Signature ecdsaSigner;
    // --- END MODIFIED ---

    // Transient buffer for encryption operations to avoid overwriting APDU buffer prematurely
    // Adjust size if you expect larger data blocks, ensure it's a multiple of AES_BLOCK_SIZE
    private byte[] transientBuffer;
    
     // Authentication State
    private static final byte STATE_IDLE = 0x00;
    private static final byte STATE_SERVICE_SELECTED = 0x01;
    private static final byte STATE_CLIENTAUTHENTICATED = 0x02;
    private byte authState = STATE_IDLE;


    /**
     * Installs this applet.
     *
     * @param bArray  the array containing installation parameters
     * @param bOffset the starting offset in bArray
     * @param bLength the length in bytes of the parameter data in bArray
     */
    public static void install(byte[] bArray, short bOffset, byte bLength) throws ISOException {
        new Myvoting1(bArray, bOffset, bLength);
    }

    /**
     * Only this class's install method should create the applet object.
     */
    protected Myvoting1(byte[] bArray, short bOffset, byte bLength) {
        // --- Key Initialization (Example - Use a secure mechanism in production!) ---
        // IMPORTANT: Hardcoding keys like this is insecure for production systems.
        // Keys should be securely provisioned, e.g., via GlobalPlatform SCP.
        byte[] tempKeyBytes = {
                (byte) 0x00, (byte) 0x01, (byte) 0x02, (byte) 0x03,
                (byte) 0x04, (byte) 0x05, (byte) 0x06, (byte) 0x07,
                (byte) 0x08, (byte) 0x09, (byte) 0x0A, (byte) 0x0B,
                (byte) 0x0C, (byte) 0x0D, (byte) 0x0E, (byte) 0x0F
        };

        try {
            // Create the AES key object
            aesKey = (AESKey) KeyBuilder.buildKey(KeyBuilder.TYPE_AES, KeyBuilder.LENGTH_AES_128, false);
            // Set the key value
            aesKey.setKey(tempKeyBytes, (short) 0);

            // Create the AES ECB Cipher object (No Padding)
            // ALG_AES_BLOCK_128_ECB_NOPAD requires data length to be a multiple of 16 bytes.
            aesEcbCipher = Cipher.getInstance(Cipher.ALG_AES_BLOCK_128_ECB_NOPAD, false);

            // Allocate transient buffer for crypto operations
            // Size should be sufficient for largest expected input/output + potential overhead
            // For ECB NOPAD, input size == output size. Let's allocate for 256 bytes max.
            transientBuffer = JCSystem.makeTransientByteArray((short) 256, JCSystem.CLEAR_ON_DESELECT);

            // --- MODIFIED: ECDSA Initialization ---
            // IMPORTANT: In production, keys should be securely provisioned, not generated with default parameters.
            // Create a KeyPair object for ECDSA with a 256-bit key (SECP256r1 is the Javacard default for this size)
            ecdsaKeyPair = new KeyPair(KeyPair.ALG_EC_FP, KeyBuilder.LENGTH_EC_FP_256);
            ecdsaKeyPair.genKeyPair(); // Generate the key pair

            // Create a Signature object instance for SHA-256 based ECDSA.
            ecdsaSigner = Signature.getInstance(Signature.ALG_ECDSA_SHA_256, false);
            // --- END MODIFIED ---

        } catch (CryptoException e) {
            // Handle cryptography-related exceptions during initialization
             ISOException.throwIt((short)(ISO7816.SW_COMMAND_NOT_ALLOWED + e.getReason()));
        } catch (SystemException e) {
             // Handle memory allocation issues
             ISOException.throwIt((short)(ISO7816.SW_FILE_FULL + e.getReason())); // Example error code
        }

        // --- Applet Registration ---
        // Determine the AID length and offset from the installation parameters
        // bArray[bOffset] typically contains the AID length
        // bArray[bOffset+1] to bArray[bOffset+bArray[bOffset]] typically contains the AID
        register(bArray, (short) (bOffset + 1), bArray[bOffset]);
    }

    /**
     * Processes an incoming APDU.
     *
     * @param apdu the incoming APDU
     * @see APDU
     */
    @Override
    public void process(APDU apdu) throws ISOException {
        byte[] buffer = apdu.getBuffer();

        // Ignore APDU during applet selection
        if (selectingApplet()) {
            return;
        }

        // Check CLA byte (optional but good practice)
        // if (buffer[ISO7816.OFFSET_CLA] != YOUR_EXPECTED_CLA) {
        //     ISOException.throwIt(ISO7816.SW_CLA_NOT_SUPPORTED);
        // }

        byte ins = buffer[ISO7816.OFFSET_INS];

        switch (ins) {
            case SERVICE_ID: // Original instruction 0xCA
                handleServiceID(apdu);
                break;

            case INS_ENCRYPT_AES_ECB: // New instruction 0x10
                handleEncryptAesEcb(apdu);
                break;
            case INS_DECRYPT_AES_ECB:
                handleDecryptAesEcb(apdu);
                break;
            case INS_RESPOND_AUTH:
                handleRespondAuth(apdu);
                break;
            case INS_GET_VOTER_DATA:
                SendVoterData(apdu);
                break;

            
            // --- MODIFIED: New cases for ECDSA ---
            case INS_GET_PUBLIC_KEY:
                sendPublicKey(apdu);
                break;
            case INS_GET_voting_DATA_SIGNATURE:
                sendvotingDataSignature(apdu);
                break;
            // --- END MODIFIED --    
                
            default:
                // Unsupported instruction
                ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
        }
    }

    /**
     * Handles the original GET DATA command.
     *
     * @param apdu The APDU object
     */
    private void sendBytes(APDU apdu, byte[] data) {
        byte[] buf = apdu.getBuffer();
        
        // P1|P2 form a 16-bit offset into the data.
        short offset = Util.getShort(buf, ISO7816.OFFSET_P1);
        
        // Le is the maximum number of bytes the terminal expects.
        short le = apdu.setOutgoing(); //the chunk size

        short dataLen = (short)data.length;

        // Basic validation
        if (offset < 0 || offset >= dataLen) {
            ISOException.throwIt(ISO7816.SW_WRONG_P1P2);
        }
        
        // Determine how many bytes to send in this chunk.
        short remaining = (short)(dataLen - offset);
        short sendLen = (le < remaining) ? le : remaining; //le < remaining then sendLen = le else sendLen = remaining.
        
        // Set the actual outgoing length and send the data chunk.
        apdu.setOutgoingLength(sendLen);
        apdu.sendBytesLong(data, offset, sendLen);
    }
     
    private void handleServiceID(APDU apdu) {
        // Keep the original functionality
        byte[] dataToSend = nonce;
        short len = (short) dataToSend.length;

        apdu.setOutgoing();
        apdu.setOutgoingLength(len);
        apdu.sendBytesLong(dataToSend, (short) 0, len);
    }
    
    private void sendPublicKey(APDU apdu) {
        byte[] buffer = apdu.getBuffer();
        ECPublicKey pubKey = (ECPublicKey) ecdsaKeyPair.getPublic();

        apdu.setOutgoing();
        short len = pubKey.getW(buffer, (short) 0);
        apdu.setOutgoingLength(len);
        apdu.sendBytes((short) 0, len);
    }

    /**
     * Signs the entire 'bankData' array using ECDSA and sends the signature.
     * This operation requires the client to be authenticated.
     * @param apdu The APDU object
     */
    private void sendvotingDataSignature(APDU apdu) throws ISOException {
        if (authState != STATE_CLIENTAUTHENTICATED) {
            // Not yet authenticated
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
            return;
        }

        byte[] buffer = apdu.getBuffer();
        ECPrivateKey privKey = (ECPrivateKey) ecdsaKeyPair.getPrivate();

        short signatureLen = 0;
        try {
            // Initialize the signer with the private key for signing
            ecdsaSigner.init(privKey, Signature.MODE_SIGN);
            // Sign the entire bankData array and place the result in the APDU buffer
            signatureLen = ecdsaSigner.sign(VoterData, (short) 0, (short) VoterData.length, buffer, (short) 0);
        } catch (CryptoException e) {
            ISOException.throwIt((short)(ISO7816.SW_SECURITY_STATUS_NOT_SATISFIED + e.getReason()));
        }

        // Send the generated signature
        apdu.setOutgoing();
        apdu.setOutgoingLength(signatureLen);
        apdu.sendBytes((short) 0, signatureLen);
    }
    /**
     * Handles the AES ECB encryption command (INS = 0x10).
     * Expects data in the command data field, length must be a multiple of 16.
     * Encrypts the data and sends the ciphertext back.
     *
     * @param apdu The APDU object
     */
    private void handleEncryptAesEcb(APDU apdu) throws ISOException {
        byte[] buffer = apdu.getBuffer();

        // Receive incoming data
        // setIncomingAndReceive() reads data into the APDU buffer at OFFSET_CDATA
        short bytesRead = apdu.setIncomingAndReceive();

        // Lc value from the APDU header (actual length received is bytesRead)
        short lc = apdu.getIncomingLength();

        // Validate data length
        if (bytesRead != lc) {
            // This shouldn't happen if the terminal behaves correctly, but check anyway
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        if (lc <= 0) {
             ISOException.throwIt(ISO7816.SW_WRONG_LENGTH); // No data sent
        }
        // Crucial check for ECB NoPadding: Length MUST be a multiple of block size
        if ((lc % AES_BLOCK_SIZE) != 0) {
             ISOException.throwIt(ISO7816.SW_WRONG_LENGTH); // Invalid length for AES ECB NOPAD
        }
        // Check if data exceeds our transient buffer capacity
        if (lc > (short)transientBuffer.length) {
             ISOException.throwIt(ISO7816.SW_WRONG_LENGTH); // Data too large for buffer
        }

        // *** FIX: Initialize ciphertextLen to satisfy Java compiler's definite assignment check ***
        short ciphertextLen = 0;
        try {
            // Initialize the cipher for encryption with the AES key
            aesEcbCipher.init(aesKey, Cipher.MODE_ENCRYPT);

            // Perform encryption
            // Input: APDU buffer starting at OFFSET_CDATA, length bytesRead
            // Output: transientBuffer starting at offset 0
            ciphertextLen = aesEcbCipher.doFinal(buffer, ISO7816.OFFSET_CDATA, bytesRead,
                                                  transientBuffer, (short) 0);

        } catch (CryptoException e) {
            // Handle encryption errors
             ISOException.throwIt((short)(ISO7816.SW_SECURITY_STATUS_NOT_SATISFIED + e.getReason()));
        }

        // Send the encrypted data (ciphertext) back
        apdu.setOutgoing();
        apdu.setOutgoingLength(ciphertextLen); // Should be same as bytesRead for ECB NOPAD
        apdu.sendBytesLong(transientBuffer, (short) 0, ciphertextLen);
    }
  private void handleDecryptAesEcb(APDU apdu) throws ISOException {
        byte[] buffer = apdu.getBuffer();
        short bytesRead = apdu.setIncomingAndReceive();
        short lc = apdu.getIncomingLength();
        if (lc <= 0 || (lc % AES_BLOCK_SIZE) != 0 || lc > (short)transientBuffer.length) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        short outputLen = 0;
        try {
            aesEcbCipher.init(aesKey, Cipher.MODE_DECRYPT);
            outputLen = aesEcbCipher.doFinal(buffer, ISO7816.OFFSET_CDATA, bytesRead,
                                             transientBuffer, (short) 0);
        } catch (CryptoException e) {
            ISOException.throwIt((short)(ISO7816.SW_SECURITY_STATUS_NOT_SATISFIED + e.getReason()));
        }
        
       if (Util.arrayCompare(transientBuffer, (short) 0,
                          nonce, (short) 0,
                          AES_BLOCK_SIZE) != 0) {
        // nonce mismatch → authentication failed
        ISOException.throwIt(ISO7816.SW_SECURITY_STATUS_NOT_SATISFIED);
    } 
        authState = STATE_CLIENTAUTHENTICATED;
        //apdu.setOutgoing();
        //apdu.setOutgoingLength(outputLen);
        //apdu.sendBytesLong(transientBuffer, (short) 0, outputLen);
    }
    
    private void handleRespondAuth(APDU apdu) throws ISOException {
    if (authState != STATE_CLIENTAUTHENTICATED) {
        // Not yet authenticated
        ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        return;
    }

    // readerNonce lives in transientBuffer[16..31] from previous decrypt
    final short PART_SIZE = AES_BLOCK_SIZE;
    byte[] outBuf = apdu.getBuffer();
    short offset = ISO7816.OFFSET_CDATA;

    // Prepare plaintext = readerNonce || cardID
    // Copy readerNonce
    Util.arrayCopyNonAtomic(
        transientBuffer, PART_SIZE,
        outBuf, offset,
        PART_SIZE
    );
    // Copy cardID right after
    Util.arrayCopyNonAtomic(
        cardID, (short) 0,
        outBuf, (short)(offset + PART_SIZE),
        PART_SIZE
    );
    
     short totalLen = (short)(2 * PART_SIZE);
     
     short cipherLen = 0 ;
     try {
        aesEcbCipher.init(aesKey, Cipher.MODE_ENCRYPT);
        cipherLen = aesEcbCipher.doFinal(
            outBuf, offset, totalLen,
            outBuf, offset
        );
    } catch (CryptoException e) {
        ISOException.throwIt((short)
            (ISO7816.SW_SECURITY_STATUS_NOT_SATISFIED + e.getReason()));
        return;
    }

    // Send ciphertext back
    apdu.setOutgoing();
    apdu.setOutgoingLength(cipherLen);
    apdu.sendBytesLong(outBuf, offset, cipherLen);
     
    }
    
    private void SendVoterData(APDU apdu) throws ISOException {
      if (authState != STATE_CLIENTAUTHENTICATED) {
        // Not yet authenticated
        ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        return;
     }
      byte[] VoterDataToSend = VoterData;
        short len = (short) VoterDataToSend.length;

        apdu.setOutgoing();
        apdu.setOutgoingLength(len);
        apdu.sendBytesLong(VoterDataToSend, (short) 0, len);
     
    
    }
    
  }
