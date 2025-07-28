import sys  # System-specific parameters and functions for program termination
import json  # JSON encoder and decoder for handling JSON data
import time  # Time-related functions
import traceback  # Extract, format and print information about Python stack traces
from datetime import datetime  # Classes for working with dates and times
from smartcard.System import readers  # Smart card reader detection and management
from smartcard.util import toHexString, toBytes  # Utility functions for hex string conversion
from smartcard.Exceptions import NoCardException, CardConnectionException  # Smart card specific exceptions
# --- MODIFIED: Add imports for ECDSA signature verification ---
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256
# --- END MODIFIED ---

# --- DEPENDENCY NOTE ---
# This script requires 'pycryptodome'. Install with: pip install pycryptodome
from Crypto.Cipher import AES  # AES encryption/decryption functionality

# --- Configuration ---
APPLET_AID = toBytes("A0 45 40 20 13 03")  # Application Identifier for the smart card applet
# The shared AES key (must be a bytes object) - 16-byte key for encryption/decryption
AES_KEY = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'
# Static reader nonce (16 bytes) for mutual authentication - prevents replay attacks
STATIC_READER_NONCE = bytes.fromhex("51525354554142434415212223242526")
ACCOUNTS_DB_FILE = 'user_account.json'  # File path for the user accounts database

# --- APDU Instruction Constants (from MyVoting.java) ---
INS_SELECT_APPLET = toBytes("00 A4 04 00")  # APDU command to select the applet on the smart card
INS_GET_NONCE = toBytes("80 CA 00 00 05")  # Get card's challenge nonce for authentication
INS_MUTUAL_AUTH = toBytes("80 11 00 00")   # Send our challenge response for mutual authentication
INS_RESPOND_AUTH = toBytes("80 12 00 00 00")  # Get card's challenge response to verify authentication
INS_GET_BANK_DATA = toBytes("00 50")       # Get the encrypted banking data from the card
# --- MODIFIED: New APDU constants for signature ---
INS_GET_BANK_DATA_SIGNATURE = toBytes("00 51 00 00") # P1, P2 are 00
INS_GET_PUBLIC_KEY = toBytes("00 52 00 00")       # P1, P2 are 00
# --- END MODIFIED --

def connect_to_card():
    """Establishes a connection with the smart card."""
    try:
        reader = readers()[0]  # Get the first available smart card reader
        connection = reader.createConnection()  # Create a connection object for the reader
        connection.connect()  # Establish physical connection to the smart card
        print(f" Connected to: {reader}\n")  # Display successful connection message
        return connection  # Return the connection object for further use
    except (IndexError, NoCardException):  # Handle cases where no reader/card is found
        print(" Error: No card or reader found.")  # Display error message
        sys.exit(1)  # Exit the program with error code 1

def transmit_and_check(conn, apdu, description):
    """Transmits an APDU and checks for a success (90 00) status word."""
    print(f"▶ {description}: {toHexString(apdu)}")  # Display the APDU command being sent
    resp, sw1, sw2 = conn.transmit(apdu)  # Send APDU to card and get response data and status words
    print(f"   Response: {toHexString(resp)}, SW: {sw1:02X}{sw2:02X}")  # Display response and status
    if (sw1, sw2) != (0x90, 0x00):  # Check if status words indicate success (90 00)
        print(f" Operation failed for: {description}")  # Display failure message
        return None, False  # Return None and False to indicate failure
    return resp, True  # Return response data and True to indicate success

