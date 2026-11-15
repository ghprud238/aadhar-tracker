import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
  Modal,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { api } from '../services/api';
import {
  generateCertifiedIdentityPass,
  verifyCertifiedIdentityPass,
  CertifiedIdentityPass,
  PassRequest,
} from '../services/passGenerator';
import {
  generateCybercrimeComplaint,
  CybercrimeComplaintDossier,
  CybercrimeComplaintRequest,
} from '../services/cybercrimeToolkit';
import { antiTamperShield } from '../services/antiTamperShield';
import { TelecomCreditShieldService, SimConnectionInfo, CreditInquiryAlert } from '../services/telecomCreditShield';
import { ForensicEvidenceCertificate, EvidenceItem } from '../services/evidenceDossier';

export const AadhaarPanScreen: React.FC = () => {
  const [lockedConfirmed, setLockedConfirmed] = useState(false);
  const [submittingLock, setSubmittingLock] = useState(false);

  // Virtual ID (VID) State
  const [vidData, setVidData] = useState<{ vid: string; formatted: string; validUntil: string } | null>(null);
  const [generatingVid, setGeneratingVid] = useState(false);

  // Pass Generator Modal State
  const [passModalVisible, setPassModalVisible] = useState(false);
  const [passRecipient, setPassRecipient] = useState('Taj Lands End, Mumbai');
  const [passPurpose, setPassPurpose] = useState<PassRequest['purpose']>('hotel_checkin');
  const [passCustomPurpose, setPassCustomPurpose] = useState('');
  const [passDocType, setPassDocType] = useState<PassRequest['documentType']>('aadhaar');
  const [generatedPass, setGeneratedPass] = useState<CertifiedIdentityPass | null>(null);

  // Cybercrime 1930 / FIR Drafter State
  const [firModalVisible, setFirModalVisible] = useState(false);
  const [victimName, setVictimName] = useState('Aarav Sharma');
  const [victimPhone, setVictimPhone] = useState('9876543210');
  const [victimEmail, setVictimEmail] = useState('resident@example.in');
  const [incidentType, setIncidentType] = useState<CybercrimeComplaintRequest['incidentType']>('aeps_biometric_fraud');
  const [lossAmount, setLossAmount] = useState('10000');
  const [suspectNotes, setSuspectNotes] = useState('AePS micro-ATM withdrawal triggered at unknown CSP outlet.');
  const [generatedFIR, setGeneratedFIR] = useState<CybercrimeComplaintDossier | null>(null);

  // Telecom SIM (TAFCOP) & Credit Radar States
  const [simModalVisible, setSimModalVisible] = useState(false);
  const [simConnections, setSimConnections] = useState<SimConnectionInfo[]>([]);
  const [creditModalVisible, setCreditModalVisible] = useState(false);
  const [creditInquiries, setCreditInquiries] = useState<CreditInquiryAlert[]>([]);

  // Section 63 BSA Forensic Evidence Package State
  const [evidenceModalVisible, setEvidenceModalVisible] = useState(false);
  const [generatedEvidence, setGeneratedEvidence] = useState<ForensicEvidenceCertificate | null>(null);

  useEffect(() => {
    handleGenerateVid(true);
    setSimConnections(api.getSimConnections());
    setCreditInquiries(api.getCreditInquiries());
  }, []);

  const handleGenerateVid = async (isInitial = false) => {
    setGeneratingVid(true);
    try {
      const data = await api.generateVirtualId();
      setVidData(data);
      if (!isInitial) {
        Alert.alert(
          '16-Digit Virtual ID Rotated',
          `New disposable VID generated:\n${data.formatted}\n\nValid for 24 hours. Your raw Aadhaar number is never shared.`
        );
      }
    } catch (err: any) {
      if (!isInitial) Alert.alert('VID Error', err.message);
    } finally {
      setGeneratingVid(false);
    }
  };

  const handleOpenUIDAI = () => {
    Linking.openURL('https://myaadhaar.uidai.gov.in/').catch(() => {
      Alert.alert('Cannot Open URL', 'Please visit myaadhaar.uidai.gov.in in your browser.');
    });
  };

  const handleOpenITD = () => {
    Linking.openURL('https://eportal.incometax.gov.in/iec/foservices/#/pre-login/link-aadhaar-status').catch(() => {
      Alert.alert('Cannot Open URL', 'Please visit eportal.incometax.gov.in in your browser.');
    });
  };

  const handleDial1930 = () => {
    Linking.openURL('tel:1930').catch(() => {
      Alert.alert('Emergency Helpline', 'Please dial 1930 on your phone dialer for the National Cyber Crime Helpline.');
    });
  };

  const handleOpenCybercrimeGov = () => {
    Linking.openURL('https://cybercrime.gov.in/').catch(() => {
      Alert.alert('Cannot Open URL', 'Please visit cybercrime.gov.in in your browser.');
    });
  };

  const copyToClipboard = (text: string, title = 'Credential') => {
    antiTamperShield.safeCopyToClipboard(text, title);
  };

  const handleVerifyPass = () => {
    if (!generatedPass) return;
    const res = verifyCertifiedIdentityPass(generatedPass);
    if (res.verified) {
      Alert.alert(
        '✓ Cryptographic Signature Valid',
        `Ed25519 asymmetric signature verified offline!\n\nSigner Public Key:\n${generatedPass.signerPublicKey.slice(0, 32)}...\n\nSignature:\n${generatedPass.signatureHex.slice(0, 32)}...\n\nValid Until: ${generatedPass.validUntil}\n\nTamper Check: PASS (Zero-Knowledge Offline Signature)`
      );
    } else {
      Alert.alert('Verification Failed', res.error || 'Signature mismatch or pass expired.');
    }
  };

  const handleConfirmLock = async () => {
    setSubmittingLock(true);
    try {
      await api.confirmAadhaarLock(
        'lock_biometrics',
        'Resident confirmed biometrics locked via official UIDAI portal/mAadhaar'
      );
      setLockedConfirmed(true);
      Alert.alert(
        'Protection Recorded',
        'Your confirmation has been logged to your immutable audit trail and synced to your companion shield status.'
      );
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setSubmittingLock(false);
    }
  };

  const handleCreatePass = () => {
    if (!passRecipient.trim()) {
      return Alert.alert('Recipient Entity Required', 'Please enter hotel, kiosk, or agency name.');
    }
    const masked = passDocType === 'aadhaar' ? 'XXXX-XXXX-4819' : (passDocType === 'pan' ? 'ABC**4819F' : 'MH12****4819');
    const pass = generateCertifiedIdentityPass({
      documentType: passDocType,
      holderName: 'Aarav Sharma',
      maskedIdentifier: masked,
      recipientEntity: passRecipient.trim(),
      purpose: passPurpose,
      customPurpose: passCustomPurpose,
    });
    setGeneratedPass(pass);
  };

  const handleGenerateFIR = () => {
    const dossier = generateCybercrimeComplaint({
      victimName: victimName.trim() || 'Aarav Sharma',
      victimPhone: victimPhone.trim() || '9876543210',
      victimEmail: victimEmail.trim() || 'resident@example.in',
      maskedIdentifier: 'XXXX-XXXX-4819',
      incidentType,
      approximateDate: new Date().toLocaleDateString('en-IN'),
      financialLossInr: parseFloat(lossAmount) || 0,
      suspectDetails: suspectNotes.trim(),
    });
    setGeneratedFIR(dossier);
  };

  const handleOpenTAFCOP = () => {
    Linking.openURL(TelecomCreditShieldService.TAFCOP_PORTAL_URL).catch(() => {
      Alert.alert('Cannot Open URL', 'Please visit tafcop.sancharsaathi.gov.in in your browser.');
    });
  };

  const handleOpenCEIR = () => {
    Linking.openURL(TelecomCreditShieldService.CEIR_PORTAL_URL).catch(() => {
      Alert.alert('Cannot Open URL', 'Please visit ceir.gov.in in your browser.');
    });
  };

  const handleOpenRBI = () => {
    Linking.openURL(TelecomCreditShieldService.RBI_OMBUDSMAN_URL).catch(() => {
      Alert.alert('Cannot Open URL', 'Please visit cms.rbi.org.in in your browser.');
    });
  };

  const handleCopyDisputeLetter = (inquiry: CreditInquiryAlert) => {
    const letter = api.generateLoanDisputeLetter(inquiry, 'Aarav Sharma', 'ABC**4819F');
    copyToClipboard(letter, 'Dispute Letter Copied');
    Alert.alert(
      'RBI Dispute Letter Ready',
      'The formal complaint letter to the lender and Banking Ombudsman has been copied to your clipboard.'
    );
  };

  const handleGenerateEvidence = () => {
    const mockEvidenceItems: EvidenceItem[] = [
      {
        type: 'sms_otp',
        description: 'AePS Transaction OTP received from VM-AADHAR',
        sourceReference: 'SMS Header: VM-AADHAR-0192',
        sha256Digest: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        capturedAt: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        type: 'bank_utr',
        description: 'Unauthorized Micro-ATM CSP Debit IMPS/AePS',
        sourceReference: 'Bank UTR: SBIN202611029841',
        sha256Digest: 'a89c02e5b7b1d3f9821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f',
        capturedAt: new Date(Date.now() - 1800000).toISOString(),
      },
      {
        type: 'screenshot',
        description: 'Aadhaar Biometric lock status screen capture',
        sourceReference: 'IMG_SURAKSHA_20261115_001.png',
        sha256Digest: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
        capturedAt: new Date().toISOString(),
      },
    ];

    const cert = api.generateSection63Certificate('Aarav Sharma', mockEvidenceItems, 'iPhone 15 Pro / iOS 18.2');
    setGeneratedEvidence(cert);
    setEvidenceModalVisible(true);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Aadhaar & Citizen Defense</Text>
        <Text style={styles.subtitle}>
          Purpose watermarks • 1930 Cybercrime FIR • Disposable 16-digit VID
        </Text>
      </View>

      {/* Zero Scraping & DPDP Guarantee Pill */}
      <View style={styles.bannerGuar}>
        <Text style={styles.bannerGuarIcon}>🛡️</Text>
        <Text style={styles.bannerGuarText}>
          Suraksha operates strictly as a zero-cloud privacy companion. We never query UIDAI servers or store
          raw Aadhaar numbers. All watermarks and FIR drafts are compiled 100% on your device.
        </Text>
      </View>

      {/* Feature 1: Single-Use Watermarked Masked Pass */}
      <View style={[styles.card, { borderColor: '#3b82f6' }]}>
        <View style={styles.cardHeader}>
          <Text style={[styles.cardBadge, { color: '#60a5fa' }]}>PREVENT HOTEL & RENTAL LEAK FRAUD</Text>
          <Text style={styles.cardTitle}>Single-Use Watermarked Identity Pass</Text>
        </View>
        <Text style={styles.cardIntro}>
          Hotels, car rentals, and co-working spaces regularly photocopy identity cards. Generate an indelible,
          purpose-restricted masked pass with statutory warning that makes secondary reuse impossible.
        </Text>
        <TouchableOpacity
          style={[styles.portalBtn, { backgroundColor: '#1d4ed8', borderColor: '#3b82f6' }]}
          onPress={() => {
            setGeneratedPass(null);
            setPassModalVisible(true);
          }}
        >
          <Text style={[styles.portalBtnText, { color: '#ffffff' }]}>🎫 Generate Watermarked Pass</Text>
        </TouchableOpacity>
      </View>

      {/* Feature 2: 1-Tap 16-Digit Virtual ID Rotator */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardBadge}>UIDAI DISPOSABLE CREDENTIAL</Text>
          <Text style={styles.cardTitle}>1-Tap 16-Digit Virtual ID (VID) Rotator</Text>
        </View>
        <Text style={styles.cardIntro}>
          Share a temporary 16-digit VID instead of your Aadhaar number. By law (Aadhaar Act Sec 3A), banks,
          telcos, and agencies MUST accept VID.
        </Text>

        <View style={styles.vidDisplayBox}>
          <View>
            <Text style={styles.vidLabel}>CURRENT ACTIVE VIRTUAL ID</Text>
            <Text style={styles.vidNumber}>
              {vidData ? vidData.formatted : '•••• •••• •••• ••••'}
            </Text>
            <Text style={styles.vidExpiry}>
              {vidData ? `Valid Until: ${new Date(vidData.validUntil).toLocaleString()}` : 'Rotating...'}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.vidRotateBtn}
            onPress={() => handleGenerateVid(false)}
            disabled={generatingVid}
          >
            {generatingVid ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.vidRotateBtnText}>🔄 Rotate</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Feature 3: National Cybercrime 1930 & Legal FIR Assistant */}
      <View style={[styles.card, { borderColor: '#b91c1c' }]}>
        <View style={styles.cardHeader}>
          <Text style={[styles.cardBadge, { color: '#f87171' }]}>CRITICAL INCIDENT RESPONSE</Text>
          <Text style={styles.cardTitle}>National Cybercrime 1930 & FIR Assistant</Text>
        </View>
        <Text style={styles.cardIntro}>
          Incurred an unauthorized AePS debit, identity theft, or darkweb leak? Connect directly to the MHA 1930
          financial cybercrime helpline and generate an IT Act Section 66C/66D complaint letter.
        </Text>

        <View style={styles.cybercrimeActionRow}>
          <TouchableOpacity
            style={[styles.portalBtn, { flex: 1, backgroundColor: '#991b1b', borderColor: '#ef4444' }]}
            onPress={handleDial1930}
          >
            <Text style={[styles.portalBtnText, { color: '#ffffff' }]}>📞 Call 1930 (Toll Free)</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.portalBtn, { flex: 1, backgroundColor: '#1e293b', borderColor: '#475569' }]}
            onPress={() => {
              setGeneratedFIR(null);
              setFirModalVisible(true);
            }}
          >
            <Text style={[styles.portalBtnText, { color: '#cbd5e1' }]}>⚖️ Draft IT Act FIR</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Guide: Biometric Lock */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardBadge}>OFFLINE-READY GUIDE</Text>
          <Text style={styles.cardTitle}>How to Lock Your Aadhaar Biometrics</Text>
        </View>
        <Text style={styles.cardIntro}>
          Biometric locking disables fingerprint and iris authentication at micro-ATMs and PoS terminals,
          permanently stopping AePS financial fraud.
        </Text>

        <View style={styles.stepsList}>
          <View style={styles.stepRow}>
            <View style={styles.stepNum}><Text style={styles.stepNumText}>1</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>Open Official UIDAI Portal</Text>
              <Text style={styles.stepText}>Visit myaadhaar.uidai.gov.in or mAadhaar app.</Text>
            </View>
          </View>

          <View style={styles.stepRow}>
            <View style={styles.stepNum}><Text style={styles.stepNumText}>2</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>Log In with Aadhaar OTP</Text>
              <Text style={styles.stepText}>Authenticate with registered mobile number OTP.</Text>
            </View>
          </View>

          <View style={styles.stepRow}>
            <View style={styles.stepNum}><Text style={styles.stepNumText}>3</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>Toggle "Lock Biometrics"</Text>
              <Text style={styles.stepText}>Locks fingerprint & iris until you temporarily unlock.</Text>
            </View>
          </View>
        </View>

        <View style={styles.guideButtons}>
          <TouchableOpacity style={styles.portalBtn} onPress={handleOpenUIDAI}>
            <Text style={styles.portalBtnText}>🔗 Open UIDAI Portal (External)</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.confirmBtn, lockedConfirmed && styles.confirmBtnSuccess]}
            onPress={handleConfirmLock}
            disabled={submittingLock || lockedConfirmed}
          >
            {submittingLock ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.confirmBtnText}>
                {lockedConfirmed ? '✓ Biometrics Confirmed Locked' : 'Record "I Have Locked Biometrics"'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Guide: PAN-Aadhaar Linkage */}
      <View style={styles.card}>
        <Text style={styles.cardBadge}>REGULATORY COMPLIANCE</Text>
        <Text style={styles.cardTitle}>Verify PAN-Aadhaar Linkage Status</Text>
        <Text style={styles.cardIntro}>
          Under Section 139AA of the Income-tax Act, verify that your PAN is correctly linked to your Aadhaar.
        </Text>
        <TouchableOpacity style={styles.portalBtn} onPress={handleOpenITD}>
          <Text style={styles.portalBtnText}>🔗 Check Status on Income Tax e-Filing Portal</Text>
        </TouchableOpacity>
      </View>

      {/* Feature 4: DoT Sanchar Saathi & TAFCOP SIM Audit Assistant */}
      <View style={[styles.card, { borderColor: '#0ea5e9' }]}>
        <View style={styles.cardHeader}>
          <Text style={[styles.cardBadge, { color: '#38bdf8' }]}>DOT SANCHAR SAATHI TELECOM DEFENSE</Text>
          <Text style={styles.cardTitle}>DoT TAFCOP SIM Audit & CEIR Radar</Text>
        </View>
        <Text style={styles.cardIntro}>
          Detect unauthorized mobile numbers registered against your Aadhaar/PAN without your consent.
          Block stolen handsets on all Indian networks via Central Equipment Identity Register (CEIR).
        </Text>

        <View style={{ flexDirection: 'row', gap: 8, marginBottom: 8 }}>
          <TouchableOpacity
            style={[styles.portalBtn, { flex: 1, backgroundColor: '#0369a1', borderColor: '#0ea5e9' }]}
            onPress={() => setSimModalVisible(true)}
          >
            <Text style={[styles.portalBtnText, { color: '#ffffff' }]}>🔍 Audit SIMs ({simConnections.length} Monitored)</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.portalBtn, { flex: 1, backgroundColor: '#1e293b', borderColor: '#475569' }]}
            onPress={handleOpenTAFCOP}
          >
            <Text style={[styles.portalBtnText, { color: '#cbd5e1' }]}>🔗 TAFCOP Portal</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.portalBtn} onPress={handleOpenCEIR}>
          <Text style={styles.portalBtnText}>📱 CEIR Portal: Block Lost/Stolen Mobile Handset</Text>
        </TouchableOpacity>
      </View>

      {/* Feature 5: RBI Account Aggregator & Credit Bureau Impersonation Radar */}
      <View style={[styles.card, { borderColor: '#f59e0b' }]}>
        <View style={styles.cardHeader}>
          <Text style={[styles.cardBadge, { color: '#fbbf24' }]}>CIBIL / EXPERIAN / CRIF RADAR</Text>
          <Text style={styles.cardTitle}>Credit Impersonation & Instant Loan Radar</Text>
        </View>
        <Text style={styles.cardIntro}>
          Monitors unauthorized credit inquiries and BNPL loan requests pulled on your PAN. Generate immediate
          dispute letters addressed to the lender and the RBI Banking Ombudsman (cms.rbi.org.in).
        </Text>

        <View style={{ flexDirection: 'row', gap: 8 }}>
          <TouchableOpacity
            style={[styles.portalBtn, { flex: 1, backgroundColor: '#b45309', borderColor: '#f59e0b' }]}
            onPress={() => setCreditModalVisible(true)}
          >
            <Text style={[styles.portalBtnText, { color: '#ffffff' }]}>
              💳 Credit Inquiries ({creditInquiries.filter((i) => !i.authorizedByCitizen).length} Suspicious)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.portalBtn, { flex: 1, backgroundColor: '#1e293b', borderColor: '#475569' }]}
            onPress={handleOpenRBI}
          >
            <Text style={[styles.portalBtnText, { color: '#cbd5e1' }]}>🏦 RBI Ombudsman</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Feature 6: Court-Admissible Forensic Evidence Package (Section 63 BSA 2023 / 65B IEA) */}
      <View style={[styles.card, { borderColor: '#8b5cf6' }]}>
        <View style={styles.cardHeader}>
          <Text style={[styles.cardBadge, { color: '#c084fc' }]}>BHARATIYA SAKSHYA ADHINIYAM COMPLIANT</Text>
          <Text style={styles.cardTitle}>Section 63 BSA Forensic Evidence Package</Text>
        </View>
        <Text style={styles.cardIntro}>
          Replaces legacy Section 65B Indian Evidence Act affidavits (effective 1 July 2024). Packages SMS OTP
          headers, bank transaction UTRs, and screenshot SHA-256 digests into a court-ready electronic affidavit.
        </Text>

        <TouchableOpacity
          style={[styles.portalBtn, { backgroundColor: '#6d28d9', borderColor: '#8b5cf6' }]}
          onPress={handleGenerateEvidence}
        >
          <Text style={[styles.portalBtnText, { color: '#ffffff' }]}>📜 Generate Court Affidavit (BSA Sec 63)</Text>
        </TouchableOpacity>
      </View>

      {/* Modal 1: Single-Use Watermarked Pass Modal */}
      <Modal visible={passModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <ScrollView contentContainerStyle={styles.modalScroll}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Certified Identity Pass Generator</Text>
              <Text style={styles.modalSub}>
                Creates an immutable masked identity document with purpose watermark and tamper-evident QR code.
              </Text>

              {!generatedPass ? (
                <>
                  <Text style={styles.inputLabel}>Recipient Hotel / Business / Organization:</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g. Taj Lands End, Mumbai"
                    placeholderTextColor="#64748b"
                    value={passRecipient}
                    onChangeText={setPassRecipient}
                  />

                  <Text style={styles.inputLabel}>Purpose of Sharing:</Text>
                  <View style={styles.typeSelector}>
                    {[
                      { key: 'hotel_checkin', label: '🏨 Hotel Check-In' },
                      { key: 'car_rental', label: '🚗 Car Rental' },
                      { key: 'coworking_visit', label: '🏢 Co-working' },
                    ].map((p) => (
                      <TouchableOpacity
                        key={p.key}
                        style={[styles.typeBtn, passPurpose === p.key && styles.typeBtnActiveBlue]}
                        onPress={() => setPassPurpose(p.key as any)}
                      >
                        <Text style={[styles.typeBtnText, passPurpose === p.key && styles.typeBtnTextActiveBlue]}>
                          {p.label}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>

                  <Text style={styles.inputLabel}>Document Type to Mask & Certify:</Text>
                  <View style={styles.typeSelector}>
                    {[
                      { key: 'aadhaar', label: '🇮🇳 Aadhaar' },
                      { key: 'driving_license', label: '🚗 Driving Lic' },
                      { key: 'pan', label: '💳 PAN Card' },
                    ].map((d) => (
                      <TouchableOpacity
                        key={d.key}
                        style={[styles.typeBtn, passDocType === d.key && styles.typeBtnActiveBlue]}
                        onPress={() => setPassDocType(d.key as any)}
                      >
                        <Text style={[styles.typeBtnText, passDocType === d.key && styles.typeBtnTextActiveBlue]}>
                          {d.label}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>

                  <View style={styles.modalButtons}>
                    <TouchableOpacity
                      style={styles.btnSecondary}
                      onPress={() => setPassModalVisible(false)}
                    >
                      <Text style={styles.btnSecondaryText}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.btnPrimary, { backgroundColor: '#2563eb' }]}
                      onPress={handleCreatePass}
                    >
                      <Text style={styles.btnPrimaryText}>Generate Pass</Text>
                    </TouchableOpacity>
                  </View>
                </>
              ) : (
                <View>
                  {/* Watermarked Pass Preview Card */}
                  <View style={styles.passPreviewCard}>
                    <View style={styles.watermarkOverlay}>
                      <Text style={styles.watermarkOverlayText}>{generatedPass.watermarkText}</Text>
                    </View>

                    <View style={styles.passBadgeRow}>
                      <Text style={styles.passHeaderPill}>CERTIFIED PASS #{generatedPass.passId}</Text>
                      <Text style={styles.passExpiryPill}>EXPIRES: {generatedPass.validUntil}</Text>
                    </View>

                    <Text style={styles.passHolder}>{generatedPass.holderName}</Text>
                    <Text style={styles.passDocNum}>{generatedPass.maskedIdentifier}</Text>
                    <Text style={styles.passRecipientText}>RECIPIENT: {generatedPass.recipientEntity.toUpperCase()}</Text>
                    <Text style={styles.passPurposeText}>PURPOSE: {generatedPass.purposeText.toUpperCase()}</Text>

                    <View style={styles.qrMockBox}>
                      <Text style={styles.qrMockIcon}>🔐</Text>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.qrMockText}>Ed25519 Asymmetric Signature Attached</Text>
                        <Text style={{ fontSize: 9, color: '#93c5fd', fontFamily: 'monospace' }}>
                          Pubkey: {generatedPass.signerPublicKey.slice(0, 16)}... • Sig: {generatedPass.signatureHex.slice(0, 16)}...
                        </Text>
                      </View>
                      <TouchableOpacity
                        style={{ backgroundColor: '#0284c7', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 }}
                        onPress={handleVerifyPass}
                      >
                        <Text style={{ color: '#fff', fontSize: 10, fontWeight: '700' }}>Verify</Text>
                      </TouchableOpacity>
                    </View>
                  </View>

                  {/* Legal Notice */}
                  <View style={styles.legalNoticeBox}>
                    <Text style={styles.legalNoticeTitle}>STATUTORY CLAUSE (Aadhaar Act & IT Act):</Text>
                    <Text style={styles.legalNoticeText}>{generatedPass.legalNotice}</Text>
                  </View>

                  <View style={styles.modalButtons}>
                    <TouchableOpacity
                      style={styles.btnSecondary}
                      onPress={() => setGeneratedPass(null)}
                    >
                      <Text style={styles.btnSecondaryText}>Back / Edit</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.btnPrimary, { backgroundColor: '#059669' }]}
                      onPress={() => copyToClipboard(
                        `${generatedPass.watermarkText}\n\n${generatedPass.legalNotice}\n\nPass Payload: ${generatedPass.qrPayload}`,
                        'Pass Copied'
                      )}
                    >
                      <Text style={styles.btnPrimaryText}>📋 Copy Pass</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Modal 2: National Cybercrime 1930 / FIR Drafter Modal */}
      <Modal visible={firModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <ScrollView contentContainerStyle={styles.modalScroll}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>National Cybercrime 1930 & FIR Assistant</Text>
              <Text style={styles.modalSub}>
                Auto-generates formal police complaint pre-citing IT Act 66C/66D and Aadhaar Act Sec 43 for cybercrime.gov.in.
              </Text>

              {!generatedFIR ? (
                <>
                  <Text style={styles.inputLabel}>Incident Type:</Text>
                  <View style={styles.typeSelector}>
                    {[
                      { key: 'aeps_biometric_fraud', label: 'AePS Biometric' },
                      { key: 'sim_swap', label: 'SIM Swap' },
                      { key: 'unauthorized_loan', label: 'Fraud Loan' },
                      { key: 'darkweb_leak', label: 'Data Leak' },
                    ].map((t) => (
                      <TouchableOpacity
                        key={t.key}
                        style={[styles.typeBtn, incidentType === t.key && styles.typeBtnActive]}
                        onPress={() => setIncidentType(t.key as any)}
                      >
                        <Text style={[styles.typeBtnText, incidentType === t.key && styles.typeBtnTextActive]}>
                          {t.label}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>

                  <Text style={styles.inputLabel}>Victim Full Name & Contact Phone:</Text>
                  <View style={{ flexDirection: 'row', gap: 8 }}>
                    <TextInput
                      style={[styles.input, { flex: 1 }]}
                      placeholder="Full Name"
                      placeholderTextColor="#64748b"
                      value={victimName}
                      onChangeText={setVictimName}
                    />
                    <TextInput
                      style={[styles.input, { flex: 1 }]}
                      placeholder="Mobile Phone"
                      placeholderTextColor="#64748b"
                      keyboardType="phone-pad"
                      value={victimPhone}
                      onChangeText={setVictimPhone}
                    />
                  </View>

                  <Text style={styles.inputLabel}>Financial Loss in ₹ (if any):</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g. 10000"
                    placeholderTextColor="#64748b"
                    keyboardType="numeric"
                    value={lossAmount}
                    onChangeText={setLossAmount}
                  />

                  <Text style={styles.inputLabel}>Incident Facts & Suspect Details:</Text>
                  <TextInput
                    style={[styles.input, { height: 70, textAlignVertical: 'top' }]}
                    multiline
                    placeholder="Any micro-ATM location, bank account debited, or SMS timestamps..."
                    placeholderTextColor="#64748b"
                    value={suspectNotes}
                    onChangeText={setSuspectNotes}
                  />

                  <View style={styles.modalButtons}>
                    <TouchableOpacity
                      style={styles.btnSecondary}
                      onPress={() => setFirModalVisible(false)}
                    >
                      <Text style={styles.btnSecondaryText}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.btnPrimary, { backgroundColor: '#dc2626' }]}
                      onPress={handleGenerateFIR}
                    >
                      <Text style={styles.btnPrimaryText}>Draft Legal Complaint</Text>
                    </TouchableOpacity>
                  </View>
                </>
              ) : (
                <View>
                  <View style={styles.firChecklistCard}>
                    <Text style={styles.firChecklistTitle}>IMMEDIATE ACTIONS CHECKLIST:</Text>
                    {generatedFIR.immediateChecklist.map((step, idx) => (
                      <Text key={idx} style={styles.firChecklistText}>• {step}</Text>
                    ))}
                  </View>

                  <Text style={styles.inputLabel}>Statutory Sections Cited:</Text>
                  <View style={styles.clausesBox}>
                    {generatedFIR.statutoryClauses.map((c, i) => (
                      <Text key={i} style={styles.clauseItem}>⚖️ {c}</Text>
                    ))}
                  </View>

                  <Text style={styles.inputLabel}>Formal Complaint Dossier Preview:</Text>
                  <ScrollView style={styles.dossierScrollBox}>
                    <Text style={styles.dossierText}>{generatedFIR.formalComplaintBody}</Text>
                  </ScrollView>

                  <View style={styles.modalButtons}>
                    <TouchableOpacity
                      style={styles.btnSecondary}
                      onPress={() => setGeneratedFIR(null)}
                    >
                      <Text style={styles.btnSecondaryText}>Back</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.btnPrimary, { backgroundColor: '#0284c7' }]}
                      onPress={handleOpenCybercrimeGov}
                    >
                      <Text style={styles.btnPrimaryText}>cybercrime.gov.in</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.btnPrimary, { backgroundColor: '#059669' }]}
                      onPress={() => copyToClipboard(generatedFIR.formalComplaintBody, 'Complaint Copied')}
                    >
                      <Text style={styles.btnPrimaryText}>📋 Copy Dossier</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          </ScrollView>
        </View>
      </Modal>
      {/* Modal 3: TAFCOP SIM Connections Modal */}
      <Modal visible={simModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <ScrollView contentContainerStyle={styles.modalScroll}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>DoT TAFCOP SIM Connections Audit</Text>
              <Text style={styles.modalSub}>
                Department of Telecommunications active mobile connections linked to your documents.
              </Text>

              {simConnections.map((sim) => {
                const isGhost = sim.status === 'unauthorized_ghost';
                return (
                  <View
                    key={sim.id}
                    style={[
                      styles.simCard,
                      isGhost ? { borderColor: '#ef4444', backgroundColor: '#450a0a' } : { borderColor: '#1e293b' },
                    ]}
                  >
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <Text style={{ fontSize: 15, fontWeight: '700', color: isGhost ? '#fca5a5' : '#f8fafc', fontFamily: 'monospace' }}>
                        {sim.mobileNumberMasked}
                      </Text>
                      <Text
                        style={[
                          styles.simBadge,
                          isGhost ? { backgroundColor: '#7f1d1d', color: '#fca5a5' } : { backgroundColor: '#064e3b', color: '#6ee7b7' },
                        ]}
                      >
                        {isGhost ? '⚠️ GHOST SIM / UNKNOWN' : '✓ AUTHORIZED'}
                      </Text>
                    </View>
                    <Text style={{ fontSize: 12, color: '#94a3b8' }}>
                      Operator: <Text style={{ color: '#cbd5e1', fontWeight: '600' }}>{sim.telecomOperator}</Text> • Linked to: <Text style={{ color: '#cbd5e1', fontWeight: '600' }}>{sim.linkedDocument.toUpperCase()}</Text>
                    </Text>
                    <Text style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                      Registered: {sim.issuedDate}
                    </Text>
                    {isGhost && (
                      <View style={{ marginTop: 8, padding: 8, backgroundColor: '#571010', borderRadius: 6 }}>
                        <Text style={{ fontSize: 11, color: '#fee2e2', fontWeight: '600' }}>
                          CRITICAL: This connection was NOT authorized by you. Disconnect immediately on the DoT TAFCOP portal.
                        </Text>
                      </View>
                    )}
                  </View>
                );
              })}

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={styles.btnSecondary}
                  onPress={() => setSimModalVisible(false)}
                >
                  <Text style={styles.btnSecondaryText}>Close</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btnPrimary, { backgroundColor: '#0284c7' }]}
                  onPress={handleOpenTAFCOP}
                >
                  <Text style={styles.btnPrimaryText}>Open TAFCOP Portal</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Modal 4: Credit Inquiries & RBI Dispute Modal */}
      <Modal visible={creditModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <ScrollView contentContainerStyle={styles.modalScroll}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Credit Inquiries & Impersonation Radar</Text>
              <Text style={styles.modalSub}>
                CIBIL / Experian soft & hard pulls registered on your PAN.
              </Text>

              {creditInquiries.map((inq) => {
                const isFraud = !inq.authorizedByCitizen;
                return (
                  <View
                    key={inq.id}
                    style={[
                      styles.simCard,
                      isFraud ? { borderColor: '#ef4444', backgroundColor: '#450a0a' } : { borderColor: '#1e293b' },
                    ]}
                  >
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <Text style={{ fontSize: 14, fontWeight: '700', color: isFraud ? '#fca5a5' : '#f8fafc' }}>
                        {inq.lenderName}
                      </Text>
                      <Text
                        style={[
                          styles.simBadge,
                          isFraud ? { backgroundColor: '#7f1d1d', color: '#fca5a5' } : { backgroundColor: '#064e3b', color: '#6ee7b7' },
                        ]}
                      >
                        {isFraud ? '🚨 UNAUTHORIZED PULL' : '✓ AUTHORIZED'}
                      </Text>
                    </View>
                    <Text style={{ fontSize: 12, color: '#94a3b8' }}>
                      Type: <Text style={{ color: '#cbd5e1', fontWeight: '600' }}>{inq.inquiryType.toUpperCase()}</Text> • Bureau: <Text style={{ color: '#cbd5e1', fontWeight: '600' }}>{inq.bureauReported}</Text>
                    </Text>
                    {inq.amountRequestedInr && (
                      <Text style={{ fontSize: 12, color: '#f59e0b', fontWeight: '700', marginTop: 2 }}>
                        Loan Amount Attempted: ₹{inq.amountRequestedInr.toLocaleString('en-IN')}
                      </Text>
                    )}
                    <Text style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                      Inquiry Date: {inq.inquiryDate}
                    </Text>
                    {isFraud && (
                      <TouchableOpacity
                        style={{ marginTop: 8, padding: 8, backgroundColor: '#b45309', borderRadius: 6, alignItems: 'center' }}
                        onPress={() => handleCopyDisputeLetter(inq)}
                      >
                        <Text style={{ fontSize: 12, color: '#ffffff', fontWeight: '700' }}>
                          ⚖️ Copy RBI & CIBIL Dispute Letter
                        </Text>
                      </TouchableOpacity>
                    )}
                  </View>
                );
              })}

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={styles.btnSecondary}
                  onPress={() => setCreditModalVisible(false)}
                >
                  <Text style={styles.btnSecondaryText}>Close</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btnPrimary, { backgroundColor: '#b45309' }]}
                  onPress={handleOpenRBI}
                >
                  <Text style={styles.btnPrimaryText}>RBI Ombudsman</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Modal 5: Section 63 BSA Forensic Evidence Package Modal */}
      <Modal visible={evidenceModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <ScrollView contentContainerStyle={styles.modalScroll}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Section 63 BSA 2023 Electronic Evidence</Text>
              <Text style={styles.modalSub}>
                Statutory certificate for Cyber Police Stations & Judicial Magistrate Courts under Bharatiya Sakshya Adhiniyam, 2023.
              </Text>

              {generatedEvidence && (
                <View>
                  <View style={{ backgroundColor: '#1e1b4b', padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#6366f1', marginBottom: 12 }}>
                    <Text style={{ fontSize: 11, fontWeight: '800', color: '#c7d2fe', marginBottom: 4 }}>
                      CERTIFICATE ID: {generatedEvidence.certificateId}
                    </Text>
                    <Text style={{ fontSize: 11, color: '#93c5fd', marginBottom: 2 }}>
                      Citation: {generatedEvidence.statutoryActCitation}
                    </Text>
                    <Text style={{ fontSize: 10, color: '#cbd5e1', fontFamily: 'monospace' }}>
                      Manifest SHA-256: {generatedEvidence.manifestHash}
                    </Text>
                  </View>

                  <Text style={styles.inputLabel}>Included Evidence Items ({generatedEvidence.evidenceItems.length}):</Text>
                  {generatedEvidence.evidenceItems.map((item, idx) => (
                    <View key={idx} style={{ backgroundColor: '#090d16', padding: 8, borderRadius: 6, borderWidth: 1, borderColor: '#1e293b', marginBottom: 6 }}>
                      <Text style={{ fontSize: 11, fontWeight: '700', color: '#f8fafc' }}>
                        [{item.type.toUpperCase()}] {item.description}
                      </Text>
                      <Text style={{ fontSize: 10, color: '#94a3b8' }}>Source: {item.sourceReference}</Text>
                      <Text style={{ fontSize: 9, color: '#64748b', fontFamily: 'monospace' }}>SHA-256: {item.sha256Digest.slice(0, 24)}...</Text>
                    </View>
                  ))}

                  <Text style={[styles.inputLabel, { marginTop: 8 }]}>Statutory Affidavit Text:</Text>
                  <ScrollView style={styles.dossierScrollBox}>
                    <Text style={styles.dossierText}>{generatedEvidence.affidavitBody}</Text>
                  </ScrollView>

                  <View style={styles.modalButtons}>
                    <TouchableOpacity
                      style={styles.btnSecondary}
                      onPress={() => setEvidenceModalVisible(false)}
                    >
                      <Text style={styles.btnSecondaryText}>Close</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.btnPrimary, { backgroundColor: '#6d28d9' }]}
                      onPress={() => copyToClipboard(generatedEvidence.affidavitBody, 'Section 63 Affidavit Copied')}
                    >
                      <Text style={styles.btnPrimaryText}>📋 Copy Affidavit</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          </ScrollView>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 16,
    marginTop: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#f8fafc',
  },
  subtitle: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  bannerGuar: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 16,
  },
  bannerGuarIcon: {
    fontSize: 18,
    marginRight: 10,
  },
  bannerGuarText: {
    flex: 1,
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 16,
  },
  card: {
    backgroundColor: '#111827',
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderColor: '#1f2937',
    marginBottom: 16,
  },
  cardHeader: {
    marginBottom: 6,
  },
  cardBadge: {
    fontSize: 10,
    fontWeight: '700',
    color: '#38bdf8',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 6,
  },
  cardIntro: {
    fontSize: 12,
    color: '#94a3b8',
    lineHeight: 17,
    marginBottom: 14,
  },
  stepsList: {
    marginBottom: 14,
  },
  stepRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  stepNum: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  stepNumText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '700',
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#f8fafc',
    marginBottom: 2,
  },
  stepText: {
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 15,
  },
  guideButtons: {
    gap: 8,
  },
  portalBtn: {
    backgroundColor: '#1f2937',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#374151',
  },
  portalBtnText: {
    color: '#38bdf8',
    fontWeight: '600',
    fontSize: 13,
  },
  confirmBtn: {
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  confirmBtnSuccess: {
    backgroundColor: '#059669',
  },
  confirmBtnText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 13,
  },
  vidDisplayBox: {
    backgroundColor: '#0c1a2f',
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e3a8a',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  vidLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#93c5fd',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  vidNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: '#ffffff',
    fontFamily: 'monospace',
    letterSpacing: 1.5,
    marginBottom: 2,
  },
  vidExpiry: {
    fontSize: 10,
    color: '#60a5fa',
  },
  vidRotateBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  vidRotateBtnText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 12,
  },
  cybercrimeActionRow: {
    flexDirection: 'row',
    gap: 10,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    padding: 16,
  },
  modalScroll: {
    paddingVertical: 20,
  },
  modalContent: {
    backgroundColor: '#111827',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#374151',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  modalSub: {
    fontSize: 12,
    color: '#94a3b8',
    marginBottom: 14,
    lineHeight: 16,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#cbd5e1',
    marginBottom: 6,
    marginTop: 4,
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 12,
  },
  typeBtn: {
    flex: 1,
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#374151',
    paddingVertical: 7,
    paddingHorizontal: 4,
    borderRadius: 6,
    alignItems: 'center',
  },
  typeBtnActive: {
    borderColor: '#ef4444',
    backgroundColor: '#450a0a',
  },
  typeBtnActiveBlue: {
    borderColor: '#3b82f6',
    backgroundColor: '#1e3a8a',
  },
  typeBtnText: {
    color: '#94a3b8',
    fontSize: 11,
    textAlign: 'center',
  },
  typeBtnTextActive: {
    color: '#f87171',
    fontWeight: '700',
  },
  typeBtnTextActiveBlue: {
    color: '#bfdbfe',
    fontWeight: '700',
  },
  input: {
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 8,
    padding: 10,
    color: '#f8fafc',
    fontSize: 13,
    marginBottom: 12,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 8,
  },
  btnSecondary: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#4b5563',
    backgroundColor: '#1e293b',
  },
  btnSecondaryText: {
    color: '#cbd5e1',
    fontSize: 12,
    fontWeight: '600',
  },
  btnPrimary: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
  },
  btnPrimaryText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  passPreviewCard: {
    backgroundColor: '#041727',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#0284c7',
    marginBottom: 12,
    position: 'relative',
    overflow: 'hidden',
  },
  watermarkOverlay: {
    position: 'absolute',
    top: 20,
    left: -20,
    right: -20,
    bottom: 20,
    justifyContent: 'center',
    alignItems: 'center',
    transform: [{ rotate: '-18deg' }],
    opacity: 0.15,
  },
  watermarkOverlayText: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '900',
    textAlign: 'center',
    letterSpacing: 1,
  },
  passBadgeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  passHeaderPill: {
    fontSize: 10,
    fontWeight: '800',
    color: '#38bdf8',
    backgroundColor: '#082f49',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  passExpiryPill: {
    fontSize: 10,
    fontWeight: '700',
    color: '#f59e0b',
  },
  passHolder: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 2,
  },
  passDocNum: {
    fontSize: 18,
    fontWeight: '800',
    color: '#38bdf8',
    fontFamily: 'monospace',
    letterSpacing: 2,
    marginBottom: 10,
  },
  passRecipientText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 2,
  },
  passPurposeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 10,
  },
  qrMockBox: {
    backgroundColor: '#082f49',
    padding: 8,
    borderRadius: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  qrMockIcon: {
    fontSize: 16,
  },
  qrMockText: {
    fontSize: 10,
    color: '#bae6fd',
    fontWeight: '600',
  },
  legalNoticeBox: {
    backgroundColor: '#090d16',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 14,
  },
  legalNoticeTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: '#f59e0b',
    marginBottom: 4,
  },
  legalNoticeText: {
    fontSize: 10,
    color: '#94a3b8',
    lineHeight: 14,
  },
  firChecklistCard: {
    backgroundColor: '#450a0a',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ef4444',
    marginBottom: 10,
  },
  firChecklistTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: '#fca5a5',
    marginBottom: 4,
  },
  firChecklistText: {
    fontSize: 11,
    color: '#fee2e2',
    lineHeight: 16,
  },
  clausesBox: {
    backgroundColor: '#090d16',
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#374151',
    marginBottom: 10,
  },
  clauseItem: {
    fontSize: 10,
    color: '#cbd5e1',
    lineHeight: 15,
  },
  dossierScrollBox: {
    maxHeight: 150,
    backgroundColor: '#090d16',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#374151',
    marginBottom: 12,
  },
  dossierText: {
    fontSize: 10,
    color: '#cbd5e1',
    fontFamily: 'monospace',
    lineHeight: 14,
  },
  simCard: {
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  simBadge: {
    fontSize: 10,
    fontWeight: '800',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: 'hidden',
  },
});
