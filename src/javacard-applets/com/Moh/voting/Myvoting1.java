package com.Moh.voting;

import javacard.framework.*;

/**
 * Voting JavaCard Applet
 * Handles electronic voting functionality
 */
public class Myvoting1 extends Applet {
    
    // Class and instance variables
    private static final byte VOTING_CLA = (byte) 0x80;
    
    // Instruction codes
    private static final byte INS_REGISTER_VOTER = (byte) 0x10;
    private static final byte INS_CAST_VOTE = (byte) 0x20;
    private static final byte INS_GET_VOTE_STATUS = (byte) 0x30;
    private static final byte INS_VERIFY_VOTER = (byte) 0x40;
    
    // Voting status
    private static final byte STATUS_NOT_REGISTERED = 0x00;
    private static final byte STATUS_REGISTERED = 0x01;
    private static final byte STATUS_VOTED = 0x02;
    
    // Storage
    private byte voterStatus;
    private byte candidateVoted;
    private byte[] voterID;
    private static final byte VOTER_ID_LENGTH = 8;
    
    /**
     * Constructor
     */
    private Myvoting1() {
        voterStatus = STATUS_NOT_REGISTERED;
        candidateVoted = 0;
        voterID = new byte[VOTER_ID_LENGTH];
    }
    
    /**
     * Installs this applet
     */
    public static void install(byte[] bArray, short bOffset, byte bLength) {
        new Myvoting1().register(bArray, (short) (bOffset + 1), bArray[bOffset]);
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
            case INS_REGISTER_VOTER:
                registerVoter(apdu);
                break;
            case INS_CAST_VOTE:
                castVote(apdu);
                break;
            case INS_GET_VOTE_STATUS:
                getVoteStatus(apdu);
                break;
            case INS_VERIFY_VOTER:
                verifyVoter(apdu);
                break;
            default:
                ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
        }
    }
    
    /**
     * Register a voter
     */
    private void registerVoter(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != VOTER_ID_LENGTH) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        if (voterStatus != STATUS_NOT_REGISTERED) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        Util.arrayCopy(buf, ISO7816.OFFSET_CDATA, voterID, (short) 0, VOTER_ID_LENGTH);
        voterStatus = STATUS_REGISTERED;
    }
    
    /**
     * Cast a vote
     */
    private void castVote(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != 1) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        if (voterStatus != STATUS_REGISTERED) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        candidateVoted = buf[ISO7816.OFFSET_CDATA];
        voterStatus = STATUS_VOTED;
    }
    
    /**
     * Get voting status
     */
    private void getVoteStatus(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        buf[0] = voterStatus;
        buf[1] = candidateVoted;
        apdu.setOutgoingAndSend((short) 0, (short) 2);
    }
    
    /**
     * Verify voter identity
     */
    private void verifyVoter(APDU apdu) {
        byte[] buf = apdu.getBuffer();
        short lc = apdu.setIncomingAndReceive();
        
        if (lc != VOTER_ID_LENGTH) {
            ISOException.throwIt(ISO7816.SW_WRONG_LENGTH);
        }
        
        if (voterStatus == STATUS_NOT_REGISTERED) {
            ISOException.throwIt(ISO7816.SW_CONDITIONS_NOT_SATISFIED);
        }
        
        if (Util.arrayCompare(buf, ISO7816.OFFSET_CDATA, voterID, (short) 0, VOTER_ID_LENGTH) == 0) {
            buf[0] = (byte) 0x01; // Verified
        } else {
            buf[0] = (byte) 0x00; // Not verified
        }
        
        apdu.setOutgoingAndSend((short) 0, (short) 1);
    }
}
