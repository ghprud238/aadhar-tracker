import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { api } from '../services/api';
import { Identifier } from '../types';
import {
  validateAadhaar,
  validatePan,
  validateDrivingLicense,
  validateVoterId,
  validatePassport,
} from '../services/verhoeff';

type SupportedDocType = Identifier['type'];

const DOC_TYPE_META: Record<SupportedDocType, { label: string; icon: string; placeholder: string; helper: string }> = {
  aadhaar: {
    label: 'Aadhaar',
    icon: '🇮🇳',
    placeholder: 'e.g. 5489 1234 5678',
    helper: '12-digit number verified on-device via Verhoeff D5 algorithm.',
  },
  pan: {
    label: 'PAN Card',
    icon: '💳',
    placeholder: 'e.g. ABCDE1234F',
    helper: '10-character PAN checked against Income Tax Dept schema.',
  },
  driving_license: {
    label: 'Driving License',
    icon: '🚗',
    placeholder: 'e.g. MH-12-2015-0012345',
    helper: 'Parivahan format: State (2) + RTO (2) + Year (4) + Digits (7).',
  },
  voter_id: {
    label: 'Voter ID (EPIC)',
    icon: '🗳️',
    placeholder: 'e.g. ABC1234567',
    helper: 'Election Commission of India 10-char alphanumeric format.',
  },
  passport: {
    label: 'Passport',
    icon: '✈️',
    placeholder: 'e.g. Z1234567',
    helper: 'Ministry of External Affairs 8-char Indian passport format.',
  },
  phone: {
    label: 'Mobile Phone',
    icon: '📱',
    placeholder: 'e.g. 9876543210',
    helper: '10-digit mobile number for SIM protection.',
  },
  email: {
    label: 'Email',
    icon: '✉️',
    placeholder: 'e.g. resident@example.in',
    helper: 'Used for darkweb breach monitoring and data leak alerts.',
  },
};

