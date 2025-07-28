import sys
import json
import traceback
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException

# --- Cryptography Imports (from pycryptodome) ---
from Crypto.Cipher import AES
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

# --- Configuration ---
# AID for the Voting Applet on the smart card
APPLET_AID = toBytes("AE 33 93 EE 01 02")
# Shared AES key for mutual authentication and decryption
AES_KEY = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'
# Static reader nonce (16 bytes) for mutual authentication
STATIC_READER_NONCE = bytes.fromhex("51525354554142434415212223242526")
# Path to the simulated Voting Database
VOTING_DB_FILE = 'DB_Voting.json'

# --- APDU Instruction Constants ---
INS_SELECT_APPLET = toBytes("00 A4 04 00")
INS_GET_NONCE = toBytes("80 CA 00 00 05")
INS_MUTUAL_AUTH = toBytes("80 11 00 00")
INS_RESPOND_AUTH = toBytes("80 12 00 00 00")
# --- APDUs for Secure Data Retrieval ---
INS_GET_VOTER_DATA = toBytes("80 13 00 00 00") # Original command to get voter data
INS_GET_PUBLIC_KEY = toBytes("00 52 00 00")    # Command to get the card's public key
INS_GET_DATA_SIGNATURE = toBytes("00 51") # Command to get the signature of the data (P1 selects type)

def connect_to_card():
    """Establishes a connection with the first available smart card."""
    try:
        reader = readers()[0]
        connection = reader.createConnection()
        connection.connect()
        print(f"Connected to: {reader}\n")
        return connection
    except (IndexError, NoCardException):
        print("Error: No card or reader found.")
        sys.exit(1)

def transmit_and_check(conn, apdu, description):
    """Transmits an APDU and checks for a success (90 00) status word."""
    print(f"▶ {description}: {toHexString(apdu)}")
    try:
        resp, sw1, sw2 = conn.transmit(apdu)
        print(f"  Response: {toHexString(resp)}, SW: {sw1:02X}{sw2:02X}")
        if (sw1, sw2) != (0x90, 0x00):
            print(f"Operation failed for: {description}")
            return None, False
        return resp, True
    except Exception as e:
        print(f"Error transmitting APDU for '{description}': {e}")
        return None, False

def run_authentication(conn, key):
    """Runs the full mutual authentication sequence."""
    print("--- 1. MUTUAL AUTHENTICATION ---")

    # Step 1: Select Applet
    select_apdu = list(INS_SELECT_APPLET) + [len(APPLET_AID)] + list(APPLET_AID)
    _, success = transmit_and_check(conn, select_apdu, "SELECT Applet")
    if not success: return False

    # Step 2: Get card's nonce (challenge)
    card_nonce_resp, success = transmit_and_check(conn, list(INS_GET_NONCE), "GET Card Nonce")
    if not success: return False

    # Step 3: Encrypt (card_nonce + reader_nonce) and send to card
    card_nonce = bytes(card_nonce_resp)
    reader_nonce = STATIC_READER_NONCE
    plaintext = card_nonce + reader_nonce

    cipher = AES.new(key, AES.MODE_ECB)
    encrypted_data = cipher.encrypt(plaintext)

    mutual_auth_apdu = list(INS_MUTUAL_AUTH) + [len(encrypted_data)] + list(encrypted_data)
    _, success = transmit_and_check(conn, mutual_auth_apdu, "SEND Mutual Auth Challenge")
    if not success:
        print("  Authentication failed at step 3.")
        return False

    # Step 4: Ask card to respond to our challenge
    respond_auth_resp, success = transmit_and_check(conn, list(INS_RESPOND_AUTH), "GET Respond Auth")
    if not success:
        print("  Authentication failed at step 4.")
        return False

    # Step 5: Verify card's response
    decrypted_response = cipher.decrypt(bytearray(respond_auth_resp))
    responded_reader_nonce = decrypted_response[:16]

    if responded_reader_nonce == reader_nonce:
        print("  Reader nonce verified successfully.")
        print("Mutual Authentication successful!\n")
        return True
    else:
        print("  Verification Failed: Reader nonce mismatch!")
        return False

def get_public_key(conn):
    """Retrieves and parses the card's ECDSA public key."""
    print("--- 2a. RETRIEVING PUBLIC KEY ---")
    apdu = list(INS_GET_PUBLIC_KEY) + [0x41] # Le=0x41 (65 bytes for uncompressed P-256 key)
    pub_key_bytes, success = transmit_and_check(conn, apdu, "GET Public Key")
    if not success:
        return None

    try:
        public_key = ECC.import_key(bytes(pub_key_bytes), curve_name='P-256')
        print("Public Key retrieved and parsed successfully.\n")
        return public_key
    except Exception as e:
        print(f"Error parsing public key: {e}")
        return None

def get_data_signature(conn):
    """Retrieves the signature of the voter data from the card."""
    print("--- 2c. RETRIEVING SIGNATURE ---")
    # APDU: CLA=00, INS=51, P1=01 (Voter Data), P2=00, Le=48
    p1_voter_data = 0x01
    p2 = 0x00
    le_max_signature = 0x48
    apdu = list(INS_GET_DATA_SIGNATURE) + [p1_voter_data, p2, le_max_signature]
    
    signature, success = transmit_and_check(conn, apdu, "GET Voter Data Signature")
    if not success:
        return None
    print("Signature retrieved successfully.\n")
    return bytes(signature)

