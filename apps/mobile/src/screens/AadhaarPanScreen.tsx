import React, { useState } from 'react';
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

export const AadhaarPanScreen: React.FC = () => {
  const [lockedConfirmed, setLockedConfirmed] = useState(false);
  const [submittingLock, setSubmittingLock] = useState(false);
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const [incidentType, setIncidentType] = useState('unauthorized_aadhaar_auth');
  const [incidentDescription, setIncidentDescription] = useState('');
  const [submittingReport, setSubmittingReport] = useState(false);

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

  const handleReportSuspicious = async () => {
    if (!incidentDescription.trim()) {
      return Alert.alert('Description Required', 'Please detail the suspicious SMS, OTP, or activity.');
    }
    setSubmittingReport(true);
    try {
      await api.reportSuspiciousActivity({
        incident_type: incidentType,
        description: incidentDescription.trim(),
      });
      Alert.alert('Report Logged', 'Incident report registered. Follow the UIDAI 1947 helpline guidance below.');
      setReportModalVisible(false);
      setIncidentDescription('');
    } catch (err: any) {
      Alert.alert('Report Failed', err.message);
    } finally {
      setSubmittingReport(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Aadhaar & PAN Assistance</Text>
        <Text style={styles.subtitle}>
          Authoritative self-service guidance • Zero scraping guarantee
        </Text>
      </View>

      {/* Zero Scraping Guarantee Pill */}
      <View style={styles.bannerGuar}>
        <Text style={styles.bannerGuarIcon}>🏛️</Text>
        <Text style={styles.bannerGuarText}>
          The platform operates strictly as an advisory companion. We never impersonate UIDAI or the
          Income Tax Department, nor do we request or store your raw Aadhaar number or OTPs.
        </Text>
      </View>

      {/* Guide 1: Biometric Lock */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardBadge}>OFFLINE-READY GUIDE</Text>
          <Text style={styles.cardTitle}>How to Lock Your Aadhaar Biometrics</Text>
        </View>
        <Text style={styles.cardIntro}>
          Biometric locking prevents unauthorized Aadhaar authentication (fingerprint, iris, face) by fraudulent parties.
        </Text>

        <View style={styles.stepsList}>
          <View style={styles.stepRow}>
            <View style={styles.stepNum}><Text style={styles.stepNumText}>1</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>Open Official UIDAI Portal or mAadhaar</Text>
              <Text style={styles.stepText}>Visit myaadhaar.uidai.gov.in or install the official mAadhaar mobile app.</Text>
            </View>
          </View>

          <View style={styles.stepRow}>
            <View style={styles.stepNum}><Text style={styles.stepNumText}>2</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>Log In with Aadhaar & OTP</Text>
              <Text style={styles.stepText}>Enter your 12-digit number and authenticate with the OTP received on your UIDAI-registered mobile.</Text>
            </View>
          </View>

          <View style={styles.stepRow}>
            <View style={styles.stepNum}><Text style={styles.stepNumText}>3</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>Select "Lock/Unlock Biometrics"</Text>
              <Text style={styles.stepText}>Navigate to the Security services tile and toggle Biometrics to Locked.</Text>
            </View>
          </View>

          <View style={styles.stepRow}>
            <View style={styles.stepNum}><Text style={styles.stepNumText}>4</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>Temporary Unlock for Legitimate Use</Text>
              <Text style={styles.stepText}>When needing to authenticate (e.g. SIM purchase or banking), unlock temporarily for 10 minutes.</Text>
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

      {/* Guide 2: PAN-Aadhaar Linkage */}
      <View style={styles.card}>
        <Text style={styles.cardBadge}>REGULATORY COMPLIANCE</Text>
        <Text style={styles.cardTitle}>Verify PAN-Aadhaar Linkage Status</Text>
        <Text style={styles.cardIntro}>
          Under Section 139AA of the Income-tax Act, verify that your Permanent Account Number (PAN) is correctly linked to your Aadhaar.
        </Text>
        <TouchableOpacity style={styles.portalBtn} onPress={handleOpenITD}>
          <Text style={styles.portalBtnText}>🔗 Check Status on Income Tax e-Filing Portal</Text>
        </TouchableOpacity>
      </View>

      {/* Suspicious Activity Report Card */}
      <View style={[styles.card, { borderColor: '#b91c1c' }]}>
        <Text style={[styles.cardBadge, { color: '#f87171' }]}>ASSISTANCE & INCIDENT ESCALATION</Text>
        <Text style={styles.cardTitle}>Report Suspicious Aadhaar / Financial Activity</Text>
        <Text style={styles.cardIntro}>
          Received an unexpected authentication OTP or suspect unauthorized SIM issuance using your identity?
        </Text>
        <TouchableOpacity
          style={[styles.portalBtn, { backgroundColor: '#7f1d1d', borderColor: '#ef4444' }]}
          onPress={() => setReportModalVisible(true)}
        >
          <Text style={[styles.portalBtnText, { color: '#fca5a5' }]}>⚠️ Log Suspicious Activity Report</Text>
        </TouchableOpacity>
      </View>

      {/* Suspicious Activity Modal */}
      <Modal visible={reportModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Report Suspicious Incident</Text>
            <Text style={styles.modalSub}>
              Log details for your audit report and get step-by-step guidance on contacting UIDAI 1947 or Cyber Crime 1930.
            </Text>

            <Text style={styles.inputLabel}>Incident Type:</Text>
            <View style={styles.typeSelector}>
              {[
                { key: 'unauthorized_aadhaar_auth', label: 'Unexpected Auth OTP' },
                { key: 'sim_fraud', label: 'Unsolicited SIM' },
                { key: 'financial_fraud', label: 'Fraudulent Loan/Credit' },
              ].map((t) => (
                <TouchableOpacity
                  key={t.key}
                  style={[styles.typeBtn, incidentType === t.key && styles.typeBtnActive]}
                  onPress={() => setIncidentType(t.key)}
                >
                  <Text style={[styles.typeBtnText, incidentType === t.key && styles.typeBtnTextActive]}>
                    {t.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.inputLabel}>Details & Narrative:</Text>
            <TextInput
              style={[styles.input, { height: 90, textAlignVertical: 'top' }]}
              multiline
              placeholder="Describe what occurred, any reference numbers or timestamps..."
              placeholderTextColor="#64748b"
              value={incidentDescription}
              onChangeText={setIncidentDescription}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.btnSecondary}
                onPress={() => setReportModalVisible(false)}
                disabled={submittingReport}
              >
                <Text style={styles.btnSecondaryText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btnPrimary, { backgroundColor: '#ef4444' }]}
                onPress={handleReportSuspicious}
                disabled={submittingReport}
              >
                {submittingReport ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.btnPrimaryText}>Submit & Get Advice</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
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
    fontSize: 20,
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
    marginBottom: 12,
  },
  stepNum: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  stepNumText: {
    color: '#38bdf8',
    fontSize: 12,
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
    fontSize: 12,
    color: '#94a3b8',
    lineHeight: 16,
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
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    padding: 20,
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
    marginBottom: 6,
  },
  modalSub: {
    fontSize: 12,
    color: '#94a3b8',
    marginBottom: 16,
    lineHeight: 17,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#cbd5e1',
    marginBottom: 6,
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 14,
  },
  typeBtn: {
    flex: 1,
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#374151',
    paddingVertical: 6,
    paddingHorizontal: 6,
    borderRadius: 6,
    alignItems: 'center',
  },
  typeBtnActive: {
    borderColor: '#ef4444',
    backgroundColor: '#450a0a',
  },
  typeBtnText: {
    color: '#94a3b8',
    fontSize: 11,
    textAlign: 'center',
  },
  typeBtnTextActive: {
    color: '#f87171',
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 8,
    padding: 12,
    color: '#f8fafc',
    fontSize: 13,
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
  },
  btnSecondary: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#4b5563',
  },
  btnSecondaryText: {
    color: '#94a3b8',
    fontSize: 13,
  },
  btnPrimary: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  btnPrimaryText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
});
