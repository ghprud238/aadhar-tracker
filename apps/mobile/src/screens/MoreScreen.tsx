import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { UserSession } from '../types';
import { IdentitiesScreen } from './IdentitiesScreen';
import { SecurityScreen } from './SecurityScreen';
import { MarketResearchScreen } from './MarketResearchScreen';
import { SupportedLanguage } from '../services/bhashiniLocalization';
import { api } from '../services/api';

interface MoreScreenProps {
  session: UserSession | null;
  onRefreshSession: () => void;
  onLogout: () => void;
  onNavigateToVault: () => void;
  onSelectLanguage: (lang: SupportedLanguage) => void;
  currentLanguage: SupportedLanguage;
  initialSubView?: 'menu' | 'identities' | 'security' | 'research';
}

type SubView = 'menu' | 'identities' | 'security' | 'research';

export const MoreScreen: React.FC<MoreScreenProps> = ({
  session,
  onRefreshSession,
  onLogout,
  onNavigateToVault,
  onSelectLanguage,
  currentLanguage,
  initialSubView = 'menu',
}) => {
  const [activeSubView, setActiveSubView] = useState<SubView>(initialSubView);

  React.useEffect(() => {
    setActiveSubView(initialSubView);
  }, [initialSubView]);

  if (activeSubView === 'identities') {
    return (
      <View style={styles.container}>
        <View style={styles.subHeader}>
          <TouchableOpacity style={styles.backBtn} onPress={() => setActiveSubView('menu')}>
            <Text style={styles.backBtnText}>← Back to Settings</Text>
          </TouchableOpacity>
        </View>
        <IdentitiesScreen />
      </View>
    );
  }

  if (activeSubView === 'security') {
    return (
      <View style={styles.container}>
        <View style={styles.subHeader}>
          <TouchableOpacity style={styles.backBtn} onPress={() => setActiveSubView('menu')}>
            <Text style={styles.backBtnText}>← Back to Settings</Text>
          </TouchableOpacity>
        </View>
        <SecurityScreen
          session={session}
          onRefreshSession={onRefreshSession}
          onLogout={onLogout}
        />
      </View>
    );
  }

  if (activeSubView === 'research') {
    return (
      <View style={styles.container}>
        <View style={styles.subHeader}>
          <TouchableOpacity style={styles.backBtn} onPress={() => setActiveSubView('menu')}>
            <Text style={styles.backBtnText}>← Back to Settings</Text>
          </TouchableOpacity>
        </View>
        <MarketResearchScreen onNavigateToShield={onNavigateToVault} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      {/* Profile Header Card */}
      <View style={styles.profileCard}>
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarText}>
            {session?.full_name ? session.full_name.charAt(0).toUpperCase() : 'R'}
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.userName}>{session?.full_name || 'Resident Citizen'}</Text>
          <Text style={styles.userEmail}>{session?.email || 'resident@example.in'}</Text>
          <View style={styles.verifiedRow}>
            <Text style={styles.verifiedBadge}>✓ DPDP Act 2023 Consent Active</Text>
          </View>
        </View>
      </View>

      {/* Section 1: Identity & Credentials */}
      <Text style={styles.sectionHeader}>IDENTITY MONITORING</Text>
      <View style={styles.cardGroup}>
        <TouchableOpacity
          style={styles.menuRow}
          onPress={() => setActiveSubView('identities')}
          activeOpacity={0.7}
        >
          <Text style={styles.menuIcon}>🔑</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.menuTitle}>Monitored Identifiers</Text>
            <Text style={styles.menuSub}>Verified email & phone breach radars</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>

        <View style={styles.rowDivider} />

        <TouchableOpacity
          style={styles.menuRow}
          onPress={onNavigateToVault}
          activeOpacity={0.7}
        >
          <Text style={styles.menuIcon}>🇮🇳</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.menuTitle}>Aadhaar & PAN Vault</Text>
            <Text style={styles.menuSub}>Biometric locks, masked passes, auto-redactor</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Section 2: Cyber Defense & Research */}
      <Text style={styles.sectionHeader}>RESEARCH & THREAT LABS</Text>
      <View style={styles.cardGroup}>
        <TouchableOpacity
          style={styles.menuRow}
          onPress={() => setActiveSubView('research')}
          activeOpacity={0.7}
        >
          <Text style={styles.menuIcon}>🔬</Text>
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <Text style={styles.menuTitle}>Citizen Cyber Hygiene Audit</Text>
              <View style={styles.liveDot} />
            </View>
            <Text style={styles.menuSub}>60s risk survey & live national telemetry</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Section 3: Security & Session */}
      <Text style={styles.sectionHeader}>SECURITY & PRIVACY</Text>
      <View style={styles.cardGroup}>
        <TouchableOpacity
          style={styles.menuRow}
          onPress={() => setActiveSubView('security')}
          activeOpacity={0.7}
        >
          <Text style={styles.menuIcon}>🛡️</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.menuTitle}>Security & Biometric Step-Up</Text>
            <Text style={styles.menuSub}>FaceID/Fingerprint, session inventory, audit log</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>

        <View style={styles.rowDivider} />

        <TouchableOpacity
          style={styles.menuRow}
          onPress={() => {
            Alert.alert(
              'Zero-Knowledge Architecture',
              '• No raw 12-digit Aadhaar or biometrics stored.\n• HMAC-SHA256 blind indexing.\n• AES-256-GCM envelope encryption.\n• On-device local-first fallback.'
            );
          }}
          activeOpacity={0.7}
        >
          <Text style={styles.menuIcon}>🔒</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.menuTitle}>Cryptographic Guarantees</Text>
            <Text style={styles.menuSub}>Zero-Plaintext Invariant & legal provenance</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Logout Action */}
      <TouchableOpacity style={styles.logoutBtn} onPress={onLogout} activeOpacity={0.8}>
        <Text style={styles.logoutBtnText}>🚪 Sign Out</Text>
      </TouchableOpacity>

      <Text style={styles.footerVersion}>Suraksha Shield v1.0.0 • Consent-First Platform</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  subHeader: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    backgroundColor: '#090d16',
  },
  backBtn: {
    paddingVertical: 4,
  },
  backBtnText: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '700',
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#131b2e',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 20,
    gap: 14,
  },
  avatarCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#0284c7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '800',
  },
  userName: {
    color: '#f8fafc',
    fontSize: 16,
    fontWeight: '700',
  },
  userEmail: {
    color: '#94a3b8',
    fontSize: 13,
    marginTop: 2,
  },
  verifiedRow: {
    marginTop: 6,
  },
  verifiedBadge: {
    color: '#10b981',
    fontSize: 11,
    fontWeight: '600',
  },
  sectionHeader: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.8,
    marginBottom: 8,
    marginLeft: 4,
  },
  cardGroup: {
    backgroundColor: '#131b2e',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 20,
    overflow: 'hidden',
  },
  menuRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    gap: 12,
  },
  menuIcon: {
    fontSize: 20,
  },
  menuTitle: {
    color: '#f8fafc',
    fontSize: 14,
    fontWeight: '700',
  },
  menuSub: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 2,
  },
  menuArrow: {
    color: '#64748b',
    fontSize: 18,
    fontWeight: '700',
  },
  rowDivider: {
    height: 1,
    backgroundColor: '#1e293b',
    marginLeft: 46,
  },
  liveDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#10b981',
  },
  logoutBtn: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  logoutBtnText: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: '700',
  },
  footerVersion: {
    textAlign: 'center',
    color: '#475569',
    fontSize: 11,
    marginTop: 8,
  },
});