def der_to_concat_rs(der_sig):
    """Converts a DER-encoded ECDSA signature to raw concatenated r||s format."""
    if der_sig[0] != 0x30: raise ValueError("Invalid DER encoding")
    r_len = der_sig[3]
    r = der_sig[4 : 4 + r_len]
    s_len = der_sig[4 + r_len + 1]
    s = der_sig[4 + r_len + 2 : 4 + r_len + 2 + s_len]
    if r[0] == 0x00 and r_len == 33: r = r[1:]
    if s[0] == 0x00 and s_len == 33: s = s[1:]
    return r.rjust(32, b'\x00') + s.rjust(32, b'\x00')

def retrieve_verify_and_decrypt_data(conn, key, public_key):
    """Retrieves encrypted voter data, verifies its signature, and then decrypts it."""
    print("--- 2. SECURE VOTER DATA RETRIEVAL ---")

    # Step 2b: Retrieve the encrypted voter data
    print("--- 2b. RETRIEVING ENCRYPTED VOTER DATA ---")
    encrypted_data, success = transmit_and_check(conn, list(INS_GET_VOTER_DATA), "GET Voter Data")
    if not success: return None

    # Step 2c: Get the signature for the data
    signature = get_data_signature(conn)
    if not signature:
        print("Failed to retrieve data signature. Aborting.")
        return None

    # Step 2d: Verify the signature
    print("--- 2d. VERIFYING DATA SIGNATURE ---")
    try:
        verifier = DSS.new(public_key, 'fips-186-3')
        hash_obj = SHA256.new(bytes(encrypted_data))
        verifier.verify(hash_obj, der_to_concat_rs(signature))
        print("SIGNATURE VERIFIED: Voter data is authentic.\n")
    except (ValueError, TypeError):
        print("VERIFICATION FAILED: The signature is invalid! Data may be compromised. Aborting.")
        return None

    # Step 2e: Decrypt the data (only if signature is valid)
    print("--- 2e. DECRYPTING VOTER DATA ---")
    cipher = AES.new(key, AES.MODE_ECB)
    try:
        decrypted_data = cipher.decrypt(bytes(encrypted_data))
        decrypted_data = decrypted_data.rstrip(b'\x00').rstrip() # Remove padding and trailing whitespace

        # Find the last brace to correctly parse the JSON object
        last_brace_index = decrypted_data.rfind(b'}')
        if last_brace_index == -1:
            print("Error: Could not find JSON object in decrypted data.")
            return None

        json_string = decrypted_data[:last_brace_index + 1].decode('utf-8')
        voter_details = json.loads(json_string)

        print("Data decrypted and parsed successfully.\n")
        return voter_details
    except Exception as e:
        print(f"An error occurred during decryption/parsing: {e}")
        return None

def load_database():
    """Loads the voting database from the JSON file."""
    try:
        with open(VOTING_DB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Voting DB file '{VOTING_DB_FILE}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: '{VOTING_DB_FILE}' is not a valid JSON file.")
        sys.exit(1)

# --- MODIFIED: This function now uses your requested hardcoded logic ---
def show_voting_menu(database, voter_id):
    """Displays the voting menu and handles user actions."""
    print("--- 3. VOTING OPERATIONS ---")
    
    # This hardcoded_id is used for all checks, ignoring the voter_id from the card.
    hardcoded_id = '789568'

    # First, check if the hardcoded ID exists in the database.
    if hardcoded_id not in database:
        print(f"Verification Failed: Hardcoded Voter ID '{hardcoded_id}' not found in the database.")
        return

    # Use the hardcoded ID for all lookups as requested.
    print(f"Welcome, {database[hardcoded_id]['Name']}")

    if database[hardcoded_id]['Registration Status'] == True:
        print("Your Card is Active")
        if database[hardcoded_id]['Eligibility flag'] == True:
            print("You Are Eligible To Vote in This Election")
            
            # Display candidate menu only if eligible
            candidate_prompt = (
                "\nPlease type the number of the candidate you want to vote for:\n"
                "1- Abdel Fattah El-Sisi\n"
                "2- Ahmed Tantawi\n"
                "3- Ahmed Shafik\n"
                "Your choice: "
            )
            choice = input(candidate_prompt)
            try:
                candidate_num = int(choice)
                if candidate_num in [1, 2, 3]:
                    # In a real system, this vote would be securely transmitted.
                    print("Thank you, your vote has been recorded.")
                else:
                    print("Invalid choice. Please select a number from 1 to 3.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        else:
            print("You are not eligible to vote in this election.")
    else:
        print("Your Card is not Active. Please contact election officials.")


def main():
    """Main function to run the entire secure voting process."""
    conn = None
    try:
        conn = connect_to_card()
        
        if run_authentication(conn, AES_KEY):
            public_key = get_public_key(conn)
            if not public_key:
                print("Could not retrieve a valid public key from the card. Aborting.")
                return

            voter_details = retrieve_verify_and_decrypt_data(conn, AES_KEY, public_key)
            
            if voter_details:
                database = load_database()
                # The voter_id from the card is retrieved but will be ignored by show_voting_menu
                voter_id = voter_details.get("VoterID")
                if voter_id:
                    show_voting_menu(database, voter_id)
                else:
                    print("Could not find 'VoterID' in the data from the card.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("--- Full Traceback ---")
        traceback.print_exc()
    finally:
        if conn:
            conn.disconnect()
        print("\nProcess finished.")

if __name__ == "__main__":
    main()
