# Secure Multi-Service JavaCard System

This project demonstrates a secure multi-service smart card system implemented using JavaCard applets and Python-based readers. The system focuses on providing secure access to various services (Banking, Voting, Transport, Electricity) by employing mutual authentication and digital signatures to protect data integrity and authenticity.

## Project Overview

The core idea is to consolidate different user-specific data onto a single smart card, which can then interact securely with various service readers. Each service applet on the card and its corresponding reader application are designed to perform a robust mutual authentication process using AES encryption. Furthermore, sensitive data retrieved from the card is digitally signed using ECDSA to ensure its authenticity and integrity.

## setup and installation guide
This document provides comprehensive instructions on how to set up your development environment, compile the JavaCard applets, load them onto a smart card (or simulator), and run the Python reader applications.

Prerequisites
To successfully set up and run this project, you will need the following software components and tools:

1. Operating System
Microsoft Windows: Versions 10 or 11 are supported.

Linux: Ubuntu Linux 20.04 LTS or Oracle Linux 9 are supported. For Linux systems, you might need to configure them to run 32-bit applications (e.g., sudo apt-get install lib32z1 lib32ncurses5 lib32stdc++6).

2. Java Development Kit (JDK)
Oracle JDK 17 (64-bit version) or OpenJDK 17 (64-bit version) is required.

The JDK release can be downloaded from Oracle's official website or obtained via OpenJDK distributions.

3. Java Card Development Kit (JCDK)
The JCDK is a suite of components essential for Java Card applet development. It typically comes in three independent downloads:

Java Card Development Kit Tools: Contains tools for converting Java bytecode to CAP files and verifying Java Card applications.

Java Card Development Kit Simulator: Provides a runtime environment that simulates a Java Card 3.2 platform, supporting applications written for various Java Card releases. This is crucial for testing without physical hardware.

Java Card Development Kit Eclipse Plug-in (Recommended): Offers an integrated environment within Eclipse IDE for developing, testing, and debugging Java Card applications.

4. Eclipse IDE (Optional, but Recommended for Development)
The Java Card Eclipse Plug-in was tested with Eclipse 2023-03 (4.27) and requires JDK 17.

Eclipse can be downloaded from https://eclipse.org/downloads.

5. Smart Card Reader
A PC/SC compliant smart card reader (e.g., ACS ACR122U, SCM SCL011).

6. JavaCard
A blank or rewritable JavaCard for physical deployment, or you can solely rely on the JCDK Simulator.

7. Python 3
Python 3.8 or newer is required for the reader applications.

8. Python Libraries
pyscard: For PC/SC smart card communication from Python.

pycryptodome: For cryptographic operations (AES, ECC, SHA-256) on the reader side.

Install using pip: pip install pyscard pycryptodome

9. GlobalPlatformPro (GPPro)
A command-line tool for managing JavaCard applets (installing, deleting, selecting) on physical cards or simulators.

Download the latest release from its GitHub page: https://github.com/martinpaljak/GlobalPlatformPro/releases

Essential Configurations and Setup
1. Environment Variables
Set the following environment variables on your system:

JAVA_HOME: Must be set to the JDK software root directory (e.g., C:\Program Files\Java\jdk-17 or /usr/lib/jvm/java-17-openjdk). Ensure its bin folder is added to your system's PATH environment variable.

JC_HOME_SIMULATOR: Must be set to the root directory where the Java Card Development Kit Simulator is installed (e.g., C:\JavaCard\jc_sdk_simulator-3_2_0 or /opt/javacard/jc_sdk_simulator-3_2_0).

JC_HOME_TOOLS: Must be set to the root directory where the Java Card Development Kit Tools are installed (e.g., C:\JavaCard\jc_sdk_tools-3_2_0 or /opt/javacard/jc_sdk_tools-3_2_0).

LD_LIBRARY_PATH (Linux only): Needs to be set to ${JC_HOME_SIMULATOR}/runtime/bin for the Simulator to access the OpenSSL shared library. Add this to your shell profile (e.g., ~/.bashrc or ~/.zshrc):

export LD_LIBRARY_PATH=${JC_HOME_SIMULATOR}/runtime/bin:$LD_LIBRARY_PATH

Optionally, OPENSSL_MODULES can be set for legacy provider support if you encounter OpenSSL-related errors.

