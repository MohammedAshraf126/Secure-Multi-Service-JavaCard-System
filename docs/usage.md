#### `docs/usage.md`

```markdown
# Usage Guide

This document explains how to run the Python reader applications to interact with the JavaCard applets for each service.

## General Usage

1.  **Ensure your smart card reader is connected** and a JavaCard with all applets installed is inserted.
2.  **Activate your Python virtual environment** (if you created one during setup):
    * On Windows: `.venv\Scripts\activate`
    * On Linux/macOS: `source .venv/bin/activate`
3.  **Navigate to the `src/python-readers` directory**:
    ```bash
    cd Secure-Multi-Service-JavaCard-System/src/python-readers
    ```
4.  **Run the desired reader script.**

## Running Each Service Reader

Each reader script will attempt to:
1.  Connect to the smart card.
2.  Perform mutual authentication.
3.  Retrieve (and verify the signature of) sensitive data from the card.
4.  Interact with its corresponding local database.
5.  Present a menu of operations (e.g., check balance, purchase ticket, cast vote, charge meter).

### 1. Banking Service Reader

To interact with the Banking applet:

```bash
python bank_reader.py