export const IdentitiesScreen: React.FC = () => {
  const [identifiers, setIdentifiers] = useState<Identifier[]>([]);
  const [loading, setLoading] = useState(true);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [selectedType, setSelectedType] = useState<SupportedDocType>('aadhaar');
  const [inputValue, setInputValue] = useState('');
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [challengeToken, setChallengeToken] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [importingDigiLocker, setImportingDigiLocker] = useState(false);

  const fetchIdentifiers = async () => {
    try {
      const data = await api.getIdentifiers();
      setIdentifiers(data);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdentifiers();
  }, []);

  const handleDigiLockerImport = async () => {
    setImportingDigiLocker(true);
    try {
      const imported = await api.importFromDigiLocker();
      await fetchIdentifiers();
      if (imported.length === 0) {
        Alert.alert(
          'DigiLocker Sync Complete',
          'All verified government credentials from DigiLocker are already present in your local vault.'
        );
      } else {
        Alert.alert(
          '🏛️ DigiLocker Import Successful',
          `Successfully imported ${imported.length} verified government credentials into your on-device hardware vault:\n` +
          imported.map((i) => `• ${DOC_TYPE_META[i.type]?.icon || '📄'} ${DOC_TYPE_META[i.type]?.label || i.type}: ${i.masked_value}`).join('\n') +
          '\n\nZero cloud servers were contacted. Keys remain in local Secure Enclave.'
        );
      }
    } catch (err: any) {
      Alert.alert('DigiLocker Sync Error', err.message);
    } finally {
      setImportingDigiLocker(false);
    }
  };

  const handleAddIdentifier = async () => {
    const val = inputValue.trim();
    if (!val) {
      return Alert.alert('Input Required', `Please enter a valid ${DOC_TYPE_META[selectedType].label}.`);
    }

    // Client-side quick validation for better UX
    if (selectedType === 'aadhaar') {
      const res = validateAadhaar(val);
      if (!res.valid) return Alert.alert('Invalid Aadhaar', res.error);
    } else if (selectedType === 'pan') {
      const res = validatePan(val);
      if (!res.valid) return Alert.alert('Invalid PAN', res.error);
    } else if (selectedType === 'driving_license') {
      const res = validateDrivingLicense(val);
      if (!res.valid) return Alert.alert('Invalid Driving License', res.error);
    } else if (selectedType === 'voter_id') {
      const res = validateVoterId(val);
      if (!res.valid) return Alert.alert('Invalid Voter ID', res.error);
    } else if (selectedType === 'passport') {
      const res = validatePassport(val);
      if (!res.valid) return Alert.alert('Invalid Passport', res.error);
    } else if (selectedType === 'email') {
      if (!val.includes('@') || !val.includes('.')) {
        return Alert.alert('Invalid Email', 'Please provide a valid email address.');
      }
    } else if (selectedType === 'phone') {
      if (!/^\d{10}$/.test(val.replace(/\D/g, ''))) {
        return Alert.alert('Invalid Phone', 'Please provide a 10-digit mobile number.');
      }
    }

    setSubmitting(true);
    try {
      const created = await api.addIdentifier(selectedType, val);
      setInputValue('');
      setAddModalVisible(false);

      if (created.state === 'pending_verification') {
        Alert.alert(
          'Identity Added',
          `Verification challenge sent to ${created.masked_value}. Complete verification to activate breach scanning.`
        );
        await fetchIdentifiers();
        startVerificationFlow(created.id);
      } else {
        Alert.alert(
          'Identity Enrolled & Protected',
          `${DOC_TYPE_META[created.type]?.label || created.type} (${created.masked_value}) has been validated on-device and enrolled into your local protection vault.`
        );
        await fetchIdentifiers();
      }
    } catch (err: any) {
      Alert.alert('Failed to Add', err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const startVerificationFlow = async (id: string) => {
    try {
      const res = await api.requestVerification(id);
      setVerifyingId(id);
      if (res.demo_token) {
        setChallengeToken(res.demo_token);
      }
    } catch (err: any) {
      Alert.alert('Challenge Error', err.message);
    }
  };

  const handleCompleteVerification = async () => {
    if (!verifyingId || !challengeToken) return;
    setSubmitting(true);
    try {
      await api.completeVerification(verifyingId, challengeToken.trim());
      Alert.alert('Success', 'Identifier verified! Active monitoring and breach alerts enabled.');
      setVerifyingId(null);
      setChallengeToken('');
      await fetchIdentifiers();
    } catch (err: any) {
      Alert.alert('Verification Failed', err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleMonitoring = async (ident: Identifier) => {
    try {
      if (ident.state === 'active') {
        await api.pauseIdentifier(ident.id);
      } else if (ident.state === 'paused') {
        await api.resumeIdentifier(ident.id);
      }
      await fetchIdentifiers();
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleDeleteIdentifier = (id: string, masked: string) => {
    Alert.alert(
      'Remove Identifier',
      `Stop monitoring and erase blind index for ${masked}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteIdentifier(id);
              await fetchIdentifiers();
            } catch (err: any) {
              Alert.alert('Error', err.message);
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={{ flex: 1, paddingRight: 8 }}>
          <Text style={styles.title}>Identity Vault</Text>
          <Text style={styles.subtitle}>Multi-document hardware vault & leak monitoring</Text>
        </View>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => setAddModalVisible(true)}
        >
          <Text style={styles.addBtnText}>+ Add</Text>
        </TouchableOpacity>
      </View>

      {/* Quick Actions Row: DigiLocker Direct Import */}
      <TouchableOpacity
        style={styles.digiLockerBanner}
        onPress={handleDigiLockerImport}
        disabled={importingDigiLocker}
      >
        <Text style={styles.digiLockerIcon}>🏛️</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.digiLockerTitle}>DigiLocker Direct Import</Text>
          <Text style={styles.digiLockerSubtitle}>
            1-tap import of verified Driving License & Voter ID directly into device enclave.
          </Text>
        </View>
        {importingDigiLocker ? (
          <ActivityIndicator size="small" color="#38bdf8" />
        ) : (
          <View style={styles.digiLockerBadge}>
            <Text style={styles.digiLockerBadgeText}>IMPORT</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Advisory Pill */}
      <View style={styles.advisoryCard}>
        <Text style={styles.advisoryIcon}>🔒</Text>
        <Text style={styles.advisoryText}>
          Zero-Knowledge & DPDP Act Invariant: Raw 12-digit Aadhaar numbers and credentials never leave your
          phone. Masked tokens and HMAC-SHA256 blind indexes are computed entirely on-device.
        </Text>
      </View>

      {identifiers.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>📭</Text>
          <Text style={styles.emptyTitle}>No Identifiers Enrolled</Text>
          <Text style={styles.emptySub}>Add an identity document or import from DigiLocker to activate breach protection.</Text>
          <TouchableOpacity style={styles.emptyBtn} onPress={() => setAddModalVisible(true)}>
            <Text style={styles.emptyBtnText}>Add Your First Document</Text>
          </TouchableOpacity>
        </View>
      ) : (
        identifiers.map((item) => {
          const meta = DOC_TYPE_META[item.type] || {
            label: item.type.toUpperCase(),
            icon: '📄',
          };
          return (
            <View key={item.id} style={styles.itemCard}>
              <View style={styles.itemHeader}>
                <View style={styles.itemTypePill}>
                  <Text style={styles.itemTypeIcon}>{meta.icon}</Text>
                  <Text style={styles.itemTypeValue}>{meta.label}</Text>
                </View>
                <View
                  style={[
                    styles.statusBadge,
                    item.state === 'active' && styles.statusActive,
                    item.state === 'pending_verification' && styles.statusPending,
                    item.state === 'paused' && styles.statusPaused,
                  ]}
                >
                  <Text style={styles.statusText}>{item.state.replace('_', ' ').toUpperCase()}</Text>
                </View>
              </View>

              <Text style={styles.maskedValue}>{item.masked_value}</Text>
              <Text style={styles.metaText}>
                Enrolled: {new Date(item.created_at).toLocaleDateString()}
                {item.verified_at ? ` • Verified: ${new Date(item.verified_at).toLocaleDateString()}` : ''}
              </Text>

              <View style={styles.itemActions}>
                {item.state === 'pending_verification' ? (
                  <TouchableOpacity
                    style={[styles.btnAction, styles.btnVerify]}
                    onPress={() => startVerificationFlow(item.id)}
                  >
                    <Text style={styles.btnVerifyText}>Verify OTP / Token</Text>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity
                    style={[styles.btnAction, styles.btnToggle]}
                    onPress={() => handleToggleMonitoring(item)}
                  >
                    <Text style={styles.btnToggleText}>
                      {item.state === 'active' ? 'Pause Shield' : 'Resume Shield'}
                    </Text>
                  </TouchableOpacity>
                )}

                <TouchableOpacity
                  style={[styles.btnAction, styles.btnDelete]}
                  onPress={() => handleDeleteIdentifier(item.id, item.masked_value)}
                >
                  <Text style={styles.btnDeleteText}>Remove</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })
      )}

      {/* Add Identifier Modal */}
      <Modal visible={addModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Enroll Government Document / ID</Text>
            <Text style={styles.modalSub}>
              Select document type. Raw numbers are validated on-device and immediately masked.
            </Text>

            {/* Document Type Selector Chips */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
              {(['aadhaar', 'pan', 'driving_license', 'voter_id', 'passport', 'email', 'phone'] as SupportedDocType[]).map((t) => {
                const isSelected = selectedType === t;
                const m = DOC_TYPE_META[t];
                return (
                  <TouchableOpacity
                    key={t}
                    style={[styles.docChip, isSelected && styles.docChipActive]}
                    onPress={() => {
                      setSelectedType(t);
                      setInputValue('');
                    }}
                  >
                    <Text style={styles.docChipIcon}>{m.icon}</Text>
                    <Text style={[styles.docChipText, isSelected && styles.docChipTextActive]}>
                      {m.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            <Text style={styles.helperText}>{DOC_TYPE_META[selectedType]?.helper}</Text>

            <TextInput
              style={styles.input}
              placeholder={DOC_TYPE_META[selectedType]?.placeholder}
              placeholderTextColor="#64748b"
              autoCapitalize={selectedType === 'pan' || selectedType === 'voter_id' || selectedType === 'passport' || selectedType === 'driving_license' ? 'characters' : 'none'}
              keyboardType={selectedType === 'aadhaar' || selectedType === 'phone' ? 'number-pad' : (selectedType === 'email' ? 'email-address' : 'default')}
              value={inputValue}
              onChangeText={setInputValue}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.btnSecondary}
                onPress={() => setAddModalVisible(false)}
                disabled={submitting}
              >
                <Text style={styles.btnSecondaryText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.btnPrimary}
                onPress={handleAddIdentifier}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.btnPrimaryText}>Add & Protect</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Verification Challenge Modal */}
      <Modal visible={!!verifyingId} animationType="fade" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Verify Ownership</Text>
            <Text style={styles.modalSub}>
              Enter the 6-digit verification code or token sent to your device to prove ownership.
            </Text>
            <TextInput
              style={[styles.input, styles.tokenInput]}
              placeholder="6-digit challenge code"
              placeholderTextColor="#64748b"
              value={challengeToken}
              onChangeText={setChallengeToken}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.btnSecondary}
                onPress={() => setVerifyingId(null)}
                disabled={submitting}
              >
                <Text style={styles.btnSecondaryText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.btnPrimary}
                onPress={handleCompleteVerification}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.btnPrimaryText}>Verify & Activate</Text>
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
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#090d16',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  addBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 8,
  },
  addBtnText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 13,
  },
  digiLockerBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0c2340',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1d4ed8',
    marginBottom: 16,
  },
  digiLockerIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  digiLockerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#93c5fd',
  },
  digiLockerSubtitle: {
    fontSize: 11,
    color: '#bfdbfe',
    marginTop: 2,
    lineHeight: 15,
  },
  digiLockerBadge: {
    backgroundColor: '#1d4ed8',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    marginLeft: 8,
  },
  digiLockerBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: 0.5,
  },
  advisoryCard: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 16,
  },
  advisoryIcon: {
    marginRight: 8,
    fontSize: 16,
  },
  advisoryText: {
    flex: 1,
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 16,
  },
  emptyState: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1f2937',
    marginTop: 20,
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f8fafc',
    marginBottom: 6,
  },
  emptySub: {
    fontSize: 12,
    color: '#94a3b8',
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 18,
  },
  emptyBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  emptyBtnText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 13,
  },
  itemCard: {
    backgroundColor: '#111827',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
    marginBottom: 12,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  itemTypePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  itemTypeIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  itemTypeValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#cbd5e1',
    letterSpacing: 0.5,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusActive: {
    backgroundColor: '#064e3b',
  },
  statusPending: {
    backgroundColor: '#78350f',
  },
  statusPaused: {
    backgroundColor: '#374151',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#f8fafc',
  },
  maskedValue: {
    fontSize: 17,
    fontWeight: '700',
    color: '#f8fafc',
    letterSpacing: 1,
    marginBottom: 4,
    fontFamily: 'monospace',
  },
  metaText: {
    fontSize: 11,
    color: '#64748b',
    marginBottom: 14,
  },
  itemActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: '#1f2937',
    paddingTop: 10,
    gap: 8,
  },
  btnAction: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  btnVerify: {
    backgroundColor: '#2563eb',
  },
  btnVerifyText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '600',
  },
  btnToggle: {
    backgroundColor: '#1e293b',
  },
  btnToggleText: {
    color: '#cbd5e1',
    fontSize: 11,
    fontWeight: '600',
  },
  btnDelete: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
  },
  btnDeleteText: {
    color: '#f87171',
    fontSize: 11,
    fontWeight: '600',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    justifyContent: 'center',
    padding: 16,
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
  chipRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  docChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  docChipActive: {
    backgroundColor: '#1d4ed8',
    borderColor: '#3b82f6',
  },
  docChipIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  docChipText: {
    fontSize: 12,
    color: '#94a3b8',
    fontWeight: '600',
  },
  docChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  helperText: {
    fontSize: 11,
    color: '#38bdf8',
    marginBottom: 10,
    fontStyle: 'italic',
  },
  input: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    padding: 12,
    color: '#f8fafc',
    fontSize: 14,
    marginBottom: 16,
  },
  tokenInput: {
    textAlign: 'center',
    fontSize: 18,
    letterSpacing: 2,
    fontFamily: 'monospace',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  btnSecondary: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#1e293b',
  },
  btnSecondaryText: {
    color: '#cbd5e1',
    fontWeight: '600',
    fontSize: 13,
  },
  btnPrimary: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#2563eb',
    minWidth: 100,
    alignItems: 'center',
  },
  btnPrimaryText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 13,
  },
});
