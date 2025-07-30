
# JavaCard Project Setup Guide (Eclipse + Simulator + Python Readers)

This document provides a **step-by-step guide** on how to:

* Build your JavaCard project using **Eclipse**
* Deploy the applets to the **Java Card Development Kit Simulator**
* Interact with them using **Python reader applications**

> ✅ **Before we Begin:**
> Make sure you've completed all the prerequisites and environment variable configurations detailed in `docs/setup.md`.
> Specifically, ensure the following are correctly set up:

* `JDK`
* `JCDK`
* `GlobalPlatformPro`
* The JCDK Simulator is provisioned using `Configurator.jar`.

---

## 1. Building and Deploying JavaCard Applets (Eclipse + Simulator)

### 1.1 Create JavaCard Project in Eclipse

1. Open **Eclipse IDE**
2. Navigate to: `File > New > Java Card Project`
3. Follow the wizard:

   * Give the project a meaningful name (e.g., `SecureMultiServiceApplets`)
   * Select the correct Java Card platform (e.g., `Sample_Platform` pointing to your JCDK Simulator installation)

---

### 1.2 Import Your Java Code

1. In your newly created Eclipse JavaCard project, navigate to the `src` folder
2. Right-click `src > Import > General > File > New > Others`
3. Select **Java Card Project**


![Create Java Card Project](https://github.com/user-attachments/assets/e327dd4d-f7e8-469d-94ef-1fb501d1b3f3)

4. Fill in:

   * Project name
   * Applet name
   * Package name
   * Applet AID


![Applet Details](https://github.com/user-attachments/assets/4fe1553e-d0fd-429d-a66c-6abc7a25bd17)

5. Click **Next** then **Finish**


![Project Ready](https://github.com/user-attachments/assets/e1f22d13-e0ab-405d-817c-5e04b7f3d553)

6. Navigate to your source directory (e.g., `/home/kali/eclipse-workspace/Banking/src/com/Metwally/Banking/Banking.java`)
7. Paste your Java code and press `Ctrl + S` to save.


![CAP Compilation](https://github.com/user-attachments/assets/eb4bc1d6-c6da-4906-bca3-590ec666cd2f)

---

### 1.3 Convert Java Code to CAP Files

* Eclipse (with Java Card plugin) will automatically compile to `.cap` files.
* Output is located in the `cap/` or `bin/` directory of your Eclipse project.

If not generated:

* Right-click the project → `Build Project` or `Clean Project > Build Project`
* Confirm that `.cap` files like:

  * `Banking.cap`
  * `Electricity.cap`
  * `transport.cap`
  * `Myvoting1.cap`
    are generated.

---

### 1.4 Run the JCDK Simulator

1. Open a **new terminal**
2. Set the `LD_LIBRARY_PATH` (Linux only):

```bash
export LD_LIBRARY_PATH="/home/kali/Downloads/java_card_devkit_simulator-linux-bin-v24.1-b_289-06-OCT-2024/runtime/bin:$LD_LIBRARY_PATH"
```

3. Navigate to the simulator binary directory:

```bash
cd /home/kali/Downloads/java_card_devkit_simulator-linux-bin-v24.1-b_289-06-OCT-2024/runtime/bin
./jcsl -p=9020
```

* The `-p=9020` flag tells the simulator to listen on port 9020.


![Simulator Running](https://github.com/user-attachments/assets/214c1418-83df-4f6b-9979-4fb60a6d34cb)

---

### 1.5 Run the PC/SC Daemon

1. Open **another terminal**
2. Start the PC/SC daemon:

```bash
sudo pcscd -f -d -a
```

* `-f`: Foreground
* `-d`: Debug messages
* `-a`: Auto-start on card insert/removal


![PCSC Daemon Running](https://github.com/user-attachments/assets/1be9c8bc-e561-437d-b976-f2288bb9d6ca)

---

### 1.6 Install Applets using GlobalPlatformPro

1. Open **another terminal**
2. Navigate to the directory where `gp.jar` is located
3. **List existing applets**:

```bash
java -jar gp.jar \
  --list \
  --key-enc 1111111111111111111111111111111111111111111111111111111111111111 \
  --key-mac 2222222222222222222222222222222222222222222222222222222222222222 \
  --key-dek 3333333333333333333333333333333333333333333333333333333333333333
```


![List Applets](https://github.com/user-attachments/assets/86670632-1e82-4a5d-b955-d161a73c4faf)

---

### Install Each Applet

```bash
# Example: Banking Applet
java -jar gp.jar \
  --install path/to/your/Banking.cap \
  --key-enc 1111111111111111111111111111111111111111111111111111111111111111 \
  --key-mac 2222222222222222222222222222222222222222222222222222222222222222 \
  --key-dek 3333333333333333333333333333333333333333333333333333333333333333

# Repeat for each applet
java -jar gp.jar --install path/to/your/Electricity.cap ...
java -jar gp.jar --install path/to/your/transport.cap ...
java -jar gp.jar --install path/to/your/Myvoting1.cap ...
```


![Applets Installed](https://github.com/user-attachments/assets/6d08c08d-d1cd-40c6-a92d-5e5c867466c8)

---

## 2. Running Python Reader Applications

With the simulator and pcscd running and applets installed, you can now interact with them using Python scripts.

### Prerequisites

Activate your Python virtual environment:

```bash
# On Windows
.venv\Scripts\activate

# On Linux/macOS
source .venv/bin/activate
```

Navigate to the reader directory:

```bash
cd Secure-Multi-Service-JavaCard-System/src/python-readers
```

---

### 2.1 Voting Service Reader

```bash
python3 voting_reader.py
```

* Retrieves voter data
* Simulates voting interaction


![Voting Reader](https://github.com/user-attachments/assets/36d82f87-934e-488d-aea6-7e4adc541f79)

---

### 2.2 Banking Service Reader

```bash
python3 bank_reader.py
```

* Retrieves banking info
* Allows transfers, withdrawals, and balance checks


![Banking Reader](https://github.com/user-attachments/assets/08ed10fa-a61b-4f98-8758-fd2c294f8489)

---

### 2.3 Transport Service Reader

```bash
python3 transport_reader.py
```

* Simulates ticket purchase
* Retrieves transport data


![Transport Reader](https://github.com/user-attachments/assets/42186226-478a-49c8-bc9d-e65644c0a939)

---

### 2.4 Electricity Service Reader

```bash
python3 Electricity_reader.py
```

* Retrieves meter data
* Simulates charging


![Electricity Reader](https://github.com/user-attachments/assets/4f83b902-3528-4a57-8230-788ae657df9e)