def run_authentication(conn, key):
    """Runs the full mutual authentication sequence from the banking reader."""
    print("--- 1. MUTUAL AUTHENTICATION ---")  # Display authentication section header
    
    # Step 1: Select Applet
    select_apdu = list(INS_SELECT_APPLET) + [len(APPLET_AID)] + list(APPLET_AID)  # Build SELECT command with AID
    _, success = transmit_and_check(conn, select_apdu, "SELECT Applet")  # Send SELECT command to card
    if not success: return False  # Return False if applet selection failed

    # Step 2: Get card's nonce (challenge)
    card_nonce_resp, success = transmit_and_check(conn, list(INS_GET_NONCE), "GET Card Nonce")  # Request card's nonce
    if not success: return False  # Return False if getting nonce failed
    
    # Step 3: Encrypt (card_nonce + reader_nonce) and send to card
    card_nonce = bytes(card_nonce_resp)  # Convert card nonce response to bytes
    reader_nonce = STATIC_READER_NONCE  # Use predefined reader nonce
    plaintext = card_nonce + reader_nonce  # Concatenate card and reader nonces

    cipher = AES.new(key, AES.MODE_ECB)  # Create AES cipher in ECB mode with shared key
    encrypted_data = cipher.encrypt(plaintext)  # Encrypt the concatenated nonces
    
    mutual_auth_apdu = list(INS_MUTUAL_AUTH) + [len(encrypted_data)] + list(encrypted_data)  # Build mutual auth command
    _, success = transmit_and_check(conn, mutual_auth_apdu, "SEND Mutual Auth Challenge")  # Send encrypted challenge
    if not success:  # Check if mutual authentication command failed
        print("   Authentication failed at step 3.")  # Display specific failure message
        return False  # Return False to indicate authentication failure
        
    # Step 4: Ask card to respond to our challenge
    respond_auth_resp, success = transmit_and_check(conn, list(INS_RESPOND_AUTH), "GET Respond Auth")  # Request card's response
    if not success:  # Check if getting response failed
        print("   Authentication failed at step 4.")  # Display specific failure message
        return False  # Return False to indicate authentication failure

    # Step 5: Verify card's response
    decrypted_response = cipher.decrypt(bytearray(respond_auth_resp))  # Decrypt card's response
    responded_reader_nonce = decrypted_response[:16]  # Extract first 16 bytes (reader nonce)
    responded_card_id = decrypted_response[16:32]  # Extract next 16 bytes (card ID)

    print("\n   --- Verifying Card's Response ---")  # Display verification section header
    # **FIXED**: The toHexString utility expects a list of integers, not a bytes object.
    # We convert the bytes objects to lists before printing.
    print(f"   Reader Nonce Sent:     {toHexString(list(reader_nonce))}")  # Display sent reader nonce
    print(f"   Reader Nonce Returned: {toHexString(list(responded_reader_nonce))}")  # Display returned reader nonce
    print(f"   Card ID Returned:        {toHexString(list(responded_card_id))}")  # Display card ID from response
    
    if responded_reader_nonce == reader_nonce:  # Compare sent and returned reader nonces
        print("     Reader nonce verified successfully.")  # Display success message
    else:  # If nonces don't match
        print("     Verification Failed: Reader nonce mismatch!")  # Display failure message
        return False  # Return False to indicate verification failure
        
    print(" Mutual Authentication successful!\n")  # Display overall success message
    return True  # Return True to indicate successful authentication

# --- MODIFIED: New functions to get public key and signature ---
def get_public_key(conn):
    """Retrieves the card's ECDSA public key."""
    print("--- 2a. RETRIEVING PUBLIC KEY ---")
    apdu = list(INS_GET_PUBLIC_KEY) + [0x41] # Le=0x41 (65 bytes for uncompressed P-256 key)
    pub_key_bytes, success = transmit_and_check(conn, apdu, "GET Public Key")
    if not success:
        return None
    
    # Import the key using pycryptodome. The first byte (0x04) indicates it's an uncompressed key.
    try:
        public_key = ECC.import_key(bytes(pub_key_bytes), curve_name='P-256')
        print(" Public Key retrieved and parsed successfully.\n")
        return public_key
    except Exception as e:
        print(f" Error parsing public key: {e}")
        return None

def get_data_signature(conn):
    """Retrieves the signature of the bank data from the card."""
    print("--- 2c. RETRIEVING SIGNATURE ---")
    # Le=0x48 (72 bytes is max for P-256 signature in DER format)
    apdu = list(INS_GET_BANK_DATA_SIGNATURE) + [0x48]
    signature, success = transmit_and_check(conn, apdu, "GET Bank Data Signature")
    if not success:
        return None
    print(" Signature retrieved successfully.\n")
    return bytes(signature)
# --- END MODIFIED ---

# --- FIXED: Moved this helper function to the top level ---
def der_to_concat_rs(der_sig):
    """
    Convert DER-encoded ECDSA signature to raw concatenated r||s format for pycryptodome DSS.
    """
    if der_sig[0] != 0x30:
        raise ValueError("Invalid DER encoding")

    # total_len = der_sig[1] # Not strictly needed for parsing r and s
    r_len = der_sig[3]
    r_start = 4
    r = der_sig[r_start : r_start + r_len]

    s_len_pos = r_start + r_len + 1
    s_len = der_sig[s_len_pos]
    s_start = s_len_pos + 1
    s = der_sig[s_start : s_start + s_len]
    
    # Handle case where r or s are negative (high bit set) and DER adds a leading 0x00
    if r[0] == 0x00 and r_len == 33:
        r = r[1:]
    if s[0] == 0x00 and s_len == 33:
        s = s[1:]

    # Pad with 0s if needed to make both r and s 32 bytes
    r = r.rjust(32, b'\x00')
    s = s.rjust(32, b'\x00')

    return r + s  # Concatenated raw format

