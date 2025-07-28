import sys  # Import system-specific parameters and functions for system exit
import json  # Import JSON encoder and decoder for handling JSON data
import traceback  # Import traceback module for printing exception stack traces
from datetime import datetime  # Import datetime class for handling dates and times
from smartcard.System import readers  # Import smart card readers detection functionality
from smartcard.util import toHexString, toBytes  # Import utilities for hex string and byte conversions
from smartcard.Exceptions import NoCardException, CardConnectionException  # Import smart card specific exceptions
from Crypto.PublicKey import ECC  # Import Elliptic Curve Cryptography public key functionality
from Crypto.Signature import DSS  # Import Digital Signature Standard for signature verification
from Crypto.Hash import SHA256  # Import SHA-256 hashing algorithm
from Crypto.Cipher import AES  # Import Advanced Encryption Standard cipher

# --- Configuration ---
APPLET_AID = toBytes("A0 32 76 93 94 03")  # Application Identifier for the Electricity applet - unique ID to select the correct applet on the smart card
AES_KEY = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'  # 128-bit AES encryption key used for mutual authentication and data encryption
STATIC_READER_NONCE = bytes.fromhex("51525354554142434415212223242526")  # Fixed 16-byte nonce used by the reader for authentication challenge
# --- NEW: Database file for user accounts ---
USER_DB_FILE = 'electricity_db.json'  # Filename for the JSON database containing user account information

# --- APDU Instruction Constants (from Electricity.java) ---
INS_SELECT_APPLET = toBytes("00 A4 04 00")  # APDU command to select the electricity applet on the smart card
INS_GET_NONCE = toBytes("80 CA 00 00 05")  # APDU command to request a random nonce from the card for authentication
INS_MUTUAL_AUTH = toBytes("80 11 00 00")  # APDU command to send encrypted authentication challenge to the card
INS_RESPOND_AUTH = toBytes("80 12 00 00 00")  # APDU command to get the card's encrypted authentication response
INS_GET_ELECTRICITY_DATA = toBytes("00 13")  # APDU command to retrieve encrypted electricity meter data from the card
INS_GET_ELECTRICITY_DATA_SIGNATURE = toBytes("00 51 00 00")  # APDU command to get the digital signature of the electricity data
INS_GET_PUBLIC_KEY = toBytes("00 52 00 00")  # APDU command to retrieve the card's ECDSA public key for signature verification

def connect_to_card():
    """Establishes a connection with the smart card."""
    try:  # Begin exception handling block for connection errors
        reader = readers()[0]  # Get the first available smart card reader from the system
        connection = reader.createConnection()  # Create a connection object for communicating with the card
        connection.connect()  # Establish the actual connection to the smart card
        print(f" Connected to: {reader}\n")  # Display successful connection message with reader name
        return connection  # Return the established connection object
    except (IndexError, NoCardException):  # Catch errors when no reader/card is found
        print(" Error: No card or reader found.")  # Display error message to user
        sys.exit(1)  # Exit the program with error code 1

def transmit_and_check(conn, apdu, description):
    """Transmits an APDU and checks for a success (90 00) status word."""
    print(f"▶ {description}: {toHexString(apdu)}")  # Display the APDU command being sent in hex format
    resp, sw1, sw2 = conn.transmit(apdu)  # Send APDU to card and receive response data and status words
    print(f"   Response: {toHexString(resp)}, SW: {sw1:02X}{sw2:02X}")  # Display response data and status words in hex
    if (sw1, sw2) != (0x90, 0x00):  # Check if status words indicate success (90 00 means OK)
        print(f" Operation failed for: {description}")  # Display failure message if status is not success
        return None, False  # Return None and False to indicate failure
    return resp, True  # Return response data and True to indicate success

