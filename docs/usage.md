This document provides a step-by-step guide on how to build your JavaCard project using Eclipse, deploy the applets to the Java Card Development Kit Simulator, and then interact with them using the Python reader applications.

Before you begin: Ensure you have completed all the prerequisites and environment variable configurations detailed in the docs/setup.md file. Specifically, ensure your JDK, JCDK, and GlobalPlatformPro paths are correctly set up, and that the JCDK Simulator has been provisioned using Configurator.jar.

1. Building and Deploying JavaCard Applets (using Eclipse & Simulator)
This section guides you through setting up your project in Eclipse, compiling your applets, and deploying them to the Java Card Simulator.

1.1. Create JavaCard Project in Eclipse
Open Eclipse IDE.

Go to File > New > Java Card Project.

Follow the wizard to create a new project. Give it a meaningful name (e.g., SecureMultiServiceApplets).

Ensure you select the correct Java Card platform (e.g., Sample_Platform pointing to your JCDK Simulator installation) during project creation or in project properties.

1.2. Import Your Java Code
In your newly created Eclipse JavaCard project, navigate to the src folder.

Right-click on the src folder and select Import > General > File >New > others

<img width="1918" height="793" alt="image" src="https://github.com/user-attachments/assets/e327dd4d-f7e8-469d-94ef-1fb501d1b3f3" />

select java card project

<img width="683" height="496" alt="image" src="https://github.com/user-attachments/assets/4fe1553e-d0fd-429d-a66c-6abc7a25bd17" />

now begin to fill the project details like project name applet name package name applet AID then click next then click finish.

<img width="1919" height="1010" alt="image" src="https://github.com/user-attachments/assets/e1f22d13-e0ab-405d-817c-5e04b7f3d553" />

now go to the src path where we will write our java code for example /home/kali/eclipse-workspace/Banking/src/com/Metwally/Banking/Banking.java
then put our bank code then ctrl+s eclipse will convert it to cap file

<img width="1911" height="745" alt="image" src="https://github.com/user-attachments/assets/eb4bc1d6-c6da-4906-bca3-590ec666cd2f" />

1.3. Convert Java Code to CAP Files
Eclipse, with the Java Card Development Kit Plug-in, automates the compilation to CAP files.

Eclipse should automatically build the project and generate the .cap files in a designated bin or cap folder within your Eclipse project directory (e.g., SecureMultiServiceApplets/cap/).

If not, right-click on your project and select Build Project or Clean Project then Build Project.

Verify that .cap files (e.g., Banking.cap, Electricity.cap, transport.cap, Myvoting1.cap) are generated.

1.4. Run the JCDK Simulator
The JCDK Simulator (jcsl for Linux, jcsw.exe for Windows) simulates a physical Java Card, allowing your readers to connect to it.

Open a new terminal session.

Export the LD_LIBRARY_PATH (Linux only):
This command ensures the simulator can find its necessary shared libraries. Adjust the path to your JC_HOME_SIMULATOR installation.

export LD_LIBRARY_PATH="/home/kali/Downloads/java_card_devkit_simulator-linux-bin-v24.1-b_289-06-OCT-2024/runtime/bin:$LD_LIBRARY_PATH"

Start the Simulator:
Navigate to the runtime/bin directory within your JCDK Simulator installation and run the simulator executable.

cd /home/kali/Downloads/java_card_devkit_simulator-linux-bin-v24.1-b_289-06-OCT-2024/runtime/bin
./jcsl -p=9020

The -p=9020 flag sets the port for the simulator to listen on for PC/SC connections. You should see output indicating the simulator is running and listening.

<img width="1912" height="790" alt="image" src="https://github.com/user-attachments/assets/214c1418-83df-4f6b-9979-4fb60a6d34cb" />
.

1.5. Run the PC/SC Daemon
For your Python readers to communicate with the Java Card Simulator (or a physical reader) via PC/SC, the pcscd daemon must be running.

Open another new terminal session.

Start pcscd in foreground debug mode:

sudo pcscd -f -d -a

-f: Run in foreground.

-d: Enable debug messages.

-a: Start automatically on card insertion/removal.

This command provides detailed output that can be helpful for troubleshooting connection issues.

<img width="1916" height="799" alt="image" src="https://github.com/user-attachments/assets/1be9c8bc-e561-437d-b976-f2288bb9d6ca" />
.

