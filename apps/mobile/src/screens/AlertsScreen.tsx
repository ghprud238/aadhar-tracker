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
import { NotificationItem } from '../types';

interface AlertsScreenProps {
  onNavigate?: (screen: string) => void;
  onRefreshAlertsCount?: () => void;
}

export const AlertsScreen: React.FC<AlertsScreenProps> = ({ onNavigate, onRefreshAlertsCount }) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [triggering, setTriggering] = useState(false);

  const fetchNotifications = async () => {
    try {
      const data = await api.getNotifications();
      setNotifications(data);
      if (onRefreshAlertsCount) {
        onRefreshAlertsCount();
      }
    } catch (err: any) {
      console.warn('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 5000); // 5s auto-poll
    return () => clearInterval(interval);
  }, []);

  const handleMarkRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'read' } : n))
      );
      if (onRefreshAlertsCount) onRefreshAlertsCount();
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, status: 'read' })));
      if (onRefreshAlertsCount) onRefreshAlertsCount();
      Alert.alert('Cleared', 'All alerts marked as read.');
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleSimulateWhatsAppDLP = async () => {
    setTriggering(true);
    try {
      const res = await api.simulateWhatsAppDLP(
        'Please find my Aadhaar 9999 4105 7058 and PAN ABCDE1234F for checkin',
        '+919876543210'
      );
      Alert.alert(
        '🚨 WhatsApp DLP Alert Dispatched',
        `Unmasked IDs intercepted!\nAutomated WhatsApp alert sent to sender:\n\n${res.automated_whatsapp_alert?.substring(0, 150)}...`
      );
      await fetchNotifications();
    } catch (err: any) {
      Alert.alert('Simulation Error', err.message);
    } finally {
      setTriggering(false);
    }
  };

  const handleTriggerCanary = async () => {
    setTriggering(true);
    try {
      await api.triggerCanaryTest('aadhaar_sandbox_1');
      Alert.alert(
        '🛡️ Canary Exposure Injected',
        'Simulated dark web paste detection with UIDAI Sandbox dummy Aadhaar. Alert should appear momentarily.'
      );
      await fetchNotifications();
    } catch (err: any) {
      Alert.alert('Canary Error', err.message);
    } finally {
      setTriggering(false);
    }
  };

  const unreadCount = notifications.filter((n) => n.status !== 'read').length;

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Syncing notification feed...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            fetchNotifications();
          }}
          tintColor="#3b82f6"
        />
      }
    >
      {/* Screen Title & Quick Actions */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Incident Alerts</Text>
          <Text style={styles.subTitle}>
            {unreadCount > 0
              ? `${unreadCount} unread security notification${unreadCount > 1 ? 's' : ''}`
              : 'All notifications acknowledged'}
          </Text>
        </View>
        {unreadCount > 0 && (
          <TouchableOpacity style={styles.markAllBtn} onPress={handleMarkAllRead}>
            <Text style={styles.markAllText}>Mark all read</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Interactive Testing Panel */}
      <View style={styles.testPanel}>
        <Text style={styles.testPanelTitle}>🧪 Interactive Simulation Triggers</Text>
        <Text style={styles.testPanelDesc}>
          Trigger live alert payloads locally using synthetic Indian identity data:
        </Text>
        <View style={styles.testBtnRow}>
          <TouchableOpacity
            style={[styles.testBtn, styles.testBtnWa, triggering && styles.btnDisabled]}
            onPress={handleSimulateWhatsAppDLP}
            disabled={triggering}
          >
            <Text style={styles.testBtnText}>💬 WhatsApp DLP Alert</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.testBtn, styles.testBtnCanary, triggering && styles.btnDisabled]}
            onPress={handleTriggerCanary}
            disabled={triggering}
          >
            <Text style={styles.testBtnText}>🚨 Canary Breach Alert</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Notifications Feed */}
      <View style={styles.feed}>
        {notifications.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyIcon}>🛡️</Text>
            <Text style={styles.emptyTitle}>No Security Alerts</Text>
            <Text style={styles.emptyDesc}>
              No exposures have been detected for your monitored identities. Use the triggers above
              to simulate real-time alerts.
            </Text>
          </View>
        ) : (
          notifications.map((item) => {
            const isUnread = item.status !== 'read';
            const isCritical =
              item.title.toLowerCase().includes('critical') ||
              item.body.toLowerCase().includes('critical') ||
              item.title.toLowerCase().includes('whatsapp');
            return (
              <View
                key={item.id}
                style={[
                  styles.alertCard,
                  isUnread && styles.alertCardUnread,
                  isCritical && styles.alertCardCritical,
                ]}
              >
                <View style={styles.cardHeader}>
                  <View style={styles.badgeRow}>
                    {isUnread && <View style={styles.unreadDot} />}
                    <Text
                      style={[
                        styles.severityTag,
                        isCritical ? styles.severityTagCrit : styles.severityTagNorm,
                      ]}
                    >
                      {isCritical ? 'URGENT' : 'NOTIFICATION'}
                    </Text>
                    <Text style={styles.channelTag}>
                      {item.channel === 'whatsapp_dlp'
                        ? '💬 WhatsApp'
                        : item.channel === 'push_mobile_wearable'
                        ? '📱 Mobile Push'
                        : '✉️ Email'}
                    </Text>
                  </View>
                  <Text style={styles.timeText}>
                    {new Date(item.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </Text>
                </View>

                <Text style={styles.alertTitle}>{item.title}</Text>
                <Text style={styles.alertBody}>{item.body}</Text>

                <View style={styles.cardFooter}>
                  {isUnread ? (
                    <TouchableOpacity
                      style={styles.ackBtn}
                      onPress={() => handleMarkRead(item.id)}
                    >
                      <Text style={styles.ackBtnText}>✓ Acknowledge</Text>
                    </TouchableOpacity>
                  ) : (
                    <Text style={styles.readText}>Acknowledged</Text>
                  )}

                  {onNavigate && (
                    <TouchableOpacity
                      style={styles.inspectBtn}
                      onPress={() => onNavigate('incidents')}
                    >
                      <Text style={styles.inspectBtnText}>View Incident →</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            );
          })
        )}
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
  center: {
    flex: 1,
    backgroundColor: '#090d16',
    justifyContent: 'center',
    alignItems: 'center',
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
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#f8fafc',
  },
  subTitle: {
    fontSize: 13,
    color: '#94a3b8',
    marginTop: 2,
  },
  markAllBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  markAllText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  testPanel: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 14,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  testPanelTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#60a5fa',
    marginBottom: 4,
  },
  testPanelDesc: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 10,
    lineHeight: 16,
  },
  testBtnRow: {
    flexDirection: 'row',
    gap: 8,
  },
  testBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  testBtnWa: {
    backgroundColor: '#065f46',
  },
  testBtnCanary: {
    backgroundColor: '#991b1b',
  },
  btnDisabled: {
    opacity: 0.6,
  },
  testBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  feed: {
    gap: 12,
  },
  emptyCard: {
    backgroundColor: '#111827',
    padding: 32,
    borderRadius: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#f9fafb',
    marginBottom: 6,
  },
  emptyDesc: {
    fontSize: 13,
    color: '#9ca3af',
    textAlign: 'center',
    lineHeight: 18,
  },
  alertCard: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  alertCardUnread: {
    borderColor: '#3b82f6',
    backgroundColor: '#0e1b38',
  },
  alertCardCritical: {
    borderColor: '#ef4444',
    backgroundColor: '#261118',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ef4444',
  },
  severityTag: {
    fontSize: 10,
    fontWeight: '800',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  severityTagCrit: {
    backgroundColor: '#991b1b',
    color: '#fecaca',
  },
  severityTagNorm: {
    backgroundColor: '#1e3a8a',
    color: '#bfdbfe',
  },
  channelTag: {
    fontSize: 11,
    color: '#94a3b8',
  },
  timeText: {
    fontSize: 11,
    color: '#64748b',
  },
  alertTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 6,
  },
  alertBody: {
    fontSize: 13,
    color: '#cbd5e1',
    lineHeight: 18,
    marginBottom: 12,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    paddingTop: 10,
  },
  ackBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  ackBtnText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
  readText: {
    color: '#64748b',
    fontSize: 12,
  },
  inspectBtn: {
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  inspectBtnText: {
    color: '#60a5fa',
    fontSize: 12,
    fontWeight: '600',
  },
});
