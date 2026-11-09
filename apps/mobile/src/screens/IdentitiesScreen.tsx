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

export const IdentitiesScreen: React.FC = () => {
  const [identifiers, setIdentifiers] = useState<Identifier[]>([]);
  const [loading, setLoading] = useState(true);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [emailInput, setEmailInput] = useState('');
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [challengeToken, setChallengeToken] = useState('');
  const [submitting, setSubmitting] = useState(false);

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

  const handleAddIdentifier = async () => {
    if (!emailInput.trim() || !emailInput.includes('@')) {
      return Alert.alert('Invalid Email', 'Please provide a valid email address.');
    }
    setSubmitting(true);
    try {
      const created = await api.addIdentifier('email', emailInput.trim());
      setEmailInput('');
      setAddModalVisible(false);
      Alert.alert(
        'Identity Added',
        `Verification challenge sent to ${created.masked_value}. Complete verification to enable active breach scanning.`
      );
      await fetchIdentifiers();
      // Start verification modal right away
      startVerificationFlow(created.id);
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
      // For developer testing / demo ergonomics:
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
        <View>
          <Text style={styles.title}>Monitored Identities</Text>
          <Text style={styles.subtitle}>Consent-first verified email and identity tokens</Text>
        </View>
        <TouchableOpacity style={styles.addBtn} onPress={() => setAddModalVisible(true)}>
          <Text style={styles.addBtnText}>+ Add Email</Text>
        </TouchableOpacity>
      </View>

      {/* Advisory Pill */}
      <View style={styles.advisoryCard}>
        <Text style={styles.advisoryIcon}>💡</Text>
        <Text style={styles.advisoryText}>
          Per zero-knowledge privacy requirements, all identifiers are stored using AES-256-GCM envelope
          encryption. The platform never queries government portals or stores raw Aadhaar numbers.
        </Text>
      </View>

      {identifiers.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>📭</Text>
          <Text style={styles.emptyTitle}>No Identifiers Enrolled</Text>
          <Text style={styles.emptySub}>Add and verify an email address to activate breach monitoring.</Text>
          <TouchableOpacity style={styles.emptyBtn} onPress={() => setAddModalVisible(true)}>
            <Text style={styles.emptyBtnText}>Add Your First Identifier</Text>
          </TouchableOpacity>
        </View>
      ) : (
        identifiers.map((item) => (
          <View key={item.id} style={styles.itemCard}>
            <View style={styles.itemHeader}>
              <View style={styles.itemTypePill}>
                <Text style={styles.itemTypeIcon}>✉️</Text>
                <Text style={styles.itemTypeValue}>{item.type.toUpperCase()}</Text>
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
                    {item.state === 'active' ? 'Pause' : 'Resume'}
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
        ))
      )}

      {/* Add Identifier Modal */}
      <Modal visible={addModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Email Identifier</Text>
            <Text style={styles.modalSub}>
              A verification challenge will be sent to confirm your ownership before monitoring starts.
            </Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. resident@example.in"
              placeholderTextColor="#64748b"
              autoCapitalize="none"
              keyboardType="email-address"
              value={emailInput}
              onChangeText={setEmailInput}
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
                  <Text style={styles.btnPrimaryText}>Send Challenge</Text>
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
              Enter the 6-digit verification code or token sent to your email to prove ownership.
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
    fontSize: 20,
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
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addBtnText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 13,
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
    borderRadius: 14,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1f2937',
    marginTop: 10,
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  emptySub: {
    fontSize: 13,
    color: '#94a3b8',
    textAlign: 'center',
    marginBottom: 16,
  },
  emptyBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  emptyBtnText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 13,
  },
  itemCard: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
    marginBottom: 12,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  itemTypePill: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  itemTypeIcon: {
    marginRight: 6,
    fontSize: 14,
  },
  itemTypeValue: {
    fontSize: 11,
    fontWeight: '700',
    color: '#60a5fa',
    letterSpacing: 0.5,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    backgroundColor: '#374151',
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
    fontSize: 16,
    fontWeight: '600',
    color: '#f8fafc',
    marginBottom: 4,
    fontFamily: 'monospace',
  },
  metaText: {
    fontSize: 11,
    color: '#64748b',
    marginBottom: 12,
  },
  itemActions: {
    flexDirection: 'row',
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#1f2937',
    paddingTop: 10,
  },
  btnAction: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  btnVerify: {
    backgroundColor: '#d97706',
    flex: 1,
  },
  btnVerifyText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  btnToggle: {
    backgroundColor: '#1f2937',
    borderWidth: 1,
    borderColor: '#374151',
    flex: 1,
  },
  btnToggleText: {
    color: '#e2e8f0',
    fontSize: 12,
    fontWeight: '500',
  },
  btnDelete: {
    backgroundColor: '#450a0a',
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  btnDeleteText: {
    color: '#f87171',
    fontSize: 12,
    fontWeight: '500',
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
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 16,
    lineHeight: 18,
  },
  input: {
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 8,
    padding: 12,
    color: '#f8fafc',
    fontSize: 14,
    marginBottom: 16,
  },
  tokenInput: {
    textAlign: 'center',
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 2,
    fontFamily: 'monospace',
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
    fontWeight: '500',
  },
  btnPrimary: {
    backgroundColor: '#2563eb',
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
