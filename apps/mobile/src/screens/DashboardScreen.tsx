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
} from 'react-native';
import { api } from '../services/api';
import { CompanionGlance, UserSession } from '../types';

interface DashboardScreenProps {
  session: UserSession | null;
  onNavigate: (screen: string) => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ session, onNavigate }) => {
  const [glance, setGlance] = useState<CompanionGlance | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [scanning, setScanning] = useState(false);

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
          <Text style={styles.greeting}>Identity Shield</Text>
          <Text style={styles.userName}>{session?.full_name || 'Resident'}</Text>
        </View>
        <TouchableOpacity
          style={[styles.scanButton, scanning && styles.buttonDisabled]}
          onPress={handleScanNow}
          disabled={scanning}
        >
          {scanning ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.scanButtonText}>⚡ Quick Scan</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Main Shield Widget */}
      <View style={[styles.shieldCard, { borderColor: shieldColor }]}>
        <View style={[styles.shieldBadge, { backgroundColor: `${shieldColor}20` }]}>
          <Text style={[styles.shieldIcon, { color: shieldColor }]}>🛡️</Text>
          <Text style={[styles.shieldStatusText, { color: shieldColor }]}>
            {glance?.shield_status.toUpperCase() || 'SECURE'}
          </Text>
        </View>
        <Text style={styles.shieldTitle}>
          {glance?.shield_status === 'critical'
            ? 'Critical Exposure Detected'
            : glance?.shield_status === 'warning'
            ? 'Potential Threat Identified'
            : 'Identity Protected & Secure'}
        </Text>
        <Text style={styles.shieldSubtitle}>
          {glance?.shield_status === 'secure'
            ? 'No unaddressed breach records or compromised credentials matching your verified identifiers.'
            : 'Action required: Review detected incidents and complete remediation steps below.'}
        </Text>
      </View>

      {/* Urgent Breach Alert if present */}
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

      {/* Metric Cards Grid */}
      <View style={styles.statsGrid}>
        <TouchableOpacity
          style={styles.statCard}
          onPress={() => onNavigate('identities')}
        >
          <Text style={styles.statNumber}>{glance?.active_monitored_count ?? 0}</Text>
          <Text style={styles.statLabel}>Active Identifiers</Text>
          <Text style={styles.statLink}>Manage →</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.statCard}
          onPress={() => onNavigate('incidents')}
        >
          <Text style={[styles.statNumber, { color: glance?.active_incidents ? '#ef4444' : '#10b981' }]}>
            {glance?.active_incidents ?? 0}
          </Text>
          <Text style={styles.statLabel}>Active Incidents</Text>
          <Text style={styles.statLink}>View List →</Text>
        </TouchableOpacity>
      </View>

      {/* Aadhaar Biometric Lock Status Card */}
      <View style={styles.actionCard}>
        <View style={styles.actionHeader}>
          <Text style={styles.actionIcon}>🇮🇳</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.actionTitle}>UIDAI Aadhaar Biometric Lock</Text>
            <Text style={styles.actionStatus}>
              {glance?.biometrics_locked
                ? '✅ User Reported Locked via m-Aadhaar'
                : '⚠️ Biometric Lock Not Confirmed Yet'}
            </Text>
          </View>
        </View>
        <Text style={styles.actionDesc}>
          Prevent unauthorized authentication by keeping your Aadhaar biometric records locked when not in use.
        </Text>
        <TouchableOpacity
          style={styles.actionBtn}
          onPress={() => onNavigate('aadhaar')}
        >
          <Text style={styles.actionBtnText}>Open Aadhaar & PAN Guide →</Text>
        </TouchableOpacity>
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
    marginBottom: 20,
    marginTop: 8,
  },
  greeting: {
    fontSize: 13,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  userName: {
    fontSize: 22,
    fontWeight: '700',
    color: '#f8fafc',
  },
  scanButton: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    shadowColor: '#2563eb',
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 2,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  scanButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14,
  },
  shieldCard: {
    backgroundColor: '#111827',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1.5,
    marginBottom: 16,
  },
  shieldBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginBottom: 12,
  },
  shieldIcon: {
    fontSize: 18,
    marginRight: 6,
  },
  shieldStatusText: {
    fontWeight: '700',
    fontSize: 13,
    letterSpacing: 0.6,
  },
  shieldTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 6,
  },
  shieldSubtitle: {
    fontSize: 13,
    color: '#94a3b8',
    lineHeight: 18,
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
});