def retrieve_verify_and_decrypt_data(conn, key, public_key):
    """
    Retrieves encrypted data, verifies its signature, and then decrypts it.
    """
    print("--- 2. SECURE DATA RETRIEVAL & VERIFICATION ---")
    
    # --- Step 2b: Retrieve the encrypted data (this part is from the old function) ---
    print("--- 2b. RETRIEVING ENCRYPTED DATA ---")
    encrypted_data = bytearray()
    offset = 0
    chunk_size = 240
    
    while True:
        p1 = offset >> 8
        p2 = offset & 0xFF
        apdu = list(INS_GET_BANK_DATA) + [p1, p2, chunk_size]
        resp, success = transmit_and_check(conn, apdu, f"GET Bank Data (offset {offset})")
        if not success: return None
        if not resp: break
        encrypted_data.extend(resp)
        offset += len(resp)
        if len(resp) < chunk_size: break
            
    print(f" Full encrypted data retrieved ({len(encrypted_data)} bytes).\n")
    
    # --- Step 2c: Get the signature for the data we just retrieved ---
    signature = get_data_signature(conn)
    if not signature:
        print(" Failed to retrieve data signature. Aborting.")
        return None
        
    # --- Step 2d: Verify the signature ---
    print("--- 2d. VERIFYING DATA SIGNATURE ---")
    try:
        verifier = DSS.new(public_key, 'fips-186-3')
        hash_obj = SHA256.new(encrypted_data)
        verifier.verify(hash_obj, der_to_concat_rs(signature))
        print(" SIGNATURE VERIFIED: The data is authentic and has not been tampered with.\n")
    except (ValueError, TypeError):
        print(" VERIFICATION FAILED: The signature is invalid! Aborting.")
        traceback.print_exc() # Print more details on verification failure
        return None

    # --- Step 2e: Decrypt the data (only if signature is valid) ---
    # --- FIXED: This block is now correctly indented ---
    print("--- 2e. DECRYPTING CARD DATA ---")
    cipher = AES.new(key, AES.MODE_ECB)
    try:
        decrypted_data = cipher.decrypt(bytes(encrypted_data))
        decrypted_data = decrypted_data.rstrip(b'\x00')
        print(" Data decrypted successfully.")
        decrypted_json_string = decrypted_data.decode('utf-8')
        card_details = json.loads(decrypted_json_string)
        
        print(" Plaintext data parsed as JSON.\n")
        print("   --- Decrypted Card Details ---")
        for k, v in card_details.items():
            print(f"   {k}: {v}")
        print("   ------------------------------\n")
        return card_details
    except Exception as e:
        print(f" An error occurred during decryption/parsing: {e}")
        return None

def load_accounts():
    """Loads the accounts database from the JSON file."""
    try:
        with open(ACCOUNTS_DB_FILE, 'r') as f:  # Open accounts database file in read mode
            return json.load(f)  # Parse and return JSON data from file
    except FileNotFoundError:  # Handle case where accounts file doesn't exist
        print(f" Error: Accounts DB file '{ACCOUNTS_DB_FILE}' not found.")  # Display file not found error
        sys.exit(1)  # Exit program with error code 1
    except json.JSONDecodeError:  # Handle case where file contains invalid JSON
        print(f" Error: '{ACCOUNTS_DB_FILE}' is not a valid JSON file.")  # Display JSON parsing error
        sys.exit(1)  # Exit program with error code 1

def save_accounts(accounts_data):
    """Saves the updated accounts database to the JSON file."""
    try:
        with open(ACCOUNTS_DB_FILE, 'w') as f:  # Open accounts database file in write mode
            json.dump(accounts_data, f, indent=4)  # Write accounts data to file with indentation
    except IOError as e:  # Handle any input/output errors during file writing
        print(f" Error saving accounts file: {e}")  # Display error message with details