1.6. Install Applets using GlobalPlatformPro (GPPro)
Now that the simulator is running and pcscd is active, you can use GlobalPlatformPro to load and install your compiled CAP files onto the simulated card.

Open yet another new terminal session.

Navigate to the directory containing your gp.jar file (or ensure gp.jar is in your PATH).

List existing applets (optional, but good to check):
Before installing, you can verify the connection and current state of the simulator. Use the SCP03 keys that you provisioned with Configurator.jar.

java -jar gp.jar \
  --list \
  --key-enc 1111111111111111111111111111111111111111111111111111111111111111 \
  --key-mac 2222222222222222222222222222222222222222222222222222222222222222 \
  --key-dek 3333333333333333333333333333333333333333333333333333333333333333

This command lists applets on the connected card/simulator, using the specified SCP03 keys for secure communication.

<img width="1886" height="789" alt="image" src="https://github.com/user-attachments/assets/86670632-1e82-4a5d-b955-d161a73c4faf" />
.

Install each applet:
You will need to run the --install command for each of your applet CAP files. Replace path/to/your/applet.cap with the actual path to your generated CAP files (e.g., from your Eclipse project's cap/ or bin/ directory).

# Example for Banking applet
java -jar gp.jar \
  --install path/to/your/Banking.cap \
  --key-enc 1111111111111111111111111111111111111111111111111111111111111111 \
  --key-mac 2222222222222222222222222222222222222222222222222222222222222222 \
  --key-dek 3333333333333333333333333333333333333333333333333333333333333333

# Repeat for Electricity, Transport, and Myvoting1 applets,
# making sure to use their respective .cap file paths.
java -jar gp.jar --install path/to/your/Electricity.cap ...
java -jar gp.jar --install path/to/your/transport.cap ...
java -jar gp.jar --install path/to/your/Myvoting1.cap ...

Ensure the SCP03 keys --key-enc, --key-mac, --key-dek match the ones used during simulator provisioning.

<img width="1873" height="332" alt="image" src="https://github.com/user-attachments/assets/6d08c08d-d1cd-40c6-a92d-5e5c867466c8" />


2. Running Python Reader Applications
With the applets deployed on the simulator (or physical card) and pcscd running, you can now execute the Python reader applications to interact with your JavaCard system.

Open a new terminal session.

Activate your Python virtual environment (if you created one during setup):

On Windows: .venv\Scripts\activate

On Linux/macOS: source .venv/bin/activate

Navigate to the src/python-readers directory:

cd Secure-Multi-Service-JavaCard-System/src/python-readers

2.1. Voting Service Reader
This reader communicates with the Myvoting1 applet to retrieve voter data and simulate a voting process.

python3 voting_reader.py

Follow the prompts. This script will perform mutual authentication, retrieve signed voter data, and present a voting menu.

Screenshot Placeholder: Voting Reader in Action
Insert a screenshot here showing the terminal output of voting_reader.py demonstrating authentication and the voting menu/interaction.

2.2. Banking Service Reader
This reader interacts with the Banking applet to demonstrate banking operations like balance checks, transfers, and withdrawals.

python3 bank_reader.py

Follow the prompts. This script will perform mutual authentication, retrieve signed banking data, and present a banking menu.

Screenshot Placeholder: Banking Reader in Action
Insert a screenshot here showing the terminal output of bank_reader.py demonstrating authentication and the banking menu/interaction.

2.3. Transport Service Reader
This reader communicates with the transport applet to simulate ticket purchases.

python3 transport_reader.py

Follow the prompts. This script will perform mutual authentication, retrieve signed transport data, and guide you through a ticket purchase simulation.

Screenshot Placeholder: Transport Reader in Action
Insert a screenshot here showing the terminal output of transport_reader.py demonstrating authentication and the ticket purchase interaction.

2.4. Electricity Service Reader
This reader interacts with the Electricity applet to simulate charging an electricity meter.

python3 Electricity_reader.py

Follow the prompts. This script will perform mutual authentication, retrieve signed electricity meter data, and simulate the charging process.

Screenshot Placeholder: Electricity Reader in Action
Insert a screenshot here showing the terminal output of Electricity_reader.py demonstrating authentication and the meter charging interaction.
