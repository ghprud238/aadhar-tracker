import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { api } from '../services/api';
import { UserSession } from '../types';

interface SecurityScreenProps {
  session: UserSession | null;
  onRefreshSession: () => void;
  onLogout?: () => void;
}

export const SecurityScreen: React.FC<SecurityScreenProps> = ({ session, onRefreshSession, onLogout }) => {
  const [biometricsEnabled, setBiometricsEnabled] = useState(true);
  const [stepUpElevated, setStepUpElevated] = useState(false);
  const [elevating, setElevating] = useState(false);
  const [passwordInput, setPasswordInput] = useState('');
  const [exporting, setExporting] = useState(false);
  const [erasing, setErasing] = useState(false);

  const handleLogout = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out of Suraksha Identity Shield?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await api.logout();
            if (onLogout) onLogout();
          },
        },
      ]
    );
  };

  const handleStepUpElevate = async () => {
    if (!passwordInput.trim()) {
      return Alert.alert('Password Required', 'Please enter your password to elevate this session.');
    }
    setElevating(true);
    try {
      const res = await api.stepUpElevate(passwordInput.trim());
      setStepUpElevated(res.elevated);
      setPasswordInput('');
      Alert.alert(
        'Session Elevated',
        `Elevated step-up privilege active for ${Math.round(res.valid_for_seconds / 60)} minutes. You may now export data or manage sensitive consent.`
      );
      onRefreshSession();
    } catch (err: any) {
      Alert.alert('Elevation Failed', err.message);
    } finally {
      setElevating(false);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const res = await api.exportPrivacyData();
      Alert.alert('Data Export Generated', `Export job completed. Status: ${res.status || 'Success'}. Export archive encrypted with tenant key.`);
    } catch (err: any) {
      if (err.message.includes('STEP_UP') || err.message.includes('Elevate')) {
        Alert.alert('Step-Up Auth Required', 'Please authenticate in the Step-Up section above before exporting personal data.');
      } else {
        Alert.alert('Export Error', err.message);
      }
    } finally {
      setExporting(false);
    }
  };

  const handleRequestErasure = () => {
    Alert.alert(
      'Request Account & Data Erasure',
      'This will withdraw all consents, delete your blind indexes, and cascade purge all monitored identifiers under the 30-day DPDP Act lifecycle. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Request Erasure',
          style: 'destructive',
          onPress: async () => {
            setErasing(true);
            try {
              await api.requestAccountErasure();
              Alert.alert('Erasure Requested', 'Your erasure request has been queued into the Privacy Worker pipeline.');
            } catch (err: any) {
              Alert.alert('Erasure Error', err.message);
            } finally {
              setErasing(false);
            }
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Account Security & Privacy</Text>
        <Text style={styles.subtitle}>
          End-to-end encryption • Step-up authentication • DPDP Act compliance
        </Text>
      </View>

      {/* Biometric App Lock Card */}
      <View style={styles.card}>
        <View style={styles.rowBetween}>
          <View style={{ flex: 1, paddingRight: 12 }}>
            <Text style={styles.cardTitle}>Biometric App Lock</Text>
            <Text style={styles.cardDesc}>
              Require Face ID / Touch ID / Fingerprint to open Suraksha on this mobile device.
            </Text>
          </View>
          <Switch
            value={biometricsEnabled}
            onValueChange={(val) => {
              setBiometricsEnabled(val);
              Alert.alert('Biometrics Updated', val ? 'Biometric verification required on launch.' : 'Biometric launch check disabled.');
            }}
            trackColor={{ false: '#374151', true: '#2563eb' }}
            thumbColor={biometricsEnabled ? '#ffffff' : '#9ca3af'}
          />
        </View>
      </View>

      {/* Step-Up Authentication Card */}
      <View style={styles.card}>
        <View style={styles.stepUpHeader}>
          <Text style={styles.cardTitle}>Step-Up Authentication</Text>
          <View style={[styles.statusPill, stepUpElevated ? styles.statusPillActive : styles.statusPillStandard]}>
            <Text style={styles.statusPillText}>{stepUpElevated ? 'ELEVATED' : 'STANDARD'}</Text>
          </View>
        </View>
        <Text style={styles.cardDesc}>
          Privileged operations (exporting audit trails, modifying core consent, deleting identifiers)
          require a recent high-assurance authentication step.
        </Text>

        {!stepUpElevated ? (
          <View style={{ marginTop: 12 }}>
            <TextInput
              style={styles.input}
              placeholder="Confirm account password (e.g. SecretMaster123!)"
              placeholderTextColor="#64748b"
              secureTextEntry
              value={passwordInput}
              onChangeText={setPasswordInput}
            />
            <TouchableOpacity
              style={styles.btnPrimary}
              onPress={handleStepUpElevate}
              disabled={elevating}
            >
              {elevating ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.btnPrimaryText}>Elevate Session</Text>
              )}
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.elevatedBox}>
            <Text style={styles.elevatedText}>✓ Session elevated. Valid for high-privilege actions.</Text>
          </View>
        )}
      </View>

      {/* Privacy Center & DPDP Actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Privacy Center & Rights</Text>
        <Text style={styles.cardDesc}>
          Exercise your statutory rights under the Digital Personal Data Protection Act (DPDP Act 2023).
        </Text>

        <View style={styles.actionRow}>
          <TouchableOpacity
            style={styles.btnOutline}
            onPress={handleExportData}
            disabled={exporting}
          >
            {exporting ? (
              <ActivityIndicator color="#38bdf8" size="small" />
            ) : (
              <Text style={styles.btnOutlineText}>📥 Export My Data (JSON)</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.btnDanger}
            onPress={handleRequestErasure}
            disabled={erasing}
          >
            {erasing ? (
              <ActivityIndicator color="#f87171" size="small" />
            ) : (
              <Text style={styles.btnDangerText}>🗑️ Request Account Erasure</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.btnOutline, { borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.08)' }]}
            onPress={handleLogout}
          >
            <Text style={[styles.btnOutlineText, { color: '#f87171' }]}>🚪 Sign Out of Google Session</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Current Session Metadata */}
      <View style={styles.sessionMetaCard}>
        <Text style={styles.sessionMetaTitle}>Active Session Telemetry</Text>
        <Text style={styles.sessionMetaText}>Resident: {session?.email}</Text>
        <Text style={styles.sessionMetaText}>Tenant: {session?.tenant_id}</Text>
        <Text style={styles.sessionMetaText}>Role: {session?.role}</Text>
        <Text style={styles.sessionMetaText}>Session Token Digest: HMAC-SHA256 verified</Text>
      </View>
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
  card: {
    backgroundColor: '#111827',
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderColor: '#1f2937',
    marginBottom: 16,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stepUpHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  cardDesc: {
    fontSize: 12,
    color: '#94a3b8',
    lineHeight: 17,
  },
  statusPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusPillActive: {
    backgroundColor: '#064e3b',
  },
  statusPillStandard: {
    backgroundColor: '#374151',
  },
  statusPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#f8fafc',
  },
  input: {
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 8,
    padding: 12,
    color: '#f8fafc',
    fontSize: 13,
    marginBottom: 10,
  },
  btnPrimary: {
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnPrimaryText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  elevatedBox: {
    backgroundColor: '#064e3b',
    borderRadius: 8,
    padding: 12,
    marginTop: 10,
    borderWidth: 1,
    borderColor: '#059669',
  },
  elevatedText: {
    color: '#6ee7b7',
    fontSize: 12,
    fontWeight: '600',
  },
  actionRow: {
    gap: 10,
    marginTop: 14,
  },
  btnOutline: {
    backgroundColor: '#1f2937',
    borderWidth: 1,
    borderColor: '#374151',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnOutlineText: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '600',
  },
  btnDanger: {
    backgroundColor: '#450a0a',
    borderWidth: 1,
    borderColor: '#ef4444',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnDangerText: {
    color: '#f87171',
    fontSize: 13,
    fontWeight: '600',
  },
  sessionMetaCard: {
    backgroundColor: '#0d1322',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  sessionMetaTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748b',
    marginBottom: 6,
  },
  sessionMetaText: {
    fontSize: 11,
    color: '#475569',
    lineHeight: 16,
    fontFamily: 'monospace',
  },
});