def show_banking_menu(accounts, sin):
    """Displays the interactive banking menu and handles user actions."""
    print("--- 3. BANKING OPERATIONS ---")  # Display banking operations section header
    account = accounts[sin]  # Get the specific account using SIN as key
    
    while True:  # Infinite loop for menu interaction
        print("\nPlease choose an option:")  # Display menu prompt
        print(f"   1. Check Balance (Current: ${account['balance']:.2f})")  # Display balance check option
        print("   2. Transfer Funds")  # Display deposit option
        print("   3. Withdraw Funds")  # Display withdrawal option
        print("   4. View Transaction History")  # Display transaction history option
        print("   5. Exit")  # Display exit option
        
        choice = input("Enter your choice (1-5): ")  # Get user's menu choice
        
        if choice == '1':  # Handle balance check option
            print(f"\nYour current balance is: ${account['balance']:.2f}")  # Display current balance
        
        elif choice == '2':
            try:
                recipient_sin = input("Enter recipient's SIN: ")
                if recipient_sin == sin:
                    print("Error: Cannot transfer funds to your own account.")
                    continue
                if recipient_sin not in accounts:
                    print("Error: Recipient account not found.")
                    continue
                amount = float(input("Enter amount to transfer: "))
                if amount <= 0:
                    print("Transfer amount must be positive.")
                    continue
                if amount > account['balance']:
                    print("Insufficient funds for this transfer.")
                    continue

                account['balance'] -= amount
                accounts[recipient_sin]['balance'] += amount
                timestamp = datetime.now().isoformat()
                account['history'].append({"type": "transfer_out", "amount": amount, "to": recipient_sin, "timestamp": timestamp})
                accounts[recipient_sin]['history'].append({"type": "transfer_in", "amount": amount, "from": sin, "timestamp": timestamp})
                
                print(f"Transfer successful. New balance: ${account['balance']:.2f}")
                # --- FIXED: Save after the transaction ---
                save_accounts(accounts)

            except ValueError:
                print("Invalid amount. Please enter a number.")
            except Exception as e:
                print(f"An error occurred during transfer: {e}")

        elif choice == '3':  # Handle withdrawal option
            try:
                amount = float(input("Enter amount to withdraw: "))  # Get withdrawal amount from user
                if amount <= 0:  # Check if amount is positive
                    print("Withdrawal amount must be positive.")  # Display error for non-positive amount
                elif amount > account['balance']:  # Check if sufficient funds available
                    print("Insufficient funds.")  # Display insufficient funds error
                else:
                    account['balance'] -= amount  # Subtract withdrawal amount from balance
                    account['history'].append({"type": "withdrawal", "amount": amount, "timestamp": datetime.now().isoformat()})  # Add transaction to history
                    print(f"Withdrawal successful. New balance: ${account['balance']:.2f}")  # Display success message
            except ValueError:  # Handle invalid number input
                print("Invalid amount.")  # Display error message for invalid input
        
        elif choice == '4':  # Handle transaction history option
            print("\n--- Transaction History ---")  # Display transaction history header
            if not account['history']:  # Check if transaction history is empty
                print("No transactions found.")  # Display message for empty history
            else:
                for tx in account['history']:  # Iterate through transaction history
                    print(f"   {tx['timestamp']} - {tx['type'].capitalize()}: ${tx['amount']:.2f}")  # Display each transaction
            print("-------------------------")  # Display section footer

        elif choice == '5':  # Handle exit option
            save_accounts(accounts)  # Save current account data to file
            print("\nChanges saved. Thank you for using our service.")  # Display exit message
            break  # Exit the menu loop
        else:  # Handle invalid menu choice
            print("Invalid choice. Please try again.")  # Display error message for invalid choice

def main():
    """Main function to run the entire banking process."""
    try:
        conn = connect_to_card()
        if not conn: return
        
        # --- MODIFIED WORKFLOW ---
        if run_authentication(conn, AES_KEY):
            # Step 1: Get the card's public key for verification
            public_key = get_public_key(conn)
            if not public_key:
                print("Could not retrieve a valid public key from the card. Aborting.")
                return

            # Step 2: Retrieve, verify, and decrypt the data using the public key
            card_details = retrieve_verify_and_decrypt_data(conn, AES_KEY, public_key)
            
            # Step 3: Proceed with banking operations if successful
            if card_details:
                accounts = load_accounts()
                card_sin = card_details.get("SIN")
                if accounts and card_sin in accounts:
                    print(f" Card SIN verified. Welcome, {accounts[card_sin].get('account_holder', 'customer')}.")
                    show_banking_menu(accounts, card_sin)
                else:
                    print(f" Verification Failed: The SIN '{card_sin}' from the card is not found in the bank's database.")

    except Exception as e:
        print(f"\n An unexpected error occurred: {e}")
        print("--- Full Traceback ---")
        traceback.print_exc()
    finally:
        print("\nProcess finished.")


if __name__ == "__main__":
    main()