2. Simulator Provisioning (Configurator.jar)
Before using the Java Card Development Kit Simulator for the first time, it must be provisioned with an initial Secure Channel Protocol (SCP) key set and a Global PIN. This is critical for establishing secure communication with the card manager and performing applet management operations.

Purpose: The Configurator.jar tool injects the initial SCP03 key set and a Global PIN into the simulator's binary. These keys are used by the Issuer Security Domain (ISD), which is the default selected applet when the Simulator starts.

Location: The Configurator.jar file is located in the ${JC_HOME_SIMULATOR}/tools subdirectory.

Usage Example:

On Windows:

java -jar "%JC_HOME_SIMULATOR%\tools\Configurator.jar" -binary "%JC_HOME_SIMULATOR%\runtime\bin\jcsw.exe" -SCP-keyset 10 1111111111111111111111111111111111111111111111111111111111111111 2222222222222222222222222222222222222222222222222222222222222222 3333333333333333333333333333333333333333333333333333333333333333 -global-pin 01020304050f 03

On Linux/macOS:

java -jar "${JC_HOME_SIMULATOR}/tools/Configurator.jar" -binary "${JC_HOME_SIMULATOR}/runtime/bin/jcsl" -SCP-keyset 10 1111111111111111111111111111111111111111111111111111111111111111 2222222222222222222222222222222222222222222222222222222222222222 3333333333333333333333333333333333333333333333333333333333333333 -global-pin 01020304050f 03

Key Parameters:

-SCP-keyset <kvn> <k_enc> <k_mac> <k_dek>: Defines the Key Version Number (KVN) and the encryption, MAC, and decryption keys for the card manager. These are 32-byte (64-hex-character) values for 128-bit AES keys.

-global-pin <pin> <tries_count>: Sets the Global PIN for Cardholder Verification Method (CVM) and the number of tries.

Important: The SCP03 keys you provision using Configurator.jar must match the keys configured in the client.config.properties file (see next section) that your client applications (including GlobalPlatformPro) will use for applet management.

3. Client Configuration File (client.config.properties)
This file is crucial for client applications to communicate securely with the Java Card Simulator.

Location: Typically found at ${JC_HOME_SIMULATOR}/samples/client.config.properties.

Configuration: You need to configure this file with a valid Issuer Security Domain (ISD) entry and the SCP03 key set (encryption, MAC, and decryption keys) that were injected into the simulator binary using the Configurator.jar tool.

Ensure the SecureChannel.0.ENC, SecureChannel.0.MAC, and SecureChannel.0.DEK entries match the k_enc, k_mac, and k_dek values used in Configurator.jar.

4. Eclipse Plug-in Specific Configuration (if using Eclipse)
If you choose to use the Eclipse IDE for development:

Edit eclipse.ini: After installing the Eclipse Plug-in, you must edit the eclipse.ini file (located in your Eclipse installation folder) to add module paths for amservice.jar and socketprovider.jar. This ensures Eclipse can find the necessary Java Card SDK components.

Configure Preferences:

Ensure that Sample_Platform and Sample_Device are correctly configured in Eclipse preferences, pointing to your JC_HOME_SIMULATOR and using the client.config.properties file for device settings.

The Java Card Tools path within Eclipse preferences should be set to your JC_HOME_TOOLS directory.

It's also recommended to set JC_HOME_SIMULATOR as a classpath variable in Eclipse preferences to ensure all necessary libraries are found.

5. PCSC-Lite and IFD Handler (Optional for Linux Systems for PC/SC Communication)
If your client application uses PC/SC for communication with smart card terminals on Linux (e.g., for physical card readers, not just the simulator), you'll need to install and configure PCSC-Lite and the provided IFD Handler library (libjcsdkifdh.so).

Installation: Involves updating package databases and installing pcscd and pcsc-tools:

sudo apt update
sudo apt install pcscd pcsc-tools

Configuration: Configure the jcsdk_config file to define readers that connect to the simulator's IP sockets (if you're using a networked simulator setup). The pcscd daemon must be restarted after configuration (sudo systemctl restart pcscd).

GlobalPlatform Tools and Concepts
Your project, with its authentication process and data storage, heavily relies on the GlobalPlatform specification, which the Java Card SDK Simulator supports for application management.

GlobalPlatform (GP) Standard
GlobalPlatform is a key industry standard that defines the secure and interoperable management of applications on smart cards. The Java Card SDK Simulator explicitly supports GlobalPlatform specification version 2.3.1 for application management.

