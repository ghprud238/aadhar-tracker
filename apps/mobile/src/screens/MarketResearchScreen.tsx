import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api } from '../services/api';

interface MarketSummary {
  total_responses: number;
  unlocked_biometrics_pct: number;
  unmasked_photocopy_sharing_pct: number;
  top_scam_categories: Record<string, number>;
  tafcop_unaware_pct: number;
  feature_demand_distribution: Record<string, number>;
  willingness_to_pay_distribution: Record<string, number>;
  market_readiness_score: number;
  investor_validation_summary: string;
}

export const MarketResearchScreen: React.FC<{ onNavigateToShield?: () => void }> = ({ onNavigateToShield }) => {
  const [activeTab, setActiveTab] = useState<'audit' | 'dashboard'>('audit');
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<MarketSummary | null>(null);

  // Survey Form State
  const [bioStatus, setBioStatus] = useState<'locked' | 'unlocked' | 'unaware'>('unlocked');
  const [sharesPhotocopy, setSharesPhotocopy] = useState<boolean>(true);
  const [selectedScams, setSelectedScams] = useState<string[]>(['electricity_sms', 'digital_arrest']);
  const [tafcopStatus, setTafcopStatus] = useState<'checked_ok' | 'never_checked' | 'found_unknown'>('never_checked');
  const [desiredFeature, setDesiredFeature] = useState<string>('biometric_auto_relock');
  const [payModel, setPayModel] = useState<'free_via_bank' | 'paid_monthly_49' | 'paid_annual_199' | 'free_only'>('free_via_bank');
  const [userCity, setUserCity] = useState<string>('Bengaluru');
  const [submitting, setSubmitting] = useState(false);
  const [auditResult, setAuditResult] = useState<{ riskLevel: string; score: number } | null>(null);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const data = await api.getMarketResearchSummary();
      setSummary(data);
    } catch (err: any) {
      console.warn('Failed to load market summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const toggleScam = (scamKey: string) => {
    if (selectedScams.includes(scamKey)) {
      setSelectedScams(selectedScams.filter((s) => s !== scamKey));
    } else {
      setSelectedScams([...selectedScams, scamKey]);
    }
  };

  const handleSubmitAudit = async () => {
    setSubmitting(true);
    try {
      await api.submitMarketResearchSurvey({
        biometrics_locked_status: bioStatus,
        shared_unmasked_photocopies: sharesPhotocopy,
        received_scam_contacts: selectedScams,
        tafcop_sim_awareness: tafcopStatus,
        most_valued_feature: desiredFeature,
        willingness_to_pay_model: payModel,
        user_city: userCity,
      });

      // Compute immediate consumer score
      let riskScore = 0;
      if (bioStatus !== 'locked') riskScore += 35;
      if (sharesPhotocopy) riskScore += 25;
      if (tafcopStatus !== 'checked_ok') riskScore += 20;
      if (selectedScams.length > 0) riskScore += Math.min(20, selectedScams.length * 10);

      const level = riskScore >= 70 ? 'CRITICAL VULNERABILITY' : riskScore >= 40 ? 'ELEVATED RISK' : 'LOW RISK';
      setAuditResult({ riskLevel: level, score: riskScore });

      Alert.alert(
        '✅ Audit Recorded Anonymously',
        `Your vulnerability score is ${riskScore}/100 (${level}). Your response has been added to our live national market validation dataset.`
      );
      await fetchSummary();
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.headerIcon}>🔬</Text>
          <View>
            <Text style={styles.headerTitle}>Market Research & Validation</Text>
            <Text style={styles.headerSubtitle}>Citizen Cyber Hygiene & Empirical Threat Telemetry</Text>
          </View>
        </View>

        {/* Tab Switcher */}
        <View style={styles.tabBar}>
          <TouchableOpacity
            style={[styles.tabBtn, activeTab === 'audit' && styles.tabBtnActive]}
            onPress={() => setActiveTab('audit')}
          >
            <Text style={[styles.tabBtnText, activeTab === 'audit' && styles.tabBtnTextActive]}>
              📝 60s Consumer Audit
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabBtn, activeTab === 'dashboard' && styles.tabBtnActive]}
            onPress={() => {
              setActiveTab('dashboard');
              fetchSummary();
            }}
          >
            <Text style={[styles.tabBtnText, activeTab === 'dashboard' && styles.tabBtnTextActive]}>
              📊 Market Intelligence
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Tab 1: 60-Second Consumer Cyber Hygiene Audit */}
      {activeTab === 'audit' && (
        <View style={styles.section}>
          <View style={styles.introCard}>
            <Text style={styles.introTitle}>🔍 Validate Your Identity Exposure</Text>
            <Text style={styles.introText}>
              Answer 6 quick questions to discover your AePS biometric, Aadhaar photocopy, and telecom risk.
              Your answers anonymously train our threat models and validate the consumer demand thesis.
            </Text>
          </View>

          {/* Q1: Biometrics */}
          <View style={styles.card}>
            <Text style={styles.qNum}>QUESTION 1 OF 6</Text>
            <Text style={styles.qTitle}>Are your Aadhaar biometrics locked on the official UIDAI portal?</Text>
            <Text style={styles.qHint}>Unlocked biometrics allow micro-ATM AePS cash withdrawals without OTP.</Text>
            <View style={styles.optionsWrap}>
              {[
                { key: 'locked', label: '🔒 Yes, Locked on mAadhaar' },
                { key: 'unlocked', label: '⚠️ Unlocked (Fingerprints Active)' },
                { key: 'unaware', label: '❓ Never heard of Biometric Lock' },
              ].map((opt) => (
                <TouchableOpacity
                  key={opt.key}
                  style={[styles.optionBtn, bioStatus === opt.key && styles.optionBtnActive]}
                  onPress={() => setBioStatus(opt.key as any)}
                >
                  <Text style={[styles.optionText, bioStatus === opt.key && styles.optionTextActive]}>
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Q2: Photocopy Sharing */}
          <View style={styles.card}>
            <Text style={styles.qNum}>QUESTION 2 OF 6</Text>
            <Text style={styles.qTitle}>Do you leave unmasked Aadhaar photocopies at hotel check-ins or car rentals?</Text>
            <Text style={styles.qHint}>Unmasked copies are regularly leaked or reused by loan mule syndicates.</Text>
            <View style={styles.optionsWrap}>
              <TouchableOpacity
                style={[styles.optionBtn, sharesPhotocopy && styles.optionBtnActive]}
                onPress={() => setSharesPhotocopy(true)}
              >
                <Text style={[styles.optionText, sharesPhotocopy && styles.optionTextActive]}>
                  📄 Yes, I routinely give regular photocopies
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.optionBtn, !sharesPhotocopy && styles.optionBtnActive]}
                onPress={() => setSharesPhotocopy(false)}
              >
                <Text style={[styles.optionText, !sharesPhotocopy && styles.optionTextActive]}>
                  🛡️ No, I mask numbers or use digital watermarks
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Q3: Scam Contacts */}
          <View style={styles.card}>
            <Text style={styles.qNum}>QUESTION 3 OF 6</Text>
            <Text style={styles.qTitle}>Which scams or suspicious messages have you received in the past 6 months?</Text>
            <Text style={styles.qHint}>Select all that apply to measure current attack distribution.</Text>
            <View style={styles.optionsWrap}>
              {[
                { key: 'digital_arrest', label: '🚨 Digital Arrest (Fake Police / CBI Skype calls)' },
                { key: 'electricity_sms', label: '⚡ Urgent Power Cut / Bill Update SMS' },
                { key: 'telegram_part_time', label: '💼 Telegram Part-Time Review & Like Jobs' },
                { key: 'courier_customs', label: '📦 Courier Customs Hold / FedEx Narcotics SMS' },
                { key: 'sideload_apk', label: '📱 Link asking to install an .APK file' },
              ].map((scam) => {
                const isSelected = selectedScams.includes(scam.key);
                return (
                  <TouchableOpacity
                    key={scam.key}
                    style={[styles.optionBtn, isSelected && styles.optionBtnActive]}
                    onPress={() => toggleScam(scam.key)}
                  >
                    <Text style={[styles.optionText, isSelected && styles.optionTextActive]}>
                      {isSelected ? '☑ ' : '☐ '} {scam.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {/* Q4: TAFCOP SIM Awareness */}
          <View style={styles.card}>
            <Text style={styles.qNum}>QUESTION 4 OF 6</Text>
            <Text style={styles.qTitle}>Have you checked DoT Sanchar Saathi (TAFCOP) for ghost SIMs in your name?</Text>
            <Text style={styles.qHint}>Fraudsters use Aadhaar identity theft to obtain unauthorized SIMs.</Text>
            <View style={styles.optionsWrap}>
              {[
                { key: 'never_checked', label: '❌ Never checked TAFCOP' },
                { key: 'checked_ok', label: '✅ Checked and all SIMs are mine' },
                { key: 'found_unknown', label: '⚠️ Found unknown numbers registered' },
              ].map((opt) => (
                <TouchableOpacity
                  key={opt.key}
                  style={[styles.optionBtn, tafcopStatus === opt.key && styles.optionBtnActive]}
                  onPress={() => setTafcopStatus(opt.key as any)}
                >
                  <Text style={[styles.optionText, tafcopStatus === opt.key && styles.optionTextActive]}>
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Q5: Desired Feature */}
          <View style={styles.card}>
            <Text style={styles.qNum}>QUESTION 5 OF 6</Text>
            <Text style={styles.qTitle}>Which feature would make you feel safest?</Text>
            <View style={styles.optionsWrap}>
              {[
                { key: 'biometric_auto_relock', label: '🔒 10-Min Biometric Auto-Relock Timer' },
                { key: 'scam_radar', label: '🚨 Real-Time Digital Arrest & Malicious APK Radar' },
                { key: 'panic_pack', label: '⚡ Emergency SOS 1-Tap Panic Pack (Stolen Phone)' },
                { key: 'ephemeral_passes', label: '⏱️ Self-Destructing 1-View Watermarked Passes' },
              ].map((opt) => (
                <TouchableOpacity
                  key={opt.key}
                  style={[styles.optionBtn, desiredFeature === opt.key && styles.optionBtnActive]}
                  onPress={() => setDesiredFeature(opt.key)}
                >
                  <Text style={[styles.optionText, desiredFeature === opt.key && styles.optionTextActive]}>
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Q6: Commercial Model Preference */}
          <View style={styles.card}>
            <Text style={styles.qNum}>QUESTION 6 OF 6</Text>
            <Text style={styles.qTitle}>How would you prefer this security to be provided?</Text>
            <View style={styles.optionsWrap}>
              {[
                { key: 'free_via_bank', label: '🏦 Free, embedded inside my HDFC/SBI/UPI app' },
                { key: 'paid_monthly_49', label: '💳 ₹49 / month direct standalone subscription' },
                { key: 'paid_annual_199', label: '👨‍👩‍👧 ₹199 / year complete Family Shield' },
                { key: 'free_only', label: '🆓 Only if 100% free with no monetization' },
              ].map((opt) => (
                <TouchableOpacity
                  key={opt.key}
                  style={[styles.optionBtn, payModel === opt.key && styles.optionBtnActive]}
                  onPress={() => setPayModel(opt.key as any)}
                >
                  <Text style={[styles.optionText, payModel === opt.key && styles.optionTextActive]}>
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* City Selection */}
          <View style={styles.card}>
            <Text style={styles.qTitle}>Your City / Region</Text>
            <View style={styles.cityRow}>
              {['Bengaluru', 'Mumbai', 'Delhi NCR', 'Hyderabad', 'Tier-2 Town'].map((city) => (
                <TouchableOpacity
                  key={city}
                  style={[styles.cityChip, userCity === city && styles.cityChipActive]}
                  onPress={() => setUserCity(city)}
                >
                  <Text style={[styles.cityChipText, userCity === city && styles.cityChipTextActive]}>{city}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Submit Button */}
          <TouchableOpacity
            style={styles.submitBtn}
            onPress={handleSubmitAudit}
            disabled={submitting}
            activeOpacity={0.8}
          >
            {submitting ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.submitBtnText}>📊 Submit Anonymized Audit & See Results</Text>
            )}
          </TouchableOpacity>

          {/* Instant Audit Result */}
          {auditResult && (
            <View style={styles.auditResultBox}>
              <Text style={styles.auditResultTitle}>Your Personal Vulnerability Score</Text>
              <Text style={styles.auditScoreNum}>{auditResult.score} / 100</Text>
              <Text style={styles.auditLevelText}>{auditResult.riskLevel}</Text>
              <Text style={styles.auditRecText}>
                {auditResult.score >= 50
                  ? 'Urgent Action Recommended: Lock your Aadhaar biometrics immediately on mAadhaar and stop providing unmasked photocopies.'
                  : 'Good posture! Keep biometrics locked and use watermarked passes for hotel check-ins.'}
              </Text>
              {onNavigateToShield && (
                <TouchableOpacity style={styles.actionBtn} onPress={onNavigateToShield}>
                  <Text style={styles.actionBtnText}>🛡️ Open Shield & Take Action</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>
      )}

      {/* Tab 2: Live Market Intelligence / Founder & Investor Dashboard */}
      {activeTab === 'dashboard' && (
        <View style={styles.section}>
          {loading ? (
            <ActivityIndicator size="large" color="#3b82f6" style={{ marginTop: 32 }} />
          ) : summary ? (
            <>
              {/* Readiness Score Banner */}
              <View style={styles.scoreBanner}>
                <View style={styles.scoreLeft}>
                  <Text style={styles.scoreSub}>MARKET READINESS INDEX</Text>
                  <Text style={styles.scoreBig}>{summary.market_readiness_score}/100</Text>
                  <Text style={styles.scoreDesc}>Extreme Problem Severity & Regulatory Urgency</Text>
                </View>
                <View style={styles.sampleBadge}>
                  <Text style={styles.sampleNum}>N = {summary.total_responses}</Text>
                  <Text style={styles.sampleLabel}>Verified Audits</Text>
                </View>
              </View>

              {/* 4 Key Validation Statistics */}
              <View style={styles.statsGrid}>
                <View style={styles.statCard}>
                  <Text style={styles.statEmoji}>🚨</Text>
                  <Text style={styles.statVal}>{summary.unlocked_biometrics_pct}%</Text>
                  <Text style={styles.statLabel}>Biometrics Unlocked (AePS Vulnerable)</Text>
                </View>
                <View style={styles.statCard}>
                  <Text style={styles.statEmoji}>📄</Text>
                  <Text style={styles.statVal}>{summary.unmasked_photocopy_sharing_pct}%</Text>
                  <Text style={styles.statLabel}>Share Raw Unmasked Photocopies</Text>
                </View>
                <View style={styles.statCard}>
                  <Text style={styles.statEmoji}>📱</Text>
                  <Text style={styles.statVal}>{summary.tafcop_unaware_pct}%</Text>
                  <Text style={styles.statLabel}>TAFCOP Ghost SIM Blind Spot</Text>
                </View>
                <View style={styles.statCard}>
                  <Text style={styles.statEmoji}>🏦</Text>
                  <Text style={styles.statVal}>
                    {Math.round(
                      ((summary.willingness_to_pay_distribution['free_via_bank'] || 0) /
                        (summary.total_responses || 1)) *
                        100
                    )}%
                  </Text>
                  <Text style={styles.statLabel}>Demand Bank-Embedded Protection</Text>
                </View>
              </View>

              {/* Top Scams Encountered */}
              <View style={styles.metricCard}>
                <Text style={styles.cardHeader}>🚨 Most Prevalent Indian Scam Vectors</Text>
                {Object.entries(summary.top_scam_categories).map(([scam, count]) => {
                  const pct = Math.round((count / (summary.total_responses || 1)) * 100);
                  const names: Record<string, string> = {
                    digital_arrest: 'Digital Arrest (Fake Police/CBI)',
                    electricity_sms: 'Electricity Disconnection SMS',
                    telegram_part_time: 'Telegram Job / Review Scams',
                    courier_customs: 'Courier Customs / Narcotics',
                    sideload_apk: 'Malicious .APK Sideloading',
                  };
                  return (
                    <View key={scam} style={styles.barItem}>
                      <View style={styles.barLabels}>
                        <Text style={styles.barName}>{names[scam] || scam}</Text>
                        <Text style={styles.barPct}>{pct}% ({count})</Text>
                      </View>
                      <View style={styles.barTrack}>
                        <View style={[styles.barFill, { width: `${Math.min(100, pct)}%` }]} />
                      </View>
                    </View>
                  );
                })}
              </View>

              {/* Commercial Preference Breakdown */}
              <View style={styles.metricCard}>
                <Text style={styles.cardHeader}>💰 Commercial Willingness-to-Pay Validation</Text>
                <Text style={styles.metricSub}>
                  Validates why consumer subscriptions fail in India and why the B2B embedded SDK pivot is mandatory.
                </Text>
                {Object.entries(summary.willingness_to_pay_distribution).map(([model, count]) => {
                  const pct = Math.round((count / (summary.total_responses || 1)) * 100);
                  const labels: Record<string, string> = {
                    free_via_bank: '🏦 Embedded in Banking/Fintech App (B2B)',
                    paid_monthly_49: '💳 Direct ₹49/month Subscription',
                    paid_annual_199: '👨‍👩‍👧 Direct ₹199/year Family Plan',
                    free_only: '🆓 Free Only (No Willingness to Pay)',
                  };
                  return (
                    <View key={model} style={styles.barItem}>
                      <View style={styles.barLabels}>
                        <Text style={styles.barName}>{labels[model] || model}</Text>
                        <Text style={styles.barPct}>{pct}%</Text>
                      </View>
                      <View style={styles.barTrack}>
                        <View
                          style={[
                            styles.barFill,
                            {
                              width: `${Math.min(100, pct)}%`,
                              backgroundColor: model === 'free_via_bank' ? '#10b981' : '#3b82f6',
                            },
                          ]}
                        />
                      </View>
                    </View>
                  );
                })}
              </View>

              {/* Executive Pitch Synthesis */}
              <View style={styles.pitchCard}>
                <Text style={styles.pitchTitle}>💡 The Empirical Investor & B2B Thesis</Text>
                <Text style={styles.pitchText}>{summary.investor_validation_summary}</Text>
                <View style={styles.pitchBullet}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={styles.bulletText}>
                    <Text style={{ fontWeight: '700', color: '#f8fafc' }}>Zero Consumer Friction: </Text>
                    Consumers will not pay ₹199/year directly, but eagerly adopt free on-device scam defense.
                  </Text>
                </View>
                <View style={styles.pitchBullet}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={styles.bulletText}>
                    <Text style={{ fontWeight: '700', color: '#f8fafc' }}>High-Margin B2B Checkwriters: </Text>
                    Banks and NBFCs pay ₹2/call and ₹4-8/MAU to stop their own multi-crore fraud write-offs.
                  </Text>
                </View>
                <View style={styles.pitchBullet}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={styles.bulletText}>
                    <Text style={{ fontWeight: '700', color: '#f8fafc' }}>Data Moat Flywheel: </Text>
                    Consumer scam reports train the heuristic models that make the B2B lending fraud API invincible.
                  </Text>
                </View>
              </View>

              <TouchableOpacity style={styles.refreshBtn} onPress={fetchSummary}>
                <Text style={styles.refreshBtnText}>🔄 Refresh Live Analytics Feed</Text>
              </TouchableOpacity>
            </>
          ) : (
            <Text style={styles.emptyText}>No research data available.</Text>
          )}
        </View>
      )}
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
    marginBottom: 20,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#f8fafc',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 4,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  tabBtnActive: {
    backgroundColor: '#2563eb',
  },
  tabBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94a3b8',
  },
  tabBtnTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  section: {
    marginTop: 8,
  },
  introCard: {
    backgroundColor: '#131b2e',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e3a8a',
    marginBottom: 16,
  },
  introTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#60a5fa',
    marginBottom: 6,
  },
  introText: {
    fontSize: 12,
    color: '#cbd5e1',
    lineHeight: 18,
  },
  card: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  qNum: {
    fontSize: 10,
    fontWeight: '800',
    color: '#3b82f6',
    letterSpacing: 1,
    marginBottom: 4,
  },
  qTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  qHint: {
    fontSize: 11,
    color: '#64748b',
    marginBottom: 12,
  },
  optionsWrap: {
    gap: 8,
  },
  optionBtn: {
    backgroundColor: '#1e293b',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  optionBtnActive: {
    backgroundColor: '#1e3a8a',
    borderColor: '#3b82f6',
  },
  optionText: {
    fontSize: 13,
    color: '#94a3b8',
    fontWeight: '500',
  },
  optionTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  cityRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 8,
  },
  cityChip: {
    backgroundColor: '#1e293b',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#334155',
  },
  cityChipActive: {
    backgroundColor: '#2563eb',
    borderColor: '#60a5fa',
  },
  cityChipText: {
    fontSize: 11,
    color: '#94a3b8',
  },
  cityChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  submitBtn: {
    backgroundColor: '#2563eb',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginVertical: 12,
  },
  submitBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffffff',
  },
  auditResultBox: {
    backgroundColor: '#1e1b4b',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#6366f1',
    alignItems: 'center',
    marginTop: 12,
  },
  auditResultTitle: {
    fontSize: 12,
    color: '#a5b4fc',
    fontWeight: '600',
  },
  auditScoreNum: {
    fontSize: 36,
    fontWeight: '900',
    color: '#ffffff',
    marginVertical: 4,
  },
  auditLevelText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#f87171',
    letterSpacing: 0.5,
  },
  auditRecText: {
    fontSize: 11,
    color: '#cbd5e1',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 16,
  },
  actionBtn: {
    backgroundColor: '#4f46e5',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginTop: 12,
  },
  actionBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#ffffff',
  },
  // Dashboard Styles
  scoreBanner: {
    backgroundColor: '#172554',
    borderRadius: 16,
    padding: 18,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2563eb',
    marginBottom: 16,
  },
  scoreLeft: {
    flex: 1,
  },
  scoreSub: {
    fontSize: 10,
    fontWeight: '800',
    color: '#93c5fd',
    letterSpacing: 1,
  },
  scoreBig: {
    fontSize: 34,
    fontWeight: '900',
    color: '#ffffff',
    marginVertical: 2,
  },
  scoreDesc: {
    fontSize: 11,
    color: '#bfdbfe',
  },
  sampleBadge: {
    backgroundColor: '#1e40af',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  sampleNum: {
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  sampleLabel: {
    fontSize: 9,
    color: '#93c5fd',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 16,
  },
  statCard: {
    width: '48%',
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  statEmoji: {
    fontSize: 20,
    marginBottom: 6,
  },
  statVal: {
    fontSize: 22,
    fontWeight: '800',
    color: '#f8fafc',
  },
  statLabel: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 4,
    lineHeight: 14,
  },
  metricCard: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 16,
  },
  cardHeader: {
    fontSize: 13,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 4,
  },
  metricSub: {
    fontSize: 11,
    color: '#64748b',
    marginBottom: 12,
    lineHeight: 15,
  },
  barItem: {
    marginBottom: 10,
  },
  barLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  barName: {
    fontSize: 11,
    color: '#cbd5e1',
  },
  barPct: {
    fontSize: 11,
    fontWeight: '700',
    color: '#60a5fa',
  },
  barTrack: {
    height: 6,
    backgroundColor: '#1e293b',
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    backgroundColor: '#3b82f6',
    borderRadius: 3,
  },
  pitchCard: {
    backgroundColor: '#0b1329',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1d4ed8',
    marginBottom: 16,
  },
  pitchTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#60a5fa',
    marginBottom: 8,
  },
  pitchText: {
    fontSize: 12,
    color: '#cbd5e1',
    lineHeight: 18,
    marginBottom: 12,
  },
  pitchBullet: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  bulletDot: {
    fontSize: 14,
    color: '#3b82f6',
    marginRight: 6,
    lineHeight: 16,
  },
  bulletText: {
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 16,
    flex: 1,
  },
  refreshBtn: {
    backgroundColor: '#1e293b',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  refreshBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94a3b8',
  },
  emptyText: {
    color: '#64748b',
    textAlign: 'center',
    marginVertical: 20,
  },
});