def run_authentication(conn, key):
    """Runs the full mutual authentication sequence."""
    print("--- 1. MUTUAL AUTHENTICATION ---")  # Display authentication phase header
    
    select_apdu = list(INS_SELECT_APPLET) + [len(APPLET_AID)] + list(APPLET_AID)  # Build SELECT APDU with applet AID length and AID bytes
    _, success = transmit_and_check(conn, select_apdu, "SELECT Applet")  # Send SELECT command to activate the electricity applet
    if not success: return False  # Return False if applet selection failed

    card_nonce_resp, success = transmit_and_check(conn, list(INS_GET_NONCE), "GET Card Nonce")  # Request random nonce from the card
    if not success: return False  # Return False if nonce retrieval failed
    
    card_nonce = bytes(card_nonce_resp)  # Convert response to bytes for the card's nonce
    reader_nonce = STATIC_READER_NONCE  # Use the predefined reader nonce
    plaintext = card_nonce + reader_nonce  # Concatenate card nonce and reader nonce for encryption

    cipher = AES.new(key, AES.MODE_ECB)  # Create AES cipher in ECB mode with the shared key
    encrypted_data = cipher.encrypt(plaintext)  # Encrypt the combined nonces
    
    mutual_auth_apdu = list(INS_MUTUAL_AUTH) + [len(encrypted_data)] + list(encrypted_data)  # Build mutual auth APDU with encrypted data
    _, success = transmit_and_check(conn, mutual_auth_apdu, "SEND Mutual Auth Challenge")  # Send encrypted challenge to card
    if not success:  # Check if mutual auth command failed
        print("   Authentication failed at step 3.")  # Display specific failure message
        return False  # Return False to indicate authentication failure
        
    respond_auth_resp, success = transmit_and_check(conn, list(INS_RESPOND_AUTH), "GET Respond Auth")  # Get card's encrypted response
    if not success:  # Check if response retrieval failed
        print("   Authentication failed at step 4.")  # Display specific failure message
        return False  # Return False to indicate authentication failure

    decrypted_response = cipher.decrypt(bytearray(respond_auth_resp))  # Decrypt the card's response using the same cipher
    responded_reader_nonce = decrypted_response[:16]  # Extract the first 16 bytes as the reader nonce
    
    if responded_reader_nonce == reader_nonce:  # Verify that card correctly encrypted our reader nonce
        print("   Reader nonce verified successfully.")  # Display successful verification message
        print(" Mutual Authentication successful!\n")  # Display overall authentication success
        return True  # Return True to indicate successful authentication
    else:  # If nonces don't match, authentication failed
        print("   Verification Failed: Reader nonce mismatch!")  # Display nonce mismatch error
        return False  # Return False to indicate authentication failure

def get_public_key(conn):
    """Retrieves the card's ECDSA public key."""
    print("--- 2a. RETRIEVING PUBLIC KEY ---")  # Display public key retrieval phase header
    apdu = list(INS_GET_PUBLIC_KEY) + [0x41]  # Build APDU to get public key with expected length 0x41 (65 bytes)
    pub_key_bytes, success = transmit_and_check(conn, apdu, "GET Public Key")  # Send command to retrieve public key from card
    if not success: return None  # Return None if public key retrieval failed
    try:  # Begin exception handling for public key parsing
        public_key = ECC.import_key(bytes(pub_key_bytes), curve_name='P-256')  # Parse raw bytes as ECC public key on P-256 curve
        print(" Public Key retrieved and parsed successfully.\n")  # Display success message
        return public_key  # Return the parsed ECC public key object
    except Exception as e:  # Catch any exception during key parsing
        print(f" Error parsing public key: {e}")  # Display the specific parsing error
        return None  # Return None to indicate parsing failure

def get_data_signature(conn):
    """Retrieves the signature of the electricity data from the card."""
    print("--- 2c. RETRIEVING SIGNATURE ---")  # Display signature retrieval phase header
    apdu = list(INS_GET_ELECTRICITY_DATA_SIGNATURE) + [0x48]  # Build APDU to get data signature with expected length 0x48 (72 bytes)
    signature, success = transmit_and_check(conn, apdu, "GET Electricity Data Signature")  # Send command to retrieve signature from card
    if not success: return None  # Return None if signature retrieval failed
    print(" Signature retrieved successfully.\n")  # Display success message
    return bytes(signature)  # Return the signature as bytes

def der_to_concat_rs(der_sig):
    """Converts a DER-encoded ECDSA signature to raw concatenated r||s format."""
    if der_sig[0] != 0x30: raise ValueError("Invalid DER encoding")  # Check if first byte is 0x30 (DER SEQUENCE tag)
    r_len = der_sig[3]  # Get the length of r component from byte 3
    r_start = 4  # r component starts at byte 4
    r = der_sig[r_start : r_start + r_len]  # Extract r component bytes
    s_len_pos = r_start + r_len + 1  # Calculate position of s length byte
    s_len = der_sig[s_len_pos]  # Get the length of s component
    s_start = s_len_pos + 1  # s component starts after its length byte
    s = der_sig[s_start : s_start + s_len]  # Extract s component bytes
    if r[0] == 0x00 and r_len == 33: r = r[1:]  # Remove leading zero padding if r is 33 bytes
    if s[0] == 0x00 and s_len == 33: s = s[1:]  # Remove leading zero padding if s is 33 bytes
    return r.rjust(32, b'\x00') + s.rjust(32, b'\x00')  # Pad both r and s to 32 bytes and concatenate

