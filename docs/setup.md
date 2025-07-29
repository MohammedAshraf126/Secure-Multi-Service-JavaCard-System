# Setup and Installation Guide

This document provides instructions on how to set up your environment to compile the JavaCard applets, load them onto a smart card, and run the Python reader applications.

## Prerequisites

* **Java Development Kit (JDK):** Version 8 or newer.
* **JavaCard Development Kit (JCDK):** Typically JCDK 3.0.5u3 or similar. You can usually download this from Oracle's website or find community-maintained versions.
* **GlobalPlatformPro (GPPro):** A command-line tool for managing JavaCard applets (installing, deleting, selecting). Download the latest release from its GitHub page: `https://github.com/martinpaljak/GlobalPlatformPro/releases`
* **Smart Card Reader:** A PC/SC compliant smart card reader (e.g., ACR122U, SCM SCL011).
* **JavaCard:** A blank or rewritable JavaCard.
* **Python 3:** Version 3.8 or newer.
* **Python Libraries:** `pyscard` and `pycryptodome`.

## 1. JavaCard Applet Setup

### 1.1. Install JCDK

1.  Download the JCDK from a reliable source.
2.  Unzip the JCDK to a directory (e.g., `C:\JCDK_PATH` on Windows or `/opt/JCDK_PATH` on Linux/macOS).
3.  Set the `JCDK_HOME` environment variable to point to this directory.

### 1.2. Compile JavaCard Applets

Navigate to the `src/javacard-applets` directory in your project.

```bash
cd Secure-Multi-Service-JavaCard-System/src/javacard-applets
