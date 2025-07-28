package com.Moh.transport;

import javacard.framework.*;

/**
 * Transport JavaCard Applet
 * Handles public transportation services
 */
public class transport extends Applet {
    
    // Class and instance variables
    private static final byte TRANSPORT_CLA = (byte) 0x80;
    
    // Instruction codes
    private static final byte INS_ADD_BALANCE = (byte) 0x10;
    private static final byte INS_DEDUCT_FARE = (byte) 0x20;
    private static final byte INS_GET_BALANCE = (byte) 0x30;
    
    // Storage for balance
    private static final short MAX_BALANCE = 1000;
    private short balance;
    
    /**
     * Constructor
     */
    private transport() {
        balance = 0;
    }
    
    /**
     * Installs this applet
     */
    public static void install(byte[] bArray, short bOffset, byte bLength) {
        new transport().register(bArray, (short) (bOffset + 1), bArray[bOffset]);
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
            case INS_ADD_BALANCE:
                addBalance(apdu);
                break;
            case INS_DEDUCT_FARE:
                deductFare(apdu);
                break;
            case INS_GET_BALANCE:
                getBalance(apdu);
                break;
            default:
                ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
        }
    }
    
    /**
     * Add balance to the transport card
     */
    private void addBalance(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != 2) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        short amount = Util.getShort(buf, ISO7816.OFFSET_CDATA);
        
        if (amount <= 0 || (balance + amount) > MAX_BALANCE) {
            ISOException.throwIt(ISO7816.SW_DATA_INVALID);
        }
        
        balance += amount;
    }
    
    /**
     * Deduct fare from the transport card
     */
    private void deductFare(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != 2) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        short fare = Util.getShort(buf, ISO7816.OFFSET_CDATA);
        
        if (fare <= 0 || balance < fare) {
            ISOException.throwIt(ISO7816.SW_DATA_INVALID);
        }
        
        balance -= fare;
    }
    
    /**
     * Get current balance
     */
    private void getBalance(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        Util.setShort(buf, (short) 0, balance);
        apdu.setOutgoingAndSend((short) 0, (short) 2);
    }
}