def retrieve_verify_and_decrypt_data(conn, key, public_key):
    """Retrieves encrypted data, verifies its signature, and then decrypts it."""
    print("--- 2. SECURE DATA RETRIEVAL & VERIFICATION ---")  # Display main data retrieval phase header
    print("--- 2b. RETRIEVING ENCRYPTED ELECTRICITY DATA ---")  # Display encrypted data retrieval sub-phase header
    encrypted_data = bytearray()  # Initialize empty bytearray to store all encrypted data chunks
    offset = 0  # Initialize offset counter for data retrieval
    chunk_size = 240  # Set chunk size to 240 bytes per APDU command
    while True:  # Loop to retrieve data in chunks until all data is retrieved
        p1 = offset >> 8  # Calculate P1 parameter (high byte of offset)
        p2 = offset & 0xFF  # Calculate P2 parameter (low byte of offset)
        apdu = list(INS_GET_ELECTRICITY_DATA) + [p1, p2, chunk_size]  # Build APDU with offset and chunk size
        resp, success = transmit_and_check(conn, apdu, f"GET Electricity Data (offset {offset})")  # Send data retrieval command
        if not success: return None  # Return None if data retrieval failed
        if not resp: break  # Break loop if no more data is available
        encrypted_data.extend(resp)  # Append received data chunk to the complete data
        offset += len(resp)  # Update offset by the length of received data
        if len(resp) < chunk_size: break  # Break loop if received chunk is smaller than requested (end of data)
    print(f" Full encrypted data retrieved ({len(encrypted_data)} bytes).\n")  # Display total data size retrieved
    
    signature = get_data_signature(conn)  # Retrieve the digital signature of the encrypted data
    if not signature:  # Check if signature retrieval failed
        print(" Failed to retrieve data signature. Aborting.")  # Display error message
        return None  # Return None to indicate failure
        
    print("--- 2d. VERIFYING DATA SIGNATURE ---")  # Display signature verification phase header
    try:  # Begin exception handling for signature verification
        verifier = DSS.new(public_key, 'fips-186-3')  # Create DSS verifier with the card's public key
        hash_obj = SHA256.new(encrypted_data)  # Create SHA-256 hash of the encrypted data
        verifier.verify(hash_obj, der_to_concat_rs(signature))  # Verify signature against the data hash
        print(" SIGNATURE VERIFIED: The data is authentic and has not been tampered with.\n")  # Display verification success
    except (ValueError, TypeError):  # Catch signature verification errors
        print(" VERIFICATION FAILED: The signature is invalid! Aborting.")  # Display verification failure message
        traceback.print_exc()  # Print full exception traceback for debugging
        return None  # Return None to indicate verification failure

    print("--- 2e. DECRYPTING CARD DATA ---")  # Display data decryption phase header
    cipher = AES.new(key, AES.MODE_ECB)  # Create AES cipher in ECB mode with the shared key
    try:  # Begin exception handling for decryption and parsing
        decrypted_data = cipher.decrypt(bytes(encrypted_data))  # Decrypt the encrypted data using AES
        
        # --- FIXED: Robust JSON parsing to handle padding ---
        # Find the last closing brace '}'
        last_brace_index = decrypted_data.rfind(b'}')  # Find the last occurrence of closing brace in decrypted data
        if last_brace_index == -1:  # Check if no closing brace was found
            print(" Error: Could not find valid JSON object in decrypted data.")  # Display JSON parsing error
            return None  # Return None to indicate parsing failure
        
        # Slice the string to include only the valid JSON part
        json_string = decrypted_data[:last_brace_index + 1].decode('utf-8')  # Extract valid JSON portion and decode to string
        
        print(" Data decrypted successfully.")  # Display decryption success message
        card_details = json.loads(json_string)  # Parse the JSON string into a Python dictionary
        
        print(" Plaintext data parsed as JSON.\n")  # Display JSON parsing success message
        print("   --- Decrypted Card Details ---")  # Display card details header
        for k, v in card_details.items():  # Loop through each key-value pair in card details
            print(f"   {k}: {v}")  # Display each key-value pair
        print("   ------------------------------\n")  # Display card details footer
        return card_details  # Return the parsed card details dictionary
    except Exception as e:  # Catch any exception during decryption or parsing
        print(f" An error occurred during decryption/parsing: {e}")  # Display the specific error
        return None  # Return None to indicate failure

# --- NEW FUNCTIONS FOR CHARGING ---
def load_user_database():
    """Loads the user accounts database from the JSON file."""
    try:  # Begin exception handling for file operations
        with open(USER_DB_FILE, 'r') as f:  # Open the user database file in read mode
            return json.load(f)  # Parse and return the JSON data from the file
    except FileNotFoundError:  # Catch error when database file doesn't exist
        print(f" Error: User DB file '{USER_DB_FILE}' not found.")  # Display file not found error
        return None  # Return None to indicate loading failure
    except json.JSONDecodeError:  # Catch error when file contains invalid JSON
        print(f" Error: '{USER_DB_FILE}' is not a valid JSON file.")  # Display JSON parsing error
        return None  # Return None to indicate loading failure

