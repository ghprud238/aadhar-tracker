import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import { api } from '../services/api';
import { CompanionGlance, UserSession } from '../types';
import {
  SUPPORTED_LANGUAGES,
  SupportedLanguage,
  VernacularPhrases,
} from '../services/bhashiniLocalization';
import { UniversalScanResult } from '../services/universalQrScanner';
import { RedactionResult } from '../services/imageRedactor';
import { antiTamperShield } from '../services/antiTamperShield';
import { ScamAnalysisResult, ScamRadarService } from '../services/scamRadar';
import { SurakshaScoreReport, SurakshaScoreService } from '../services/surakshaScore';

interface DashboardScreenProps {
  session: UserSession | null;
  onNavigate: (screen: string) => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ session, onNavigate }) => {
  const [glance, setGlance] = useState<CompanionGlance | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [scanning, setScanning] = useState(false);

  // Bhashini Vernacular State
  const [currentLang, setCurrentLang] = useState<SupportedLanguage>('en');
  const [localizedStrings, setLocalizedStrings] = useState<VernacularPhrases>(api.getLocalizedStrings('en'));

  // Universal Offline QR Scanner Modal State
  const [qrModalVisible, setQrModalVisible] = useState(false);
  const [qrInputText, setQrInputText] = useState('');
  const [scanResult, setScanResult] = useState<UniversalScanResult | null>(null);

  // In-App Canvas Auto-Redactor State
  const [redactorDocType, setRedactorDocType] = useState<'aadhaar' | 'pan' | 'driving_license'>('aadhaar');
  const [redactorRecipient, setRedactorRecipient] = useState('Taj Lands End Hotel');
  const [redactedDoc, setRedactedDoc] = useState<RedactionResult>(api.redactDocumentImage('aadhaar', 'Taj Lands End Hotel'));

  // Suraksha Score (0-1000) State
  const [scoreReport, setScoreReport] = useState<SurakshaScoreReport>(() => {
    return SurakshaScoreService.calculateScore({
      biometricsLocked: true,
      activeIdentifiersCount: 1,
      hasActiveBreaches: false,
      unauthorizedGhostSimsCount: 0,
      familyMembersProtectedCount: 1,
      hasGeneratedMaskedPass: true,
    });
  });

  // 10-Minute Biometric Auto-Relock Countdown Timer State
  const [unlockTimerActive, setUnlockTimerActive] = useState(false);
  const [unlockSecondsLeft, setUnlockSecondsLeft] = useState(600); // 10 minutes

  // Digital Arrest & Scam Radar Modal State
  const [scamModalVisible, setScamModalVisible] = useState(false);
  const [scamInputText, setScamInputText] = useState('');
  const [scamHeaderInput, setScamHeaderInput] = useState('');
  const [scamChannel, setScamChannel] = useState<'sms' | 'whatsapp' | 'video_call'>('video_call');
  const [scamResult, setScamResult] = useState<ScamAnalysisResult | null>(null);

  const loadData = async () => {
    try {
      const data = await api.getCompanionGlance();
      setGlance(data);
    } catch (err: any) {
      console.warn('Failed to load companion glance:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectLanguage = (lang: SupportedLanguage) => {
    api.setLanguage(lang);
    setCurrentLang(lang);
    setLocalizedStrings(api.getLocalizedStrings(lang));
  };

  const handlePlayVoiceGuidance = () => {
    Alert.alert(
      `🗣️ Bhashini Audio Assistant (${currentLang.toUpperCase()})`,
      `[Biometric Defense Audio Script]:\n\n"${localizedStrings.voicePromptBiometricLock}"\n\n[Emergency 1930 Helpline Audio Script]:\n\n"${localizedStrings.voicePromptCybercrimeReport}"`
    );
  };

  const handleRunQrScan = () => {
    if (!qrInputText.trim()) {
      return Alert.alert('QR Input Required', 'Please paste or select a test QR payload.');
    }
    const res = api.parseAndVerifyQr(qrInputText.trim());
    setScanResult(res);
  };

  const handleLoadSampleQr = (type: 'pass' | 'uidai' | 'tampered') => {
    if (type === 'pass') {
      const sample = JSON.stringify({
        suraksha_certified: true,
        pass_id: 'PASS_SAMPLE_8921',
        claim: {
          doc_type: 'aadhaar',
          holder: 'Aarav Sharma',
          masked_id: 'XXXX-XXXX-4819',
          recipient: 'Taj Lands End, Mumbai',
          purpose: 'hotel_checkin',
          valid_until: '2026-12-31',
        },
        pubkey: 'ed25519_pk_7fa83b9c02e5b7b1d3f9821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b',
        sig: 'ed25519_sig_c2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9e2b1d3f821a4f5c9',
      });
      setQrInputText(sample);
      setScanResult(api.parseAndVerifyQr(sample));
    } else if (type === 'uidai') {
      const sample = '<?xml version="1.0" encoding="UTF-8"?><PrintLetterBarcodeData uid="XXXXXXXX4819" name="Aarav Sharma" dob="1990-05-14" gender="M" co="S/O Resident" vtc="Mumbai" po="Bandra" dist="Mumbai" subdist="Mumbai" state="Maharashtra" pc="400050" signature="MIIEvgYJKoZIhvcNAQcCoIIEr..." />';
      setQrInputText(sample);
      setScanResult(api.parseAndVerifyQr(sample));
    } else {
      const sample = JSON.stringify({
        suraksha_certified: true,
        pass_id: 'PASS_TAMPERED_0000',
        claim: {
          doc_type: 'aadhaar',
          holder: 'Unauthorized User',
          masked_id: 'XXXX-XXXX-0000',
          recipient: 'Malicious Kiosk',
          purpose: 'hotel_checkin',
          valid_until: '2020-01-01',
        },
        pubkey: 'ed25519_pk_invalid_key_string',
        sig: 'ed25519_sig_tampered_bytes',
      });
      setQrInputText(sample);
      setScanResult(api.parseAndVerifyQr(sample));
    }
  };

  const handleUpdateRedaction = (docType: 'aadhaar' | 'pan' | 'driving_license', recipient: string) => {
    setRedactorDocType(docType);
    setRedactorRecipient(recipient);
    setRedactedDoc(api.redactDocumentImage(docType, recipient));
  };

  // 10-Minute Biometric Auto-Relock Timer Effect
  useEffect(() => {
    let interval: any = null;
    if (unlockTimerActive && unlockSecondsLeft > 0) {
      interval = setInterval(() => {
        setUnlockSecondsLeft((prev) => {
          if (prev <= 1) {
            setUnlockTimerActive(false);
            Alert.alert(
              '🔒 Biometrics Auto-Relocked',
              'The 10-minute temporary unlock window has expired. Your Aadhaar biometrics are now locked and protected against AePS banking fraud.'
            );
            return 600;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [unlockTimerActive, unlockSecondsLeft]);

  const handleStartUnlockTimer = () => {
    setUnlockSecondsLeft(600);
    setUnlockTimerActive(true);
    Alert.alert(
      '🔓 10-Minute Temporary Window Started',
      'Your biometrics are temporarily open for your bank or SIM verification. A timer of 10:00 is active. You will be alerted before it automatically relocks.'
    );
  };

  const handleManualRelock = () => {
    setUnlockTimerActive(false);
    setUnlockSecondsLeft(600);
    Alert.alert('🔒 Biometrics Re-Locked Immediately', 'Your Aadhaar biometric shield is active and secure.');
  };

  const handleRunScamAnalysis = () => {
    if (!scamInputText.trim()) {
      return Alert.alert('Input Required', 'Please enter suspicious message text or suspect claims.');
    }
    const res = ScamRadarService.analyzeMessage(scamInputText.trim(), scamHeaderInput.trim() || undefined, scamChannel);
    setScamResult(res);
  };

  const handleLoadSampleScam = (type: 'digital_arrest' | 'bescom_apk' | 'challan_apk') => {
    if (type === 'digital_arrest') {
      setScamChannel('video_call');
      setScamHeaderInput('+91 98201 92841 (WhatsApp / Skype Video)');
      const text = 'You are under Digital Arrest by CBI Headquarters and Mumbai Cyber Police. Stay on Skype video call. 16 packets of MDMA narcotics seized in FedEx parcel with your Aadhaar.';
      setScamInputText(text);
      setScamResult(ScamRadarService.analyzeMessage(text, '+91 98201 92841', 'video_call'));
    } else if (type === 'bescom_apk') {
      setScamChannel('sms');
      setScamHeaderInput('VM-BESCOM-OFFICIAL');
      const text = 'Dear consumer, your electricity power will be disconnected tonight at 9:30 PM due to unpaid bill. Immediately download and install BESCOM_update.apk from bit.ly/bescom-pay to update bill.';
      setScamInputText(text);
      setScamResult(ScamRadarService.analyzeMessage(text, 'VM-BESCOM-OFFICIAL', 'sms'));
    } else {
      setScamChannel('sms');
      setScamHeaderInput('+91 88291 00291');
      const text = 'Traffic police e-challan pending for vehicle. Pay fine of Rs 500 or warrant issued. Download app echallan_parivahan.apk to pay.';
      setScamInputText(text);
      setScamResult(ScamRadarService.analyzeMessage(text, '+91 88291 00291', 'sms'));
    }
  };

  const handleScanNow = async () => {
    setScanning(true);
    try {
      const ids = await api.getIdentifiers();
      const activeIds = ids.filter((i) => i.state === 'active').map((i) => i.id);
      if (activeIds.length === 0) {
        Alert.alert('No Active Identifiers', 'Please add and verify an email identifier first.', [
          { text: 'Add Identifier', onPress: () => onNavigate('identities') },
          { text: 'Cancel', style: 'cancel' },
        ]);
        return;
      }
      await api.runScan(activeIds);
      Alert.alert('Scan Dispatched', 'Background workers are querying HIBP and Dark Web intelligence sources.');
      await loadData();
    } catch (err: any) {
      Alert.alert('Scan Failed', err.message);
    } finally {
      setScanning(false);
    }
  };

  const getShieldColor = (status?: string) => {
    switch (status) {
      case 'critical':
        return '#ef4444';
      case 'warning':
        return '#f59e0b';
      case 'secure':
      default:
        return '#10b981';
    }
  };

  const shieldColor = getShieldColor(glance?.shield_status);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Syncing identity shield...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} tintColor="#3b82f6" />}
    >
      {/* Resident Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>🇮🇳 CITIZEN IDENTITY SHIELD</Text>
          <Text style={styles.userName}>{session?.full_name || 'Resident'}</Text>
        </View>
        <TouchableOpacity
          style={[styles.headerScanBtn, scanning && styles.buttonDisabled]}
          onPress={handleScanNow}
          disabled={scanning}
          activeOpacity={0.8}
        >
          {scanning ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.headerScanBtnText}>⚡ Scan Now</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Hero Privacy Health Card */}
      <View style={[styles.heroCard, { borderColor: scoreReport.tierColor }]}>
        <View style={styles.heroTopRow}>
          <View style={[styles.shieldStatusPill, { backgroundColor: `${shieldColor}20`, borderColor: shieldColor }]}>
            <View style={[styles.statusDot, { backgroundColor: shieldColor }]} />
            <Text style={[styles.shieldStatusLabel, { color: shieldColor }]}>
              {glance?.shield_status === 'critical'
                ? 'CRITICAL EXPOSURE'
                : glance?.shield_status === 'warning'
                ? 'POTENTIAL THREAT'
                : 'SHIELD ACTIVE & SECURE'}
            </Text>
          </View>
          <View style={[styles.tierPill, { backgroundColor: `${scoreReport.tierColor}20`, borderColor: scoreReport.tierColor }]}>
            <Text style={[styles.tierPillText, { color: scoreReport.tierColor }]}>{scoreReport.tier}</Text>
          </View>
        </View>

        {/* Center Score Dial Representation */}
        <View style={styles.scoreDialCenter}>
          <View style={[styles.dialCircleOuter, { borderColor: scoreReport.tierColor }]}>
            <Text style={[styles.heroScoreNum, { color: scoreReport.tierColor }]}>{scoreReport.score}</Text>
            <Text style={styles.heroScoreMax}>/ {scoreReport.maxScore}</Text>
          </View>
          <Text style={styles.heroPercentile}>{scoreReport.percentileText}</Text>
        </View>

        {/* Badges Carousel / Subtle Row */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.heroBadgesRow}>
          {scoreReport.badges.map((b) => (
            <View key={b.id} style={[styles.badgeChip, b.unlocked ? styles.badgeChipUnlocked : styles.badgeChipLocked]}>
              <Text style={styles.badgeIcon}>{b.icon}</Text>
              <Text style={[styles.badgeTitle, b.unlocked && styles.badgeTitleUnlocked]}>{b.title}</Text>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* Quick Action Pills (2x2 Grid) */}
      <Text style={styles.sectionHeading}>QUICK ACTIONS</Text>
      <View style={styles.quickGrid}>
        <TouchableOpacity
          style={[styles.quickCard, { borderColor: '#ef4444' }]}
          onPress={() => {
            setScamResult(null);
            setScamInputText('');
            setScamHeaderInput('');
            setScamModalVisible(true);
          }}
          activeOpacity={0.8}
        >
          <Text style={styles.quickIcon}>🚨</Text>
          <Text style={styles.quickTitle}>Scam Radar</Text>
          <Text style={styles.quickSub}>Detect Fake CBI / APKs</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.quickCard, { borderColor: '#38bdf8' }]}
          onPress={() => {
            setScanResult(null);
            setQrInputText('');
            setQrModalVisible(true);
          }}
          activeOpacity={0.8}
        >
          <Text style={styles.quickIcon}>📷</Text>
          <Text style={styles.quickTitle}>Verify QR</Text>
          <Text style={styles.quickSub}>Offline Pass / UIDAI</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.quickCard, { borderColor: unlockTimerActive ? '#f59e0b' : '#10b981' }]}
          onPress={() => {
            if (unlockTimerActive) {
              handleManualRelock();
            } else {
              handleStartUnlockTimer();
            }
          }}
          activeOpacity={0.8}
        >
          <Text style={styles.quickIcon}>{unlockTimerActive ? '🔓' : '⏱️'}</Text>
          <Text style={styles.quickTitle}>
            {unlockTimerActive ? 'Relock Now' : 'Auto-Relock'}
          </Text>
          <Text style={[styles.quickSub, unlockTimerActive && { color: '#f59e0b', fontWeight: '700' }]}>
            {unlockTimerActive
              ? `${Math.floor(unlockSecondsLeft / 60)}:${(unlockSecondsLeft % 60).toString().padStart(2, '0')} Left`
              : '10-Min KYC Window'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.quickCard, { borderColor: '#818cf8' }]}
          onPress={() => onNavigate('vault')}
          activeOpacity={0.8}
        >
          <Text style={styles.quickIcon}>🇮🇳</Text>
          <Text style={styles.quickTitle}>Masked Pass</Text>
          <Text style={styles.quickSub}>UIDAI DPDP Compliant</Text>
        </TouchableOpacity>
      </View>

      {/* Urgent Breach Alert Banner (if present) */}
      {glance?.urgent_alert && (
        <TouchableOpacity
          style={styles.urgentCard}
          onPress={() => onNavigate('incidents')}
          activeOpacity={0.8}
        >
          <View style={styles.urgentHeader}>
            <Text style={styles.urgentBadge}>🚨 URGENT ACTION REQUIRED</Text>
            <Text style={styles.urgentScore}>Score: {glance.urgent_alert.priority_score}</Text>
          </View>
          <Text style={styles.urgentTitle}>{glance.urgent_alert.title}</Text>
          <Text style={styles.urgentSub}>Tap to review exposed fields and take protective action →</Text>
        </TouchableOpacity>
      )}

      {/* Key Metrics 2x2 Grid */}
      <Text style={styles.sectionHeading}>SECURITY TELEMETRY</Text>
      <View style={styles.metricsGrid}>
        <TouchableOpacity
          style={styles.metricCard}
          onPress={() => onNavigate('identities')}
          activeOpacity={0.8}
        >
          <Text style={styles.metricNumber}>{glance?.active_monitored_count ?? 1}</Text>
          <Text style={styles.metricLabel}>Monitored IDs</Text>
          <Text style={styles.metricFooter}>Manage →</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.metricCard}
          onPress={() => onNavigate('incidents')}
          activeOpacity={0.8}
        >
          <Text style={[styles.metricNumber, { color: glance?.active_incidents ? '#ef4444' : '#10b981' }]}>
            {glance?.active_incidents ?? 0}
          </Text>
          <Text style={styles.metricLabel}>Threats Detected</Text>
          <Text style={[styles.metricFooter, { color: glance?.active_incidents ? '#ef4444' : '#10b981' }]}>
            {glance?.active_incidents ? 'Review Incidents →' : 'Zero Breaches ✓'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.metricCard}
          onPress={() => onNavigate('vault')}
          activeOpacity={0.8}
        >
          <Text style={[styles.metricNumber, { color: '#10b981', fontSize: 18 }]}>
            {glance?.biometrics_locked ? 'LOCKED' : 'UNLOCKED'}
          </Text>
          <Text style={styles.metricLabel}>Biometric Shield</Text>
          <Text style={styles.metricFooter}>AePS Protection →</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.metricCard}
          onPress={() => onNavigate('more')}
          activeOpacity={0.8}
        >
          <Text style={[styles.metricNumber, { color: '#38bdf8' }]}>
            1
          </Text>
          <Text style={styles.metricLabel}>Family Protected</Text>
          <Text style={styles.metricFooter}>Family Hub →</Text>
        </TouchableOpacity>
      </View>

      {/* Active Masked ID Card */}
      <View style={styles.maskedIdCard}>
        <View style={styles.maskedIdHeader}>
          <Text style={styles.maskedIdBadge}>GOVERNMENT OF INDIA • MASKED AADHAAR</Text>
          <Text style={styles.maskedIdStatus}>🔒 VERIFIED</Text>
        </View>
        <View style={styles.maskedIdBody}>
          <Text style={styles.maskedIdNumber}>████  ████  4819</Text>
          <Text style={styles.maskedIdDesc}>
            Offline Redacted Pass ready for hotels and rental verification under UIDAI Circular 2022.
          </Text>
          <TouchableOpacity
            style={styles.vaultPassBtn}
            onPress={() => onNavigate('vault')}
            activeOpacity={0.8}
          >
            <Text style={styles.vaultPassBtnText}>Open Identity Vault & Generate Pass →</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Compliance / Privacy Guarantee */}
      <View style={styles.trustFooter}>
        <Text style={styles.trustTitle}>🔒 Privacy & Architecture Guarantees</Text>
        <Text style={styles.trustText}>
          • Zero direct scraping of UIDAI or Income Tax portals.{'\n'}
          • HMAC-SHA256 blind indexing for zero-knowledge search.{'\n'}
          • AES-256-GCM envelope encryption for all resident identifiers.
        </Text>
      </View>

      {/* Feature 3: Universal Offline QR Scanner Modal */}
      <Modal visible={qrModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <ScrollView contentContainerStyle={styles.modalScroll}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Universal Offline Identity QR Scanner</Text>
              <Text style={styles.modalSub}>
                Zero-cloud verifier for Suraksha Certified Passes (Ed25519) and UIDAI 2048-bit Secure QR codes.
              </Text>

              <Text style={styles.inputLabel}>Select Test Payload or Paste QR String:</Text>
              <View style={{ flexDirection: 'row', gap: 6, marginBottom: 10 }}>
                <TouchableOpacity
                  style={[styles.testPayloadBtn, { borderColor: '#10b981' }]}
                  onPress={() => handleLoadSampleQr('pass')}
                >
                  <Text style={[styles.testPayloadText, { color: '#34d399' }]}>Suraksha Pass</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.testPayloadBtn, { borderColor: '#38bdf8' }]}
                  onPress={() => handleLoadSampleQr('uidai')}
                >
                  <Text style={[styles.testPayloadText, { color: '#38bdf8' }]}>UIDAI QR</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.testPayloadBtn, { borderColor: '#ef4444' }]}
                  onPress={() => handleLoadSampleQr('tampered')}
                >
                  <Text style={[styles.testPayloadText, { color: '#f87171' }]}>Tampered QR</Text>
                </TouchableOpacity>
              </View>

              <TextInput
                style={[styles.input, { height: 80, textAlignVertical: 'top', fontFamily: 'monospace', fontSize: 11 }]}
                multiline
                placeholder="Scan or paste raw QR payload..."
                placeholderTextColor="#64748b"
                value={qrInputText}
                onChangeText={setQrInputText}
              />

              <TouchableOpacity
                style={[styles.actionBtn, { backgroundColor: '#0284c7', borderColor: '#38bdf8', marginBottom: 12 }]}
                onPress={handleRunQrScan}
              >
                <Text style={[styles.actionBtnText, { color: '#ffffff' }]}>🔍 Verify Signature Offline</Text>
              </TouchableOpacity>

              {/* Verification Report */}
              {scanResult && (
                <View style={styles.scanResultCard}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <Text style={{ fontSize: 13, fontWeight: '700', color: '#f8fafc' }}>{scanResult.title}</Text>
                    <Text
                      style={[
                        styles.verifyPill,
                        scanResult.verified ? styles.verifyPillValid : styles.verifyPillInvalid,
                      ]}
                    >
                      {scanResult.verified ? '✓ VERIFIED AUTHENTIC' : '❌ UNVERIFIED / TAMPERED'}
                    </Text>
                  </View>

                  <Text style={styles.securityAuditText}>{scanResult.securityAudit}</Text>

                  <View style={styles.extractedDetailsTable}>
                    {Object.entries(scanResult.extractedDetails).map(([k, v]) => (
                      <View key={k} style={styles.extractedRow}>
                        <Text style={styles.extractedKey}>{k}:</Text>
                        <Text style={styles.extractedVal}>{v}</Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={styles.btnSecondary}
                  onPress={() => setQrModalVisible(false)}
                >
                  <Text style={styles.btnSecondaryText}>Close</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Feature C: Digital Arrest & Malicious APK Scam Radar Modal */}
      <Modal visible={scamModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <ScrollView contentContainerStyle={styles.modalScroll}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Scam & Digital Arrest Threat Radar</Text>
              <Text style={styles.modalSub}>
                Zero-cloud heuristic scanner for fake police video calls, WhatsApp extortion, and APK phishing links.
              </Text>

              <Text style={styles.inputLabel}>Test Realistic Attack Scenarios:</Text>
              <View style={{ flexDirection: 'row', gap: 6, marginBottom: 10 }}>
                <TouchableOpacity
                  style={[styles.testPayloadBtn, { borderColor: '#ef4444' }]}
                  onPress={() => handleLoadSampleScam('digital_arrest')}
                >
                  <Text style={[styles.testPayloadText, { color: '#f87171' }]}>CBI Video Call</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.testPayloadBtn, { borderColor: '#f59e0b' }]}
                  onPress={() => handleLoadSampleScam('bescom_apk')}
                >
                  <Text style={[styles.testPayloadText, { color: '#fbbf24' }]}>Power Cut APK</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.testPayloadBtn, { borderColor: '#38bdf8' }]}
                  onPress={() => handleLoadSampleScam('challan_apk')}
                >
                  <Text style={[styles.testPayloadText, { color: '#38bdf8' }]}>Challan APK</Text>
                </TouchableOpacity>
              </View>

              <Text style={styles.inputLabel}>Channel & Sender Header / Number:</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 8 }}>
                <TextInput
                  style={[styles.input, { flex: 1 }]}
                  placeholder="e.g. VM-BESCOM or +91 98201..."
                  placeholderTextColor="#64748b"
                  value={scamHeaderInput}
                  onChangeText={setScamHeaderInput}
                />
              </View>

              <Text style={styles.inputLabel}>Message Text / Suspect Claims:</Text>
              <TextInput
                style={[styles.input, { height: 70, textAlignVertical: 'top' }]}
                multiline
                placeholder="Paste suspicious SMS text or Skype / video call transcript..."
                placeholderTextColor="#64748b"
                value={scamInputText}
                onChangeText={setScamInputText}
              />

              <TouchableOpacity
                style={[styles.actionBtn, { backgroundColor: '#b91c1c', borderColor: '#ef4444', marginBottom: 12 }]}
                onPress={handleRunScamAnalysis}
              >
                <Text style={[styles.actionBtnText, { color: '#ffffff' }]}>🔍 Scan for Extortion & Phishing</Text>
              </TouchableOpacity>

              {/* Analysis Result */}
              {scamResult && (
                <View style={[styles.scanResultCard, scamResult.isScam ? { borderColor: '#ef4444' } : { borderColor: '#10b981' }]}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <Text style={{ fontSize: 13, fontWeight: '700', color: '#f8fafc' }}>
                      {scamResult.scamCategory.toUpperCase().replace(/_/g, ' ')}
                    </Text>
                    <Text style={[styles.verifyPill, scamResult.isScam ? styles.verifyPillInvalid : styles.verifyPillValid]}>
                      {scamResult.threatLevel.toUpperCase()}
                    </Text>
                  </View>

                  {scamResult.isScam && (
                    <View style={{ backgroundColor: '#450a0a', padding: 8, borderRadius: 6, marginBottom: 8, borderWidth: 1, borderColor: '#ef4444' }}>
                      <Text style={{ fontSize: 11, fontWeight: '800', color: '#fca5a5', marginBottom: 4 }}>
                        🚨 EXTORTION / PHISHING WARNING (Confidence: {Math.round(scamResult.confidenceScore * 100)}%)
                      </Text>
                      {scamResult.matchedIndicators.map((ind, i) => (
                        <Text key={i} style={{ fontSize: 10, color: '#fee2e2' }}>• {ind}</Text>
                      ))}
                    </View>
                  )}

                  <View style={{ backgroundColor: '#0c1a2f', padding: 8, borderRadius: 6, marginBottom: 8 }}>
                    <Text style={{ fontSize: 10, fontWeight: '800', color: '#60a5fa', marginBottom: 2 }}>OFFICIAL MHA GUIDANCE:</Text>
                    <Text style={{ fontSize: 10, color: '#93c5fd', lineHeight: 14 }}>{scamResult.mhaOfficialAdvisory}</Text>
                  </View>

                  {scamResult.isScam && (
                    <TouchableOpacity
                      style={[styles.actionBtn, { backgroundColor: '#1e293b', borderColor: '#475569', marginTop: 4 }]}
                      onPress={() => {
                        antiTamperShield.safeCopyToClipboard(scamResult.prefilledFirDraft, 'Complaint Draft');
                        Alert.alert('Complaint Draft Copied', '1930 / cybercrime.gov.in complaint draft copied to clipboard.');
                      }}
                    >
                      <Text style={styles.actionBtnText}>📋 Copy 1930 Police Complaint Draft</Text>
                    </TouchableOpacity>
                  )}
                </View>
              )}

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={styles.btnSecondary}
                  onPress={() => setScamModalVisible(false)}
                >
                  <Text style={styles.btnSecondaryText}>Close</Text>
                </TouchableOpacity>
              </View>
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
  centerContainer: {
    flex: 1,
    backgroundColor: '#090d16',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    color: '#94a3b8',
    marginTop: 12,
    fontSize: 14,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    marginTop: 4,
  },
  greeting: {
    fontSize: 11,
    color: '#60a5fa',
    fontWeight: '800',
    letterSpacing: 1,
  },
  userName: {
    fontSize: 22,
    fontWeight: '800',
    color: '#f8fafc',
    marginTop: 2,
  },
  headerScanBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 10,
    shadowColor: '#2563eb',
    shadowOpacity: 0.35,
    shadowRadius: 5,
    elevation: 3,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  headerScanBtnText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 13,
  },
  heroCard: {
    backgroundColor: '#0c1a2f',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1.5,
    marginBottom: 20,
  },
  heroTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  shieldStatusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 16,
    borderWidth: 1,
    gap: 6,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  shieldStatusLabel: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  tierPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  tierPillText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  scoreDialCenter: {
    alignItems: 'center',
    marginVertical: 6,
  },
  dialCircleOuter: {
    width: 130,
    height: 130,
    borderRadius: 65,
    borderWidth: 4,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    marginBottom: 10,
  },
  heroScoreNum: {
    fontSize: 38,
    fontWeight: '900',
    letterSpacing: -1,
  },
  heroScoreMax: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748b',
    marginTop: -2,
  },
  heroPercentile: {
    fontSize: 12,
    color: '#93c5fd',
    fontWeight: '600',
    textAlign: 'center',
  },
  heroBadgesRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 14,
    paddingVertical: 2,
  },
  sectionHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: '#64748b',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 10,
    marginLeft: 2,
  },
  quickGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 20,
  },
  quickCard: {
    width: '48.5%',
    backgroundColor: '#111827',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
  },
  quickIcon: {
    fontSize: 22,
    marginBottom: 6,
  },
  quickTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 2,
  },
  quickSub: {
    fontSize: 10,
    color: '#94a3b8',
    fontWeight: '500',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 20,
  },
  metricCard: {
    width: '48.5%',
    backgroundColor: '#111827',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  metricNumber: {
    fontSize: 24,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 2,
  },
  metricLabel: {
    fontSize: 11,
    color: '#94a3b8',
    marginBottom: 6,
    fontWeight: '500',
  },
  metricFooter: {
    fontSize: 11,
    color: '#38bdf8',
    fontWeight: '700',
  },
  maskedIdCard: {
    backgroundColor: '#0c1a2f',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e3a8a',
    marginBottom: 20,
  },
  maskedIdHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  maskedIdBadge: {
    fontSize: 9,
    fontWeight: '800',
    color: '#60a5fa',
    letterSpacing: 0.8,
  },
  maskedIdStatus: {
    fontSize: 9,
    fontWeight: '800',
    color: '#34d399',
    backgroundColor: '#064e3b',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  maskedIdBody: {
    marginTop: 4,
  },
  maskedIdNumber: {
    fontSize: 22,
    fontWeight: '800',
    color: '#38bdf8',
    fontFamily: 'monospace',
    letterSpacing: 2,
    marginBottom: 6,
  },
  maskedIdDesc: {
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 16,
    marginBottom: 12,
  },
  vaultPassBtn: {
    backgroundColor: '#1e293b',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#38bdf8',
  },
  vaultPassBtnText: {
    color: '#38bdf8',
    fontWeight: '700',
    fontSize: 12,
  },
  urgentCard: {
    backgroundColor: '#450a0a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#ef4444',
    padding: 16,
    marginBottom: 16,
  },
  urgentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  urgentBadge: {
    color: '#f87171',
    fontWeight: '700',
    fontSize: 11,
    letterSpacing: 0.5,
  },
  urgentScore: {
    color: '#fca5a5',
    fontSize: 12,
    fontWeight: '600',
  },
  urgentTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fef2f2',
    marginBottom: 4,
  },
  urgentSub: {
    fontSize: 12,
    color: '#fca5a5',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  statNumber: {
    fontSize: 26,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 8,
  },
  statLink: {
    fontSize: 12,
    color: '#3b82f6',
    fontWeight: '600',
  },
  actionCard: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
    marginBottom: 16,
  },
  actionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  actionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f8fafc',
  },
  actionStatus: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  actionDesc: {
    fontSize: 13,
    color: '#94a3b8',
    lineHeight: 18,
    marginBottom: 12,
  },
  actionBtn: {
    backgroundColor: '#1f2937',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#374151',
  },
  actionBtnText: {
    color: '#38bdf8',
    fontWeight: '600',
    fontSize: 13,
  },
  trustFooter: {
    backgroundColor: '#0d1322',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  trustTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748b',
    marginBottom: 6,
  },
  trustText: {
    fontSize: 11,
    color: '#475569',
    lineHeight: 16,
  },
  langBarContainer: {
    marginBottom: 16,
  },
  langScroll: {
    paddingVertical: 4,
    gap: 8,
  },
  langChip: {
    backgroundColor: '#111827',
    borderWidth: 1,
    borderColor: '#374151',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  langChipActive: {
    backgroundColor: '#1d4ed8',
    borderColor: '#3b82f6',
  },
  langChipText: {
    fontSize: 12,
    color: '#94a3b8',
    fontWeight: '600',
  },
  langChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  bhashiniBanner: {
    backgroundColor: '#0c1a2f',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#1e3a8a',
    padding: 10,
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  bhashiniBannerTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#60a5fa',
    marginBottom: 2,
  },
  bhashiniBannerText: {
    fontSize: 11,
    color: '#93c5fd',
    lineHeight: 15,
  },
  audioVoiceBtn: {
    backgroundColor: '#1e3a8a',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  audioVoiceBtnText: {
    fontSize: 11,
    color: '#bfdbfe',
    fontWeight: '700',
  },
  redactorTab: {
    flex: 1,
    backgroundColor: '#111827',
    borderWidth: 1,
    borderColor: '#374151',
    paddingVertical: 6,
    borderRadius: 6,
    alignItems: 'center',
  },
  redactorTabActive: {
    backgroundColor: '#0369a1',
    borderColor: '#38bdf8',
  },
  redactorTabText: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '600',
  },
  redactorTabTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  canvasMockBox: {
    backgroundColor: '#090d16',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1e293b',
    overflow: 'hidden',
    marginTop: 8,
  },
  canvasHeaderBar: {
    backgroundColor: '#0f172a',
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  canvasHeaderTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: '#f8fafc',
  },
  canvasMaskBadge: {
    fontSize: 9,
    fontWeight: '800',
    color: '#38bdf8',
    backgroundColor: '#082f49',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  blackRedactionBox: {
    backgroundColor: '#000000',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#334155',
  },
  blackRedactionText: {
    color: '#e2e8f0',
    fontSize: 11,
    fontWeight: '900',
    fontFamily: 'monospace',
    letterSpacing: 1,
  },
  watermarkBannerBox: {
    marginTop: 10,
    padding: 6,
    backgroundColor: 'rgba(234, 88, 12, 0.1)',
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#ea580c',
  },
  watermarkBannerText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#fb923c',
    textAlign: 'center',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    padding: 16,
  },
  modalScroll: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  modalContent: {
    backgroundColor: '#0f172a',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#1e293b',
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
  },
  input: {
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    padding: 10,
    color: '#f8fafc',
    fontSize: 13,
    marginBottom: 10,
  },
  testPayloadBtn: {
    flex: 1,
    backgroundColor: '#111827',
    borderWidth: 1,
    paddingVertical: 6,
    borderRadius: 6,
    alignItems: 'center',
  },
  testPayloadText: {
    fontSize: 11,
    fontWeight: '700',
  },
  scanResultCard: {
    backgroundColor: '#090d16',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 12,
    marginBottom: 12,
  },
  verifyPill: {
    fontSize: 10,
    fontWeight: '800',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  verifyPillValid: {
    backgroundColor: '#064e3b',
    color: '#6ee7b7',
  },
  verifyPillInvalid: {
    backgroundColor: '#7f1d1d',
    color: '#fca5a5',
  },
  securityAuditText: {
    fontSize: 11,
    color: '#cbd5e1',
    marginBottom: 8,
    lineHeight: 15,
  },
  extractedDetailsTable: {
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    paddingTop: 8,
    gap: 4,
  },
  extractedRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  extractedKey: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '600',
  },
  extractedVal: {
    fontSize: 11,
    color: '#f8fafc',
    fontWeight: '600',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 8,
  },
  btnSecondary: {
    backgroundColor: '#1e293b',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnSecondaryText: {
    color: '#cbd5e1',
    fontWeight: '600',
    fontSize: 13,
  },
  cardScore: {
    backgroundColor: '#0c1a2f',
    padding: 16,
    borderRadius: 16,
    borderWidth: 1.5,
    marginBottom: 16,
  },
  scoreHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  scoreSubTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.8,
  },
  scoreNumber: {
    fontSize: 34,
    fontWeight: '900',
  },
  scoreMax: {
    fontSize: 16,
    fontWeight: '600',
    color: '#64748b',
  },
  scoreTierPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  scoreTierText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  scorePercentileText: {
    fontSize: 12,
    color: '#93c5fd',
    marginBottom: 10,
  },
  badgesScroll: {
    flexDirection: 'row',
    gap: 8,
    paddingVertical: 4,
  },
  badgeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
  badgeChipUnlocked: {
    backgroundColor: '#1e293b',
    borderColor: '#38bdf8',
  },
  badgeChipLocked: {
    backgroundColor: '#0f172a',
    borderColor: '#334155',
    opacity: 0.5,
  },
  badgeIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  badgeTitle: {
    fontSize: 11,
    color: '#64748b',
    fontWeight: '700',
  },
  badgeTitleUnlocked: {
    color: '#f8fafc',
  },
  timerActiveBox: {
    backgroundColor: '#451a03',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#f59e0b',
    marginTop: 8,
  },
  timerActiveNotice: {
    fontSize: 11,
    color: '#fde68a',
    marginBottom: 6,
    lineHeight: 15,
  },
  timerClockText: {
    fontSize: 30,
    fontWeight: '900',
    color: '#f59e0b',
    fontFamily: 'monospace',
    textAlign: 'center',
    marginBottom: 8,
  },
  relockImmediateBtn: {
    backgroundColor: '#b45309',
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  relockImmediateBtnText: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 12,
  },
  researchBannerCard: {
    backgroundColor: '#0c1a30',
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1d4ed8',
  },
  researchBannerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  researchBannerIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  researchBannerTag: {
    fontSize: 9,
    fontWeight: '800',
    color: '#60a5fa',
    letterSpacing: 1,
  },
  livePulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10b981',
  },
  researchBannerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f8fafc',
    marginTop: 2,
  },
  researchBannerSub: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  researchBannerArrow: {
    fontSize: 18,
    fontWeight: '700',
    color: '#3b82f6',
    marginLeft: 8,
  },
});
