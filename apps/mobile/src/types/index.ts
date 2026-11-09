export type ShieldStatus = 'secure' | 'warning' | 'critical';

export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';

export type IncidentState = 'new' | 'acknowledged' | 'action_in_progress' | 'resolved' | 'disputed';

export interface Identifier {
  id: string;
  type: 'email' | 'phone' | 'aadhaar' | 'pan';
  masked_value: string;
  state: 'pending_verification' | 'active' | 'paused' | 'revoked';
  monitoring_enabled: boolean;
  verified_at: string | null;
  created_at: string;
}

export interface Incident {
  id: string;
  title: string;
  source_type: string;
  breach_date: string | null;
  severity: IncidentSeverity;
  confidence: number;
  priority_score: number;
  state: IncidentState;
  exposed_fields: string[];
  description_sanitized: string;
  created_at: string;
}

export interface RemediationAction {
  id: string;
  incident_id: string;
  title: string;
  description: string;
  priority: string;
  state: 'pending' | 'completed' | 'dismissed';
  suggested_action_type: string;
  target_url?: string;
  completed_at?: string;
}

export interface CompanionGlance {
  shield_status: ShieldStatus;
  active_incidents: number;
  highest_severity: string;
  active_monitored_count: number;
  biometrics_locked: boolean;
  urgent_alert?: {
    incident_id: string;
    title: string;
    severity: string;
    priority_score: number;
  } | null;
  last_synced_at: string;
}

export interface UserSession {
  subject_id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: string;
  session_id: string;
  step_up_elevated_until?: string | null;
}

export interface AadhaarStep {
  step: number;
  title: string;
  instruction: string;
  portal_url?: string;
}
