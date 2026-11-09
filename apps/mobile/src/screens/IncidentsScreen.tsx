import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import { api } from '../services/api';
import { Incident, RemediationAction } from '../types';

export const IncidentsScreen: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [remediations, setRemediations] = useState<RemediationAction[]>([]);
  const [loadingRemediations, setLoadingRemediations] = useState(false);
  const [disputeModalVisible, setDisputeModalVisible] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');
  const [submittingDispute, setSubmittingDispute] = useState(false);

  const fetchIncidents = async () => {
    try {
      const data = await api.getIncidents();
      setIncidents(data);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const openRemediations = async (incident: Incident) => {
    setSelectedIncident(incident);
    setLoadingRemediations(true);
    try {
      const actions = await api.getRemediations(incident.id);
      setRemediations(actions);
    } catch (err: any) {
      Alert.alert('Remediation Error', err.message);
    } finally {
      setLoadingRemediations(false);
    }
  };

  const handleCompleteAction = async (actionId: string) => {
    try {
      await api.completeRemediation(actionId);
      Alert.alert('Action Completed', 'Your protection score has been updated.');
      if (selectedIncident) {
        const updated = await api.getRemediations(selectedIncident.id);
        setRemediations(updated);
      }
      await fetchIncidents();
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleDispute = async () => {
    if (!selectedIncident || !disputeReason.trim()) return;
    setSubmittingDispute(true);
    try {
      await api.disputeIncident(selectedIncident.id, disputeReason.trim());
      Alert.alert('Dispute Logged', 'Incident marked as disputed. It has been excluded from your active threat count.');
      setDisputeModalVisible(false);
      setSelectedIncident(null);
      setDisputeReason('');
      await fetchIncidents();
    } catch (err: any) {
      Alert.alert('Dispute Failed', err.message);
    } finally {
      setSubmittingDispute(false);
    }
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case 'critical':
        return { bg: '#450a0a', text: '#f87171', border: '#ef4444' };
      case 'high':
        return { bg: '#431407', text: '#fb923c', border: '#f97316' };
      case 'medium':
        return { bg: '#422006', text: '#facc15', border: '#eab308' };
      default:
        return { bg: '#064e3b', text: '#34d399', border: '#10b981' };
    }
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
        <Text style={styles.title}>Breach & Exposure Incidents</Text>
        <Text style={styles.subtitle}>
          Deterministic severity scoring • Attribution to verified intelligence sources
        </Text>
      </View>

      {incidents.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>🛡️</Text>
          <Text style={styles.emptyTitle}>No Breaches Detected</Text>
          <Text style={styles.emptySub}>
            None of your monitored identifiers match known breach corpuses or dark web listings.
          </Text>
        </View>
      ) : (
        incidents.map((inc) => {
          const sev = getSeverityStyle(inc.severity);
          return (
            <View key={inc.id} style={styles.incidentCard}>
              <View style={styles.incidentTop}>
                <View
                  style={[
                    styles.severityBadge,
                    { backgroundColor: sev.bg, borderColor: sev.border, borderWidth: 1 },
                  ]}
                >
                  <Text style={[styles.severityText, { color: sev.text }]}>
                    {inc.severity.toUpperCase()}
                  </Text>
                </View>
                <Text style={styles.scoreText}>Priority: {inc.priority_score}</Text>
              </View>

              <Text style={styles.incidentTitle}>{inc.title}</Text>
              <Text style={styles.sourceMeta}>
                Source: {inc.source_type.toUpperCase()} • Confidence: {Math.round(inc.confidence * 100)}%
                {inc.breach_date ? ` • Breach: ${inc.breach_date}` : ''}
              </Text>

              {inc.description_sanitized ? (
                <Text style={styles.descText} numberOfLines={3}>
                  {inc.description_sanitized}
                </Text>
              ) : null}

              {inc.exposed_fields?.length > 0 && (
                <View style={styles.fieldsContainer}>
                  <Text style={styles.fieldsLabel}>Exposed:</Text>
                  <View style={styles.tagsRow}>
                    {inc.exposed_fields.map((f, idx) => (
                      <View key={idx} style={styles.fieldTag}>
                        <Text style={styles.fieldTagText}>{f.replace('_', ' ')}</Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}

              <View style={styles.cardActions}>
                <TouchableOpacity
                  style={styles.remediationBtn}
                  onPress={() => openRemediations(inc)}
                >
                  <Text style={styles.remediationBtnText}>Take Action / Fix →</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.disputeBtn}
                  onPress={() => {
                    setSelectedIncident(inc);
                    setDisputeModalVisible(true);
                  }}
                >
                  <Text style={styles.disputeBtnText}>Dispute</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })
      )}

      {/* Remediation Modal */}
      <Modal visible={!!selectedIncident && !disputeModalVisible} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Remediation Checklist</Text>
              <TouchableOpacity onPress={() => setSelectedIncident(null)}>
                <Text style={styles.closeBtn}>✕</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.modalSub}>{selectedIncident?.title}</Text>

            {loadingRemediations ? (
              <ActivityIndicator color="#3b82f6" style={{ marginVertical: 20 }} />
            ) : remediations.length === 0 ? (
              <Text style={styles.emptySub}>No outstanding actions required for this incident.</Text>
            ) : (
              <ScrollView style={{ maxHeight: 320 }}>
                {remediations.map((action) => (
                  <View key={action.id} style={styles.actionItem}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.actionItemTitle}>{action.title}</Text>
                      <Text style={styles.actionItemDesc}>{action.description}</Text>
                    </View>
                    {action.state === 'completed' ? (
                      <Text style={styles.completedBadge}>✓ Done</Text>
                    ) : (
                      <TouchableOpacity
                        style={styles.markDoneBtn}
                        onPress={() => handleCompleteAction(action.id)}
                      >
                        <Text style={styles.markDoneBtnText}>Mark Done</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                ))}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      {/* Dispute Modal */}
      <Modal visible={disputeModalVisible} animationType="fade" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Dispute Incident</Text>
            <Text style={styles.modalSub}>
              Tell us why this incident does not pertain to your identity. Disputing marks the incident as
              contested and excludes it from active alerts.
            </Text>
            <TextInput
              style={[styles.input, { height: 80, textAlignVertical: 'top' }]}
              multiline
              placeholder="e.g. I never opened an account with this service..."
              placeholderTextColor="#64748b"
              value={disputeReason}
              onChangeText={setDisputeReason}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.btnSecondary}
                onPress={() => setDisputeModalVisible(false)}
                disabled={submittingDispute}
              >
                <Text style={styles.btnSecondaryText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btnPrimary, { backgroundColor: '#ef4444' }]}
                onPress={handleDispute}
                disabled={submittingDispute}
              >
                {submittingDispute ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.btnPrimaryText}>Submit Dispute</Text>
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
    lineHeight: 16,
  },
  emptyCard: {
    backgroundColor: '#111827',
    borderRadius: 14,
    padding: 32,
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
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  emptySub: {
    fontSize: 13,
    color: '#94a3b8',
    textAlign: 'center',
    lineHeight: 18,
  },
  incidentCard: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
    marginBottom: 14,
  },
  incidentTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  severityText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  scoreText: {
    fontSize: 12,
    color: '#94a3b8',
    fontWeight: '600',
  },
  incidentTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  sourceMeta: {
    fontSize: 11,
    color: '#64748b',
    marginBottom: 8,
  },
  descText: {
    fontSize: 13,
    color: '#94a3b8',
    lineHeight: 18,
    marginBottom: 12,
  },
  fieldsContainer: {
    marginBottom: 12,
  },
  fieldsLabel: {
    fontSize: 11,
    color: '#64748b',
    fontWeight: '600',
    marginBottom: 4,
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  fieldTag: {
    backgroundColor: '#1f2937',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  fieldTagText: {
    color: '#cbd5e1',
    fontSize: 11,
  },
  cardActions: {
    flexDirection: 'row',
    gap: 10,
    borderTopWidth: 1,
    borderTopColor: '#1f2937',
    paddingTop: 12,
  },
  remediationBtn: {
    backgroundColor: '#2563eb',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 6,
    flex: 1,
    alignItems: 'center',
  },
  remediationBtnText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 12,
  },
  disputeBtn: {
    backgroundColor: '#1f2937',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#374151',
    alignItems: 'center',
  },
  disputeBtnText: {
    color: '#94a3b8',
    fontSize: 12,
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
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#f8fafc',
  },
  closeBtn: {
    fontSize: 20,
    color: '#94a3b8',
    padding: 4,
  },
  modalSub: {
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 16,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#090d16',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  actionItemTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#f8fafc',
    marginBottom: 2,
  },
  actionItemDesc: {
    fontSize: 11,
    color: '#94a3b8',
  },
  completedBadge: {
    color: '#10b981',
    fontWeight: '600',
    fontSize: 12,
    paddingHorizontal: 8,
  },
  markDoneBtn: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  markDoneBtnText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
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
  },
  btnPrimary: {
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
