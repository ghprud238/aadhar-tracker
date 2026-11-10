/**
 * Suraksha Mobile API Client
 * Connects to Identity Protection Platform backend with token management and biometric authentication.
 */
import {
  CompanionGlance,
  Identifier,
  Incident,
  RemediationAction,
  UserSession,
  NotificationItem,
} from '../types';

let API_BASE_URL = 'http://localhost:8000/api/v1';
let authToken: string | null = null;

export const setApiBaseUrl = (url: string) => {
  API_BASE_URL = url.replace(/\/$/, '');
};

export const getApiBaseUrl = () => API_BASE_URL;

export const setAuthToken = (token: string | null) => {
  authToken = token;
};

export const getAuthToken = () => authToken;

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Request-ID': 'mob_' + Math.random().toString(36).substring(2, 10),
    ...(options.headers as Record<string, string>),
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.error?.message || `Request failed with status ${res.status}`);
  }

  return json.data as T;
}

// Auth & Session
export const api = {
  async authenticate(email = 'resident@example.in', fullName = 'Aarav Sharma'): Promise<UserSession> {
    const session = await request<UserSession>(
      `/auth/callback?email=${encodeURIComponent(email)}&full_name=${encodeURIComponent(fullName)}`
    );
    authToken = session.session_id;
    return session;
  },

  async getSession(): Promise<UserSession> {
    return request<UserSession>('/session');
  },

  async getCompanionGlance(): Promise<CompanionGlance> {
    return request<CompanionGlance>('/companion/glance');
  },

  // Identifiers
  async getIdentifiers(): Promise<Identifier[]> {
    return request<Identifier[]>('/identifiers');
  },

  async addIdentifier(type: 'email' | 'phone', value: string): Promise<Identifier> {
    return request<Identifier>('/identifiers', {
      method: 'POST',
      body: JSON.stringify({ type, value }),
    });
  },

  async requestVerification(identifierId: string): Promise<{ demo_token: string }> {
    return request<{ demo_token: string }>(`/identifiers/${identifierId}/verification-challenges`, {
      method: 'POST',
    });
  },

  async completeVerification(identifierId: string, challengeToken: string): Promise<Identifier> {
    return request<Identifier>('/identifiers/verification-challenges/complete', {
      method: 'POST',
      body: JSON.stringify({ identifier_id: identifierId, challenge_token: challengeToken }),
    });
  },

  async pauseIdentifier(identifierId: string): Promise<Identifier> {
    return request<Identifier>(`/identifiers/${identifierId}/pause`, {
      method: 'POST',
    });
  },

  async resumeIdentifier(identifierId: string): Promise<Identifier> {
    return request<Identifier>(`/identifiers/${identifierId}/resume`, {
      method: 'POST',
    });
  },

  async deleteIdentifier(identifierId: string): Promise<{ deleted: boolean }> {
    return request<{ deleted: boolean }>(`/identifiers/${identifierId}`, {
      method: 'DELETE',
    });
  },

  // Scans & Incidents
  async runScan(identifierIds: string[]): Promise<{ scan_job_id: string; identifiers_queued: number }> {
    return request<{ scan_job_id: string; identifiers_queued: number }>('/scans', {
      method: 'POST',
      body: JSON.stringify({ identifier_ids: identifierIds }),
    });
  },

  async getIncidents(): Promise<Incident[]> {
    return request<Incident[]>('/incidents');
  },

  async disputeIncident(incidentId: string, reason: string): Promise<Incident> {
    return request<Incident>(`/incidents/${incidentId}/dispute`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  async getRemediations(incidentId: string): Promise<RemediationAction[]> {
    return request<RemediationAction[]>(`/incidents/${incidentId}/remediations`);
  },

  async completeRemediation(actionId: string): Promise<RemediationAction> {
    return request<RemediationAction>(`/remediations/${actionId}/complete`, {
      method: 'POST',
    });
  },

  // Aadhaar & PAN Assistance
  async confirmAadhaarLock(actionType = 'lock_biometrics', note = 'Resident confirmed biometrics locked via m-Aadhaar'): Promise<any> {
    return request('/identity-assistance/actions/confirm', {
      method: 'POST',
      body: JSON.stringify({
        action_type: actionType,
        confirmation_note: note,
      }),
    });
  },

  async reportSuspiciousActivity(payload: { incident_type: string; description: string; reference_id?: string }): Promise<any> {
    return request('/identity-assistance/report', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Security & Privacy
  async stepUpElevate(password = 'SecretMaster123!'): Promise<{ elevated: boolean; valid_for_seconds: number }> {
    return request<{ elevated: boolean; valid_for_seconds: number }>('/auth/step-up', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
  },

  async exportPrivacyData(): Promise<any> {
    return request('/privacy/export', {
      method: 'POST',
    });
  },

  async requestAccountErasure(): Promise<any> {
    return request('/privacy/erasure', {
      method: 'POST',
    });
  },

  // Notifications & Alerts
  async getNotifications(): Promise<NotificationItem[]> {
    return request<NotificationItem[]>('/notifications');
  },

  async markNotificationRead(id: string): Promise<any> {
    return request(`/notifications/${id}/read`, {
      method: 'POST',
    });
  },

  async markAllNotificationsRead(): Promise<any> {
    return request('/notifications/read-all', {
      method: 'POST',
    });
  },

  // Interactive Live Alert Simulation Triggers
  async simulateWhatsAppDLP(messageText: string, senderPhone = '+919876543210'): Promise<any> {
    return request('/integrations/whatsapp/simulate-share', {
      method: 'POST',
      body: JSON.stringify({ message_text: messageText, sender_phone: senderPhone }),
    });
  },

  async triggerCanaryTest(presetId = 'aadhaar_sandbox_1'): Promise<any> {
    return request('/identity-assistance/canary-test', {
      method: 'POST',
      body: JSON.stringify({ preset_id: presetId }),
    });
  },
};
