package com.Metwally.Banking;

import javacard.framework.*;

/**
 * Banking JavaCard Applet
 * Handles banking operations and transactions
 */
public class Banking extends Applet {
    
    // Class and instance variables
    private static final byte BANKING_CLA = (byte) 0x80;
    
    // Instruction codes
    private static final byte INS_CREATE_ACCOUNT = (byte) 0x10;
    private static final byte INS_DEPOSIT = (byte) 0x20;
    private static final byte INS_WITHDRAW = (byte) 0x30;
    private static final byte INS_GET_BALANCE = (byte) 0x40;
    private static final byte INS_TRANSFER = (byte) 0x50;
    private static final byte INS_VERIFY_PIN = (byte) 0x60;
    
    // Account status
    private static final byte STATUS_NOT_CREATED = 0x00;
    private static final byte STATUS_ACTIVE = 0x01;
    private static final byte STATUS_BLOCKED = 0x02;
    
    // Storage
    private byte accountStatus;
    private int balance;
    private byte[] pin;
    private byte[] accountNumber;
    private static final byte PIN_LENGTH = 4;
    private static final byte ACCOUNT_NUMBER_LENGTH = 8;
    private static final int MAX_BALANCE = 1000000;
    private byte pinRetries;
    private static final byte MAX_PIN_RETRIES = 3;
    
    /**
     * Constructor
     */
    private Banking() {
        accountStatus = STATUS_NOT_CREATED;
        balance = 0;
        pin = new byte[PIN_LENGTH];
        accountNumber = new byte[ACCOUNT_NUMBER_LENGTH];
        pinRetries = MAX_PIN_RETRIES;
    }
    
    /**
     * Installs this applet
     */
    public static void install(byte[] bArray, short bOffset, byte bLength) {
        new Banking().register(bArray, (short) (bOffset + 1), bArray[bOffset]);
    }
    
    /**
     * Processes an incoming APDU
     */
    public void process(APDU apdu) {
        if (selectingApplet()) {
            return;
        }
        
        byte[] buf = apdu.getBuffer();
        
        switch (buf[ISO7816.OFFSET_INS]) {
            case INS_CREATE_ACCOUNT:
                createAccount(apdu);
                break;
            case INS_DEPOSIT:
                deposit(apdu);
                break;
            case INS_WITHDRAW:
                withdraw(apdu);
                break;
            case INS_GET_BALANCE:
                getBalance(apdu);
                break;
            case INS_TRANSFER:
                transfer(apdu);
                break;
            case INS_VERIFY_PIN:
                verifyPIN(apdu);
                break;
            default:
                ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
        }
    }
    
    /**
     * Create a new bank account
     */
    private void createAccount(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != (PIN_LENGTH + ACCOUNT_NUMBER_LENGTH)) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        if (accountStatus != STATUS_NOT_CREATED) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        Util.arrayCopy(buf, ISO7816.OFFSET_CDATA, pin, (short) 0, PIN_LENGTH);
        Util.arrayCopy(buf, (short) (ISO7816.OFFSET_CDATA + PIN_LENGTH), accountNumber, (short) 0, ACCOUNT_NUMBER_LENGTH);
        
        accountStatus = STATUS_ACTIVE;
        balance = 0;
        pinRetries = MAX_PIN_RETRIES;
    }
    
    /**
     * Deposit money to account
     */
    private void deposit(APDU apdu) {
        if (accountStatus != STATUS_ACTIVE) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != 4) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        int amount = Util.getInt(buf, ISO7816.OFFSET_CDATA);
        
        if (amount <= 0 || (balance + amount) > MAX_BALANCE) {
            ISOException.throwIt(ISO7816.SW_DATA_INVALID);
        }
        
        balance += amount;
    }
    
    /**
     * Withdraw money from account
     */
    private void withdraw(APDU apdu) {
        if (accountStatus != STATUS_ACTIVE) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != 4) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        int amount = Util.getInt(buf, ISO7816.OFFSET_CDATA);
        
        if (amount <= 0 || balance < amount) {
            ISOException.throwIt(ISO7816.SW_DATA_INVALID);
        }
        
        balance -= amount;
    }
    
    /**
     * Get current balance
     */
    private void getBalance(APDU apdu) {
        if (accountStatus != STATUS_ACTIVE) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        byte[] buf = apdu.getBuffer();
        Util.setInt(buf, (short) 0, balance);
        apdu.setOutgoingAndSend((short) 0, (short) 4);
    }
    
    /**
     * Transfer money (placeholder)
     */
    private void transfer(APDU apdu) {
        if (accountStatus != STATUS_ACTIVE) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        // Transfer implementation would go here
        ISOException.throwIt(ISO7816.SW_FUNC_NOT_SUPPORTED);
    }
    
    /**
     * Verify PIN
     */
    private void verifyPIN(APDU apdu) {
        if (accountStatus == STATUS_NOT_CREATED) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        if (pinRetries == 0) {
            accountStatus = STATUS_BLOCKED;
            ISOException.throwIt(ISO7816.SW_SECURITY_STATUS_NOT_SATISFIED);
        }
        
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != PIN_LENGTH) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        if (Util.arrayCompare(buf, ISO7816.OFFSET_CDATA, pin, (short) 0, PIN_LENGTH) == 0) {
            pinRetries = MAX_PIN_RETRIES;
            buf[0] = (byte) 0x01; // PIN verified
        } else {
            pinRetries--;
            buf[0] = (byte) 0x00; // PIN incorrect
        }
        
        apdu.setOutgoingAndSend((short) 0, (short) 1);
    }
}