Role: GlobalPlatform defines the mechanisms for managing applications (applets) on the card, including loading CAP files, creating and deleting applet instances, and deleting packages. This is directly relevant to how your user data storage applets will be deployed and managed on the card.

Application Management:

Loading CAP Files: The process of transferring the compiled applet package (CAP file) onto the card's memory.

Installing Applet Instances: Creating an executable instance of an applet from a loaded package.

Deleting Applets/Packages: Removing applets or entire packages from the card.

Card Lifecycle States: The Simulator supports all card lifecycle states specified in the GlobalPlatform Card Specification. The Simulator typically starts in the OP_READY lifecycle state, and the Issuer Security Domain (ISD) is in the PERSONALIZED state after installation.

Privileges: The implementation supports various GlobalPlatform privileges, which define what actions an entity (like a Security Domain or an applet) is authorized to perform (e.g., Security Domain, DAP Verification, Delegated Management, Card Lock, Card Terminate).

Secure Channel Protocol (SCP03)
SCP03 is a vital protocol within GlobalPlatform for establishing secure communication between the off-card client (e.g., GlobalPlatformPro, your Python readers via a secure connection) and the card.

Purpose: SCP03 ensures the confidentiality, integrity, and authenticity of commands and responses exchanged between the client and the card manager. This prevents eavesdropping, tampering, and unauthorized commands.

Implementation: The Issuer Security Domain (ISD), which is the default selected applet after the Simulator starts, implements SCP03.

Key Role of Configurator.jar: As mentioned, Configurator.jar's primary function is to inject the initial SCP03 key set into the simulator's binary, making secure communication possible from the outset.

Key Lengths: SCP03 supports initial AES keys of 128, 192, or 256-bit length.

Supported APDU Commands (via GlobalPlatform)
The Security Domains (ISD and Supplementary Security Domains) in the Simulator support a range of APDU commands for application management, which are typically used by tools like GlobalPlatformPro:

DELETE: For deleting applet instances and packages.

GET DATA: To retrieve BER-TLV-coded objects like Issuer Identification Number (IIN) and Card Image Number (CIN).

GET STATUS: To retrieve status information for ISD, CAP files, packages, and applets.

INSTALL: For various steps of card content management, such as loading, installing, making selectable, personalization, extradition, and registry updates.

LOAD: To load CAP files (both compact and extended format) into the Simulator.

MANAGE CHANNEL: To open and close logical channels.

SELECT: For selecting an Applet or a Security Domain.

SET STATUS: To manage card and application lifecycle states.

PUT KEY: For key loading, including changing the default Secure Channel Key Set.

STORE DATA: To transfer data to an Applet or the ISD.

1. JavaCard Applet Setup 
1.1. Compile JavaCard Applets
Navigate to the src/javacard-applets directory in your project.

cd Secure-Multi-Service-JavaCard-System/src/javacard-applets

For each applet (Banking, Electricity, Transport, Myvoting1), you'll need to compile them into CAP files. A typical build.xml (Ant build file) or a simple script would automate this, but for manual compilation:

Example for Banking.java:

Create a temp directory for intermediate files:

mkdir temp

Compile Java source to class files (using JDK 17):

javac -source 1.2 -target 1.2 -classpath "%JCDK_HOME_TOOLS%\lib\api.jar" -d temp com/Metwally/Banking/Banking.java

(Replace %JCDK_HOME_TOOLS% with $JC_HOME_TOOLS for Linux/macOS)

Convert class files to CAP file:

java -jar "%JC_HOME_TOOLS%\lib\converter.jar" -outdir bin -classdir temp -aid A04540201303 -pkg com.Metwally.Banking A04540201303 -applet com.Metwally.Banking.Banking A04540201303

