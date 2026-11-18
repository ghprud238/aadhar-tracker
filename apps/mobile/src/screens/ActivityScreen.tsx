import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
} from 'react-native';
import { IncidentsScreen } from './IncidentsScreen';
import { AlertsScreen } from './AlertsScreen';

interface ActivityScreenProps {
  onRefreshAlertsCount?: () => void;
  initialTab?: 'incidents' | 'alerts';
}

export const ActivityScreen: React.FC<ActivityScreenProps> = ({
  onRefreshAlertsCount,
  initialTab = 'incidents',
}) => {
  const [activeTab, setActiveTab] = useState<'incidents' | 'alerts'>(initialTab);

  React.useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  return (
    <View style={styles.container}>
      {/* Segmented Control Header */}
      <View style={styles.segmentContainer}>
        <TouchableOpacity
          style={[styles.segmentBtn, activeTab === 'incidents' && styles.segmentBtnActive]}
          onPress={() => setActiveTab('incidents')}
          activeOpacity={0.8}
        >
          <Text style={[styles.segmentText, activeTab === 'incidents' && styles.segmentTextActive]}>
            ⚠️ Exposures & Breaches
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.segmentBtn, activeTab === 'alerts' && styles.segmentBtnActive]}
          onPress={() => setActiveTab('alerts')}
          activeOpacity={0.8}
        >
          <Text style={[styles.segmentText, activeTab === 'alerts' && styles.segmentTextActive]}>
            🔔 Live Alerts & Radar
          </Text>
        </TouchableOpacity>
      </View>

      {/* Screen Content */}
      <View style={styles.contentWrap}>
        {activeTab === 'incidents' ? (
          <IncidentsScreen />
        ) : (
          <AlertsScreen onRefreshAlertsCount={onRefreshAlertsCount} />
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  segmentContainer: {
    flexDirection: 'row',
    backgroundColor: '#131b2e',
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 8,
    borderRadius: 12,
    padding: 4,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  segmentBtnActive: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#38bdf8',
  },
  segmentText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  segmentTextActive: {
    color: '#f8fafc',
    fontWeight: '700',
  },
  contentWrap: {
    flex: 1,
  },
});