def save_user_database(database):
    """Saves the updated accounts database to the JSON file."""
    try:  # Begin exception handling for file writing operations
        with open(USER_DB_FILE, 'w') as f:  # Open the user database file in write mode
            json.dump(database, f, indent=2)  # Write the database dictionary to file with 2-space indentation
        print(f" Database file '{USER_DB_FILE}' saved successfully.")  # Display successful save message
    except IOError as e:  # Catch any input/output error during file writing
        print(f" Error saving user database file: {e}")  # Display the specific file writing error

def charge_meter(user_db, card_details):
    """Verifies user and meter, then charges the account."""
    print("--- 3. METER CHARGING ---")  # Display meter charging phase header
    card_sin = card_details.get("SIN")  # Extract SIN (Social Insurance Number) from card data
    card_meter_id = card_details.get("Meter ID")  # Extract Meter ID from card data

    if not card_sin or not card_meter_id:  # Check if both SIN and Meter ID are present
        print(" Error: SIN or Meter ID not found in card data.")  # Display missing data error
        return  # Exit function if required data is missing

    # Check if the SIN from the card exists in our database
    if card_sin not in user_db:  # Verify that the SIN exists in the user database
        print(f" VERIFICATION FAILED: SIN '{card_sin}' not found in the company database.")  # Display SIN verification failure
        return  # Exit function if SIN is not found

    # Check if the Meter ID from the card is the one authorized for this SIN
    user_record = user_db[card_sin]  # Get the user record from database using SIN as key
    if user_record.get("authorized_meter") != card_meter_id:  # Verify that the meter ID matches the authorized one
        print(" VERIFICATION FAILED: This card is not authorized for this meter.")  # Display meter authorization failure
        print(f"   Card Meter ID: {card_meter_id}")  # Display the meter ID from the card
        print(f"   Authorized ID: {user_record.get('authorized_meter')}")  # Display the authorized meter ID from database
        return  # Exit function if meter ID doesn't match
    
    # All checks passed, proceed with charging
    print(f" Welcome, {user_record.get('owner_name')}. Meter verified.")  # Display welcome message with user name
    print(f" Current Balance: {user_record.get('balance'):.2f} EGP")  # Display current account balance
    current_balance = user_record.get('balance', 0.0)  # Get current balance with default value of 0.0
    charge_amount = 100.00  # Set the charging amount to 100 EGP
    print(f" Charging account with {charge_amount:.2f} EGP...")  # Display the charging amount
    # --- FIXED: Added balance check before charging ---
    if current_balance < charge_amount:  # Check if current balance is sufficient for the charge
        print(f" TRANSACTION FAILED: Insufficient balance to charge {charge_amount:.2f} EGP.")  # Display insufficient balance error
        return  # Exit function if balance is insufficient
    print(f" Charging account with {charge_amount:.2f} EGP...")  # Display charging confirmation message
    user_record['balance'] -= charge_amount  # Deduct the charge amount from user's balance
    
    print(f" Charge successful! New Balance: {user_record.get('balance'):.2f} EGP")  # Display new balance after charging
    
    # Save the updated database
    save_user_database(user_db)  # Save the updated user database to file

def main():
    """Main function to run the entire electricity reader process."""
    try:  # Begin exception handling for the entire main process
        conn = connect_to_card()  # Establish connection to the smart card
        if not conn: return  # Exit if connection failed
        
        if run_authentication(conn, AES_KEY):  # Run mutual authentication with the card
            public_key = get_public_key(conn)  # Retrieve the card's public key for signature verification
            if not public_key:  # Check if public key retrieval failed
                print("Could not retrieve a valid public key from the card. Aborting.")  # Display public key error
                return  # Exit if public key retrieval failed

            card_details = retrieve_verify_and_decrypt_data(conn, AES_KEY, public_key)  # Get and verify card data
            
            if card_details:  # Check if card data was successfully retrieved and verified
                user_db = load_user_database()  # Load the user accounts database from file
                if user_db:  # Check if database was successfully loaded
                    charge_meter(user_db, card_details)  # Process the meter charging transaction
            else:  # If card data retrieval failed
                print("--- PROCESS FAILED ---")  # Display process failure header
                print("Failed to retrieve or verify data from the smart card.")  # Display specific failure message

    except Exception as e:  # Catch any unexpected exception during execution
        print(f"\n An unexpected error occurred: {e}")  # Display the unexpected error
        print("--- Full Traceback ---")  # Display traceback header
        traceback.print_exc()  # Print the full exception traceback for debugging
    finally:  # Always execute this block regardless of success or failure
        if conn:  # Check if connection object exists
            conn.disconnect()  # Disconnect from the smart card
        print("\nProcess finished.")  # Display process completion message

if __name__ == "__main__":  # Check if this script is being run directly (not imported)
    main()  # Call the main function to start the electricity reader process
