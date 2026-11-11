import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  Modal,
  TextInput,
  ActivityIndicator,
  Alert,
  Linking,
  Platform,
} from 'react-native';
import { api } from '../services/api';
import { UserSession } from '../types';
import { DEMO_GOOGLE_ACCOUNTS, GoogleUserProfile, buildGoogleAuthUrl } from '../services/googleAuth';

interface LoginScreenProps {
  onLoginSuccess: (session: UserSession) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [accountPickerVisible, setAccountPickerVisible] = useState(false);
  const [customEmail, setCustomEmail] = useState('');
  const [customName, setCustomName] = useState('');

  const handleSelectGoogleAccount = async (account: GoogleUserProfile) => {
    setLoading(true);
    setAccountPickerVisible(false);
    try {
      const session = await api.loginWithGoogle(account.email, account.name);
      onLoginSuccess(session);
    } catch (err: any) {
      Alert.alert('Sign-In Error', err.message || 'Failed to complete Google authentication.');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomGoogleLogin = async () => {
    if (!customEmail.trim() || !customEmail.includes('@')) {
      return Alert.alert('Invalid Email', 'Please enter a valid Google account email.');
    }
    const name = customName.trim() || customEmail.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    setLoading(true);
    setAccountPickerVisible(false);
    try {
      const session = await api.loginWithGoogle(customEmail.trim(), name);
      onLoginSuccess(session);
    } catch (err: any) {
      Alert.alert('Sign-In Error', err.message || 'Failed to complete Google authentication.');
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchBrowserOAuth = () => {
    const redirectUri = Platform.OS === 'web' && typeof window !== 'undefined'
      ? window.location.origin
      : 'in.suraksha.mobile://oauth';
    const authUrl = buildGoogleAuthUrl(redirectUri);

    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.location.href = authUrl;
    } else {
      Linking.openURL(authUrl).catch(() => {
        Alert.alert('Browser Open Error', 'Unable to launch Google OAuth in external browser. Using quick account selector instead.');
      });
    }
  };

  const handleAnonymousLogin = async () => {
    setLoading(true);
    try {
      const session = await api.loginWithGoogle('resident.anonymous@suraksha.local', 'Anonymous Citizen');
      onLoginSuccess(session);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Brand Header */}
      <View style={styles.header}>
        <View style={styles.logoBadge}>
          <Text style={styles.logoEmoji}>🛡️</Text>
        </View>
        <Text style={styles.appTitle}>सुरक्षा | SURAKSHA</Text>
        <Text style={styles.appSubtitle}>Citizen Identity Protection & Zero-Leak Shield</Text>
        <View style={styles.badgeRow}>
          <View style={styles.securityTag}>
            <Text style={styles.securityTagText}>🇮🇳 DPDP ACT 2023 COMPLIANT</Text>
          </View>
          <View style={[styles.securityTag, { borderColor: '#10b981' }]}>
            <Text style={[styles.securityTagText, { color: '#34d399' }]}>⚡ ZERO-BACKEND PRIVACY</Text>
          </View>
        </View>
      </View>

      {/* Trust & Protection Pillars */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Why Citizens Trust Suraksha</Text>
        
        <View style={styles.featureItem}>
          <Text style={styles.featureIcon}>🔒</Text>
          <View style={styles.featureBody}>
            <Text style={styles.featureHeading}>Zero-Knowledge Hardware Vault</Text>
            <Text style={styles.featureDesc}>
              Aadhaar & PAN tokens are encrypted on-device. No central server ever sees your unmasked numbers.
            </Text>
          </View>
        </View>

        <View style={styles.featureItem}>
          <Text style={styles.featureIcon}>💬</Text>
          <View style={styles.featureBody}>
            <Text style={styles.featureHeading}>WhatsApp & SMS Outbound DLP</Text>
            <Text style={styles.featureDesc}>
              Instant Verhoeff D₅ math detects unmasked 12-digit leaks before transmission.
            </Text>
          </View>
        </View>

        <View style={styles.featureItem}>
          <Text style={styles.featureIcon}>🚨</Text>
          <View style={styles.featureBody}>
            <Text style={styles.featureHeading}>Dark Web Breach Early Warning</Text>
            <Text style={styles.featureDesc}>
              K-anonymity matching against 100M+ compromised records without uploading your identity.
            </Text>
          </View>
        </View>
      </View>

      {/* Google Authentication Actions */}
      <View style={styles.authContainer}>
        <Text style={styles.authPrompt}>Sign in to activate your personal identity shield</Text>

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#3b82f6" />
            <Text style={styles.loadingText}>Securing Google Session...</Text>
          </View>
        ) : (
          <>
            {/* Primary Google Login Button */}
            <TouchableOpacity
              style={styles.googleBtn}
              onPress={() => setAccountPickerVisible(true)}
              activeOpacity={0.85}
            >
              <View style={styles.googleIconWrapper}>
                {/* 4-Color Styled Google "G" Badge */}
                <Text style={styles.googleIconText}>G</Text>
              </View>
              <Text style={styles.googleBtnText}>Continue with Google</Text>
            </TouchableOpacity>

            {/* Anonymous Zero-Cloud Mode */}
            <TouchableOpacity
              style={styles.anonBtn}
              onPress={handleAnonymousLogin}
              activeOpacity={0.7}
            >
              <Text style={styles.anonBtnText}>Skip & Continue in Zero-Cloud Anonymous Mode</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Statutory Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Protected by end-to-end hardware encryption. Suraksha is an independent cybersecurity utility and does not store private biometric databases.
        </Text>
      </View>

      {/* Google Account Picker Modal */}
      <Modal
        visible={accountPickerVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setAccountPickerVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <View style={styles.googleModalBadge}>
                <Text style={styles.googleIconText}>G</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>Choose a Google Account</Text>
                <Text style={styles.modalSub}>to continue to Suraksha Identity Shield</Text>
              </View>
              <TouchableOpacity onPress={() => setAccountPickerVisible(false)}>
                <Text style={styles.closeBtn}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.pickerSectionLabel}>AVAILABLE GOOGLE PROFILES</Text>
            {DEMO_GOOGLE_ACCOUNTS.map((acc) => (
              <TouchableOpacity
                key={acc.id}
                style={styles.accountRow}
                onPress={() => handleSelectGoogleAccount(acc)}
              >
                <View style={styles.avatarCircle}>
                  <Text style={styles.avatarLetter}>{acc.name[0]}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.accountName}>{acc.name}</Text>
                  <Text style={styles.accountEmail}>{acc.email}</Text>
                </View>
                <Text style={styles.selectArrow}>→</Text>
              </TouchableOpacity>
            ))}

            <Text style={[styles.pickerSectionLabel, { marginTop: 16 }]}>OR ENTER ANOTHER GOOGLE ACCOUNT</Text>
            <TextInput
              style={styles.input}
              placeholder="user@gmail.com"
              placeholderTextColor="#64748b"
              value={customEmail}
              onChangeText={setCustomEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
            <TextInput
              style={[styles.input, { marginTop: 8 }]}
              placeholder="Full Name (e.g. Vikram Malhotra)"
              placeholderTextColor="#64748b"
              value={customName}
              onChangeText={setCustomName}
            />

            <TouchableOpacity
              style={styles.submitCustomBtn}
              onPress={handleCustomGoogleLogin}
            >
              <Text style={styles.submitCustomBtnText}>Sign In with This Account</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.browserOAuthBtn}
              onPress={handleLaunchBrowserOAuth}
            >
              <Text style={styles.browserOAuthBtnText}>🌐 Open Google OAuth Browser Window</Text>
            </TouchableOpacity>
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
    padding: 24,
    paddingTop: 48,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  logoBadge: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: '#1e293b',
    borderWidth: 2,
    borderColor: '#38bdf8',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    shadowColor: '#38bdf8',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
  },
  logoEmoji: {
    fontSize: 40,
  },
  appTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: 1.5,
  },
  appSubtitle: {
    fontSize: 13,
    color: '#94a3b8',
    marginTop: 4,
    textAlign: 'center',
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  securityTag: {
    borderWidth: 1,
    borderColor: '#38bdf8',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    backgroundColor: 'rgba(56, 189, 248, 0.08)',
  },
  securityTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#38bdf8',
    letterSpacing: 0.5,
  },
  card: {
    width: '100%',
    backgroundColor: '#0f172a',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 24,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#cbd5e1',
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  featureIcon: {
    fontSize: 20,
    marginRight: 12,
    marginTop: 2,
  },
  featureBody: {
    flex: 1,
  },
  featureHeading: {
    fontSize: 13,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  featureDesc: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
    lineHeight: 17,
  },
  authContainer: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 24,
  },
  authPrompt: {
    fontSize: 12,
    color: '#94a3b8',
    marginBottom: 14,
    fontWeight: '500',
  },
  googleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    width: '100%',
    paddingVertical: 14,
    borderRadius: 28,
    shadowColor: '#ffffff',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
  googleIconWrapper: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  googleIconText: {
    fontSize: 15,
    fontWeight: '900',
    color: '#4285F4',
  },
  googleBtnText: {
    color: '#1f2937',
    fontSize: 15,
    fontWeight: '700',
  },
  anonBtn: {
    marginTop: 16,
    paddingVertical: 10,
  },
  anonBtnText: {
    color: '#64748b',
    fontSize: 12,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    gap: 10,
  },
  loadingText: {
    color: '#94a3b8',
    fontSize: 13,
  },
  footer: {
    marginTop: 8,
    paddingHorizontal: 12,
  },
  footerText: {
    fontSize: 11,
    color: '#475569',
    textAlign: 'center',
    lineHeight: 16,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#0f172a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: '#334155',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 12,
  },
  googleModalBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  modalSub: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 1,
  },
  closeBtn: {
    fontSize: 18,
    color: '#94a3b8',
    padding: 6,
  },
  pickerSectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748b',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  accountRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  avatarCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#3b82f6',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  avatarLetter: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 15,
  },
  accountName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  accountEmail: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 1,
  },
  selectArrow: {
    color: '#38bdf8',
    fontSize: 16,
    fontWeight: '700',
  },
  input: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    padding: 12,
    color: '#f8fafc',
    fontSize: 13,
  },
  submitCustomBtn: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  submitCustomBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  browserOAuthBtn: {
    paddingVertical: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  browserOAuthBtnText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
});
