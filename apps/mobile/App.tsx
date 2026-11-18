import React, { useState, useEffect } from 'react';
import { registerRootComponent } from 'expo';
import {
  StyleSheet,
  Text,
  View,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { api } from './src/services/api';
import { localEngine } from './src/services/localEngine';
import { UserSession } from './src/types';
import { DashboardScreen } from './src/screens/DashboardScreen';
import { ActivityScreen } from './src/screens/ActivityScreen';
import { AadhaarPanScreen } from './src/screens/AadhaarPanScreen';
import { MoreScreen } from './src/screens/MoreScreen';
import { LoginScreen } from './src/screens/LoginScreen';
import {
  SUPPORTED_LANGUAGES,
  SupportedLanguage,
} from './src/services/bhashiniLocalization';

export type ScreenKey =
  | 'shield'
  | 'activity'
  | 'vault'
  | 'more'
  // Legacy / Direct routes
  | 'dashboard'
  | 'alerts'
  | 'incidents'
  | 'aadhaar'
  | 'research'
  | 'security'
  | 'identities';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<ScreenKey>('shield');
  const [session, setSession] = useState<UserSession | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);
  const [currentLang, setCurrentLang] = useState<SupportedLanguage>('en');
  const [langModalVisible, setLangModalVisible] = useState(false);

  const fetchUnreadCount = async () => {
    try {
      const items = await api.getNotifications();
      const unread = items.filter((n) => n.status !== 'read').length;
      setUnreadAlertsCount(unread);
    } catch {
      // Ignore background sync errors
    }
  };

  const initApp = async () => {
    try {
      await localEngine.hydrate();
      const current = await api.getSession();
      setSession(current);
      if (current) {
        await fetchUnreadCount();
      }
    } catch (err) {
      console.warn('Initial session lookup fallback:', err);
    } finally {
      setInitializing(false);
    }
  };

  useEffect(() => {
    initApp();
    const interval = setInterval(fetchUnreadCount, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectLanguage = (lang: SupportedLanguage) => {
    api.setLanguage(lang);
    setCurrentLang(lang);
    setLangModalVisible(false);
  };

  if (initializing) {
    return (
      <SafeAreaView style={styles.splashContainer}>
        <StatusBar barStyle="light-content" backgroundColor="#090d16" />
        <Text style={styles.splashLogo}>🛡️</Text>
        <Text style={styles.splashTitle}>Suraksha</Text>
        <Text style={styles.splashSubtitle}>Identity Protection Platform</Text>
        <ActivityIndicator size="small" color="#3b82f6" style={{ marginTop: 24 }} />
      </SafeAreaView>
    );
  }

  // If no user session, show the dedicated Google Login Screen
  if (!session) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#090d16" />
        <LoginScreen
          onLoginSuccess={(newSession) => {
            setSession(newSession);
            fetchUnreadCount();
          }}
        />
      </SafeAreaView>
    );
  }

  // Resolve which primary bottom nav tab is active
  const activeTabKey: 'shield' | 'activity' | 'vault' | 'more' =
    ['shield', 'dashboard'].includes(currentScreen)
      ? 'shield'
      : ['activity', 'alerts', 'incidents'].includes(currentScreen)
      ? 'activity'
      : ['vault', 'aadhaar'].includes(currentScreen)
      ? 'vault'
      : 'more';

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#090d16" />

      {/* Top App Bar */}
      <View style={styles.topBar}>
        <View style={styles.brandRow}>
          <Text style={styles.brandIcon}>🛡️</Text>
          <View>
            <Text style={styles.brandTitle}>Suraksha</Text>
            <Text style={styles.brandSub}>Consent-First Identity Shield</Text>
          </View>
        </View>
        <View style={styles.userSection}>
          {/* Vernacular Language Pill */}
          <TouchableOpacity
            style={styles.langPill}
            onPress={() => setLangModalVisible(true)}
            activeOpacity={0.7}
          >
            <Text style={styles.langPillText}>🌐 {currentLang.toUpperCase()}</Text>
          </TouchableOpacity>

          <View style={styles.userBadge}>
            <View style={styles.activeDot} />
            <Text style={styles.userEmail} numberOfLines={1}>
              {session?.email || 'resident'}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.logoutBtn}
            onPress={async () => {
              await api.logout();
              setSession(null);
            }}
          >
            <Text style={styles.logoutBtnText}>Sign Out</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Urgent Alert Banner */}
      {unreadAlertsCount > 0 && activeTabKey !== 'activity' && (
        <TouchableOpacity
          style={styles.alertBanner}
          onPress={() => setCurrentScreen('alerts')}
          activeOpacity={0.85}
        >
          <View style={styles.alertBannerLeft}>
            <Text style={styles.alertBannerIcon}>🚨</Text>
            <Text style={styles.alertBannerText}>
              {unreadAlertsCount} unread exposure alert{unreadAlertsCount > 1 ? 's' : ''}!
            </Text>
          </View>
          <Text style={styles.alertBannerArrow}>Review →</Text>
        </TouchableOpacity>
      )}

      {/* Main Screen Content */}
      <View style={styles.screenContainer}>
        {activeTabKey === 'shield' && (
          <DashboardScreen
            session={session}
            onNavigate={(scr) => setCurrentScreen(scr as ScreenKey)}
          />
        )}
        {activeTabKey === 'activity' && (
          <ActivityScreen
            initialTab={currentScreen === 'incidents' ? 'incidents' : 'alerts'}
            onRefreshAlertsCount={fetchUnreadCount}
          />
        )}
        {activeTabKey === 'vault' && <AadhaarPanScreen />}
        {activeTabKey === 'more' && (
          <MoreScreen
            session={session}
            onRefreshSession={initApp}
            onLogout={() => setSession(null)}
            onNavigateToVault={() => setCurrentScreen('vault')}
            onSelectLanguage={handleSelectLanguage}
            currentLanguage={currentLang}
            initialSubView={
              currentScreen === 'identities'
                ? 'identities'
                : currentScreen === 'security'
                ? 'security'
                : currentScreen === 'research'
                ? 'research'
                : 'menu'
            }
          />
        )}
      </View>

      {/* Bottom Navigation Tabs - 4 Elegant Tabs */}
      <View style={styles.bottomNav}>
        {[
          { key: 'shield', label: 'Shield', icon: '🛡️' },
          { key: 'activity', label: 'Activity', icon: '🔔', badge: unreadAlertsCount },
          { key: 'vault', label: 'Vault', icon: '🇮🇳' },
          { key: 'more', label: 'More', icon: '⚙️' },
        ].map((tab) => {
          const isActive = activeTabKey === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={styles.navTab}
              onPress={() => setCurrentScreen(tab.key as ScreenKey)}
              activeOpacity={0.7}
            >
              <View style={styles.tabIconWrap}>
                <Text style={[styles.navIcon, isActive && styles.navIconActive]}>{tab.icon}</Text>
                {tab.badge && tab.badge > 0 ? (
                  <View style={styles.badgeIndicator}>
                    <Text style={styles.badgeText}>{tab.badge > 9 ? '9+' : tab.badge}</Text>
                  </View>
                ) : null}
              </View>
              <Text style={[styles.navLabel, isActive && styles.navLabelActive]}>{tab.label}</Text>
              {isActive && <View style={styles.navIndicator} />}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Vernacular Language Selection Modal */}
      <Modal visible={langModalVisible} animationType="fade" transparent>
        <TouchableOpacity
          style={styles.modalBackdrop}
          activeOpacity={1}
          onPress={() => setLangModalVisible(false)}
        >
          <View style={styles.langModalContent}>
            <Text style={styles.langModalTitle}>🗣️ Select Regional Language</Text>
            <Text style={styles.langModalSub}>
              Powered by Project Bhashini Vernacular Engine
            </Text>
            <View style={{ gap: 8, marginTop: 12 }}>
              {SUPPORTED_LANGUAGES.map((lang) => (
                <TouchableOpacity
                  key={lang.code}
                  style={[
                    styles.langOptionBtn,
                    currentLang === lang.code && styles.langOptionBtnActive,
                  ]}
                  onPress={() => handleSelectLanguage(lang.code)}
                >
                  <Text style={styles.langOptionFlag}>{lang.flag}</Text>
                  <View style={{ flex: 1 }}>
                    <Text
                      style={[
                        styles.langOptionName,
                        currentLang === lang.code && styles.langOptionNameActive,
                      ]}
                    >
                      {lang.nativeName}
                    </Text>
                    <Text style={styles.langOptionEnglish}>{lang.name}</Text>
                  </View>
                  {currentLang === lang.code && (
                    <Text style={styles.langOptionCheck}>✓</Text>
                  )}
                </TouchableOpacity>
              ))}
            </View>
            <TouchableOpacity
              style={styles.langModalCloseBtn}
              onPress={() => setLangModalVisible(false)}
            >
              <Text style={styles.langModalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  splashContainer: {
    flex: 1,
    backgroundColor: '#090d16',
    alignItems: 'center',
    justifyContent: 'center',
  },
  splashLogo: {
    fontSize: 56,
    marginBottom: 8,
  },
  splashTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: 0.5,
  },
  splashSubtitle: {
    fontSize: 13,
    color: '#94a3b8',
    marginTop: 4,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    backgroundColor: '#090d16',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  brandIcon: {
    fontSize: 22,
    marginRight: 8,
  },
  brandTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
  },
  brandSub: {
    fontSize: 10,
    color: '#64748b',
  },
  userSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  langPill: {
    backgroundColor: '#111827',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  langPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#38bdf8',
  },
  userBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111827',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#1f2937',
    maxWidth: 140,
  },
  logoutBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  logoutBtnText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#f87171',
  },
  activeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10b981',
    marginRight: 6,
  },
  userEmail: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '500',
  },
  screenContainer: {
    flex: 1,
  },
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: '#111827',
    borderTopWidth: 1,
    borderTopColor: '#1f2937',
    paddingBottom: 4,
    paddingTop: 6,
  },
  navTab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
    position: 'relative',
  },
  navIcon: {
    fontSize: 18,
    marginBottom: 2,
    opacity: 0.6,
  },
  navIconActive: {
    opacity: 1,
    transform: [{ scale: 1.1 }],
  },
  navLabel: {
    fontSize: 10,
    color: '#64748b',
    fontWeight: '600',
  },
  navLabelActive: {
    color: '#38bdf8',
  },
  navIndicator: {
    position: 'absolute',
    top: -6,
    width: 24,
    height: 2,
    backgroundColor: '#38bdf8',
    borderRadius: 1,
  },
  alertBanner: {
    backgroundColor: '#991b1b',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#ef4444',
  },
  alertBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  alertBannerIcon: {
    fontSize: 16,
  },
  alertBannerText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
  alertBannerArrow: {
    color: '#fecaca',
    fontSize: 12,
    fontWeight: '700',
  },
  tabIconWrap: {
    position: 'relative',
  },
  badgeIndicator: {
    position: 'absolute',
    top: -4,
    right: -8,
    backgroundColor: '#ef4444',
    borderRadius: 8,
    minWidth: 16,
    height: 16,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 3,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 9,
    fontWeight: '800',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  langModalContent: {
    backgroundColor: '#0f172a',
    borderRadius: 16,
    padding: 20,
    width: '100%',
    maxWidth: 340,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  langModalTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 4,
  },
  langModalSub: {
    fontSize: 12,
    color: '#94a3b8',
    marginBottom: 12,
  },
  langOptionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111827',
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
    gap: 12,
  },
  langOptionBtnActive: {
    backgroundColor: '#1e3a8a',
    borderColor: '#3b82f6',
  },
  langOptionFlag: {
    fontSize: 20,
  },
  langOptionName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f8fafc',
  },
  langOptionNameActive: {
    color: '#60a5fa',
  },
  langOptionEnglish: {
    fontSize: 11,
    color: '#64748b',
  },
  langOptionCheck: {
    fontSize: 16,
    color: '#60a5fa',
    fontWeight: '800',
  },
  langModalCloseBtn: {
    marginTop: 16,
    backgroundColor: '#1e293b',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  langModalCloseText: {
    color: '#cbd5e1',
    fontWeight: '600',
    fontSize: 13,
  },
});

registerRootComponent(App);
