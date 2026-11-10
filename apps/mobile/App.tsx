import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { api } from './src/services/api';
import { UserSession } from './src/types';
import { DashboardScreen } from './src/screens/DashboardScreen';
import { IdentitiesScreen } from './src/screens/IdentitiesScreen';
import { IncidentsScreen } from './src/screens/IncidentsScreen';
import { AadhaarPanScreen } from './src/screens/AadhaarPanScreen';
import { SecurityScreen } from './src/screens/SecurityScreen';
import { AlertsScreen } from './src/screens/AlertsScreen';

type ScreenKey = 'dashboard' | 'identities' | 'incidents' | 'alerts' | 'aadhaar' | 'security';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<ScreenKey>('dashboard');
  const [session, setSession] = useState<UserSession | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);

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
      let current: UserSession;
      try {
        current = await api.getSession();
      } catch {
        current = await api.authenticate('resident@example.in', 'Aarav Sharma');
      }
      setSession(current);
      await fetchUnreadCount();
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
        <View style={styles.userBadge}>
          <View style={styles.activeDot} />
          <Text style={styles.userEmail} numberOfLines={1}>
            {session?.email || 'resident'}
          </Text>
        </View>
      </View>

      {/* Urgent Alert Banner */}
      {unreadAlertsCount > 0 && currentScreen !== 'alerts' && (
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
        {currentScreen === 'dashboard' && (
          <DashboardScreen session={session} onNavigate={(scr) => setCurrentScreen(scr as ScreenKey)} />
        )}
        {currentScreen === 'alerts' && (
          <AlertsScreen
            onNavigate={(scr) => setCurrentScreen(scr as ScreenKey)}
            onRefreshAlertsCount={fetchUnreadCount}
          />
        )}
        {currentScreen === 'identities' && <IdentitiesScreen />}
        {currentScreen === 'incidents' && <IncidentsScreen />}
        {currentScreen === 'aadhaar' && <AadhaarPanScreen />}
        {currentScreen === 'security' && (
          <SecurityScreen session={session} onRefreshSession={initApp} />
        )}
      </View>

      {/* Bottom Navigation Tabs */}
      <View style={styles.bottomNav}>
        {[
          { key: 'dashboard', label: 'Shield', icon: '📊' },
          { key: 'alerts', label: 'Alerts', icon: '🔔', badge: unreadAlertsCount },
          { key: 'incidents', label: 'Incidents', icon: '⚠️' },
          { key: 'identities', label: 'Identities', icon: '🔑' },
          { key: 'aadhaar', label: 'Aadhaar', icon: '🇮🇳' },
          { key: 'security', label: 'Security', icon: '🛡️' },
        ].map((tab) => {
          const isActive = currentScreen === tab.key;
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
  userBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111827',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#1f2937',
    maxWidth: 160,
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
});