-outdir bin: Output CAP file to a bin directory (create if it doesn't exist).

-aid A04540201303: The Package AID (from Banking.java's register method).

-pkg com.Metwally.Banking A04540201303: Package name and its AID.

-applet com.Metwally.Banking.Banking A04540201303: Applet class name and its AID. Crucially, the applet AIDs in the commands MUST match the ones hardcoded in your Python reader scripts.

Repeat this process for all applets:

transport.java:

Package: com.Moh.transport

Package AID: AB0342E22002 (from transport_reader.py)

Applet Name: transport

Applet AID: AB0342E22002

Myvoting1.java:

Package: com.moh.voting

Package AID: AE3393EE0102 (from voting_reader.py)

Applet Name: Myvoting1

Applet AID: AE3393EE0102

Electricity.java:

Package: com.Metwally.Electricity

Package AID: A03276939403 (from Electricity_reader.py)

Applet Name: Electricity

Applet AID: A03276939403

You should now have .cap files in a bin directory (e.g., src/javacard-applets/bin/).

1.2. Load Applets onto Smart Card (or Simulator) using GlobalPlatformPro
Download and set up GlobalPlatformPro (GPPro). Ensure the gp.jar file is easily accessible.

Connect your smart card reader and insert your JavaCard, or ensure your JCDK Simulator is running.

Open your terminal and navigate to the directory where your .cap files are.

To install the Banking applet:

java -jar path/to/gp.jar --install bin/com.Metwally.Banking.cap

To install the Transport applet:

java -jar path/to/gp.jar --install bin/com.Moh.transport.cap

To install the Voting applet:

java -jar path/to/gp.jar --install bin/com.moh.voting.cap

To install the Electricity applet:

java -jar path/to/gp.jar --install bin/com.Metwally.Electricity.cap

Important: GPPro automatically detects the Package AID and Applet AID from the CAP file. Ensure the AIDs in your Java code and python-readers match what's used during installation. If you encounter errors, check GPPro's output for clues (e.g., SW_CONDITIONS_NOT_SATISFIED might mean your card is locked or needs to be formatted, or your SCP03 keys in client.config.properties are incorrect).

You can list installed applets using:

java -jar path/to/gp.jar --list

2. Python Reader Setup
2.1. Install Python and Libraries
Install Python 3 if you haven't already.

Create a virtual environment (recommended):

python3 -m venv .venv

Activate the virtual environment:

On Windows: .venv\Scripts\activate

On Linux/macOS: source .venv/bin/activate

Install necessary Python libraries:

pip install pyscard pycryptodome

2.2. Prepare Data Files
Ensure that the JSON database files are present in the data/ directory relative to where you run the Python scripts:

data/user_account.json

data/electricity_db.json

data/transport_db.json

data/DB_Voting.json

These files simulate the backend databases that the reader applications interact with.

Troubleshooting
NoCardException or No reader found: Ensure your smart card reader is properly connected and its drivers are installed. Try restarting your computer. If using the simulator, ensure it's running and accessible.

SW: 6A 82 (File Not Found / Applet Not Found): The applet AID specified in the Python script does not match an applet installed on the card. Double-check the APPLET_AID in the Python reader script and verify applet installation with gp.jar --list.

SW: 69 85 (Conditions of Use Not Satisfied): This often indicates a security state issue on the card (e.g., authentication not performed when required before an operation).

CryptoException on card: Check your key lengths, modes (ECB NOPAD requires 16-byte multiples), and initialization of cryptographic objects in your JavaCard code.

Python ValueError during decryption/parsing: This often happens if the decrypted data is not valid JSON. This could be due to incorrect encryption/decryption keys, wrong AES mode, or padding issues.

Signature Verification Failed: This is critical. Ensure:

The AES_KEY is identical on both the card and the reader.

The data being signed on the card is exactly the same as the data being hashed for verification on the reader.

The public key retrieved from the card is correct.

The der_to_concat_rs function correctly transforms the signature format.

The private key used for signing on the card is correctly paired with the public key used for verification.
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
Secure-Multi-Service-JavaCard-System/
├── src/
│   ├── javacard-applets/
│   │   ├── com/
│   │   │   ├── Moh/
│   │   │   │   ├── transport/
│   │   │   │   │   └── transport.java
│   │   │   └── voting/
│   │   │       └── Myvoting1.java
│   │   └── com/
│   │       └── Metwally/
│   │           ├── Banking/
│   │           │   └── Banking.java
│   │           └── Electricity/
│   │               └── Electricity.java
│   └── python-readers/
│       ├── bank_reader.py
│       ├── Electricity_reader.py
│       ├── transport_reader.py
│       └── voting_reader.py
├── data/
│   ├── user_account.json
│   ├── electricity_db.json
│   ├── transport_db.json
│   └── DB_Voting.json
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   └── usage.md
├── .gitignore
├── LICENSE
└── README.md
