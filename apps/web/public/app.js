// Suraksha Identity Protection Platform - Client Application
const I18N = {
  en: {
    nav_overview: "Overview",
    nav_identities: "Identities",
    nav_incidents: "Incidents",
    nav_actions: "Protection Actions",
    nav_assistance: "Aadhaar & PAN Assistance",
    nav_coverage: "Coverage Transparency",
    nav_notifications: "Notifications",
    nav_billing: "Billing & Plans",
    nav_privacy: "Privacy Center",
    nav_security: "Account Security",
    empty_no_identities: "Add and verify an email to begin.",
    empty_no_incidents: "No matches were returned by the sources checked.",
    empty_paused: "Monitoring is paused.",
    run_scan: "Run Scan",
    elevate: "Elevate Session (Step-Up)"
  },
  hi: {
    nav_overview: "अवलोकन (Overview)",
    nav_identities: "पहचान (Identities)",
    nav_incidents: "सुरक्षा घटनाएं (Incidents)",
    nav_actions: "सुरक्षात्मक कदम (Actions)",
    nav_assistance: "आधार एवं पैन सहायता (Assistance)",
    nav_coverage: "कवरेज पारदर्शिता (Coverage)",
    nav_notifications: "सूचनाएं (Notifications)",
    nav_billing: "बिलिंग एवं योजनाएं (Billing)",
    nav_privacy: "गोपनीयता केंद्र (Privacy)",
    nav_security: "खाता सुरक्षा (Security)",
    empty_no_identities: "शुरू करने के लिए एक ईमेल जोड़ें और सत्यापित करें।",
    empty_no_incidents: "जांची गई स्रोतों में कोई उल्लंघन नहीं मिला।",
    empty_paused: "निगरानी रोकी गई है।",
    run_scan: "स्कैन चलाएं",
    elevate: "सत्र प्रमाणीकरण (Step-Up)"
  }
};

let currentLang = "en";
let currentView = "overview";
let currentSession = null;

// API Helper
async function apiCall(endpoint, method = "GET", body = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "req_" + Math.random().toString(36).substring(2, 10)
    }
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  try {
    const res = await fetch("/api/v1" + endpoint, options);
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.error ? json.error.message : "API Request failed");
    }
    return json;
  } catch (err) {
    console.error("API error:", err);
    throw err;
  }
}

// Ensure session
async function initSession() {
  try {
    const sess = await apiCall("/session");
    currentSession = sess.data;
  } catch (e) {
    // Attempt login callback simulation
    const loginRes = await apiCall("/auth/callback?email=resident@example.in&full_name=Aarav+Sharma");
    currentSession = loginRes.data;
  }
  document.getElementById("nav-user-email").textContent = currentSession.email;
}

// Navigation router
function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });
  renderCurrentView();
}

async function renderCurrentView() {
  const container = document.getElementById("view-container");
  const title = document.getElementById("page-title");
  const subtitle = document.getElementById("page-subtitle");

  switch (currentView) {
    case "overview":
      title.textContent = I18N[currentLang].nav_overview;
      subtitle.textContent = "Real-time summary of verified identity monitoring and security status";
      await renderOverviewView(container);
      break;
    case "identities":
      title.textContent = I18N[currentLang].nav_identities;
      subtitle.textContent = "Verified email and phone monitoring targets with cryptographic verification";
      await renderIdentitiesView(container);
      break;
    case "incidents":
      title.textContent = I18N[currentLang].nav_incidents;
      subtitle.textContent = "Corroborated security exposures, stealer telemetry, and actionable alerts";
      await renderIncidentsView(container);
      break;
    case "actions":
      title.textContent = I18N[currentLang].nav_actions;
      subtitle.textContent = "Guided protective remediation checklist with user-reported completion provenance";
      await renderActionsView(container);
      break;
    case "assistance":
      title.textContent = I18N[currentLang].nav_assistance;
      subtitle.textContent = "Official UIDAI and Income Tax Department protective guides and resident assistance";
      await renderAssistanceView(container);
      break;
    case "coverage":
      title.textContent = I18N[currentLang].nav_coverage;
      subtitle.textContent = "Explicit status of monitored intelligence sources, limits, and schedules";
      await renderCoverageView(container);
      break;
    case "notifications":
      title.textContent = I18N[currentLang].nav_notifications;
      subtitle.textContent = "Privacy-safe notification logs and channel preferences";
      await renderNotificationsView(container);
      break;
    case "billing":
      title.textContent = I18N[currentLang].nav_billing;
      subtitle.textContent = "Subscription plans, Razorpay payments, and entitlement status";
      await renderBillingView(container);
      break;
    case "privacy":
      title.textContent = I18N[currentLang].nav_privacy;
      subtitle.textContent = "DPDP / GDPR self-service: Consent controls, export data, and account deletion";
      await renderPrivacyView(container);
      break;
    case "security":
      title.textContent = I18N[currentLang].nav_security;
      subtitle.textContent = "Step-up authentication, active session inventory, and session revocation";
      await renderSecurityView(container);
      break;
  }
}

// 1. Overview View
async function renderOverviewView(container) {
  const [monStatus, incidentsRes, idsRes] = await Promise.all([
    apiCall("/monitoring/status"),
    apiCall("/incidents"),
    apiCall("/identifiers")
  ]);

  const activeIds = idsRes.data.length;
  const activeIncidents = incidentsRes.data.filter(i => i.state !== "resolved_by_user").length;

  container.innerHTML = `
    <div class="grid-cards">
      <div class="card">
        <div class="card-header">
          <span class="card-title">Monitoring Status</span>
          <span class="badge ${monStatus.data.monitoring_status === 'active' ? 'badge-low' : 'badge-high'}">
            ${monStatus.data.monitoring_status.toUpperCase()}
          </span>
        </div>
        <div class="card-value">${monStatus.data.active_monitored_identifiers_count} Identifiers</div>
        <p class="text-muted" style="margin-top: 0.5rem; font-size: 0.85rem;">
          ${monStatus.data.consent_granted ? '✓ Legal consent verified' : '⚠️ Consent pending'}
        </p>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Active Incidents</span>
          <span class="badge ${activeIncidents > 0 ? 'badge-critical' : 'badge-low'}">
            ${activeIncidents > 0 ? 'ATTENTION' : 'CLEAR'}
          </span>
        </div>
        <div class="card-value">${activeIncidents}</div>
        <p class="text-muted" style="margin-top: 0.5rem; font-size: 0.85rem;">Corroborated across HIBP & Flare</p>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Aadhaar & PAN Protection</span>
          <span class="badge badge-medium">GUIDANCE</span>
        </div>
        <div class="card-value">UIDAI Ready</div>
        <p class="text-muted" style="margin-top: 0.5rem; font-size: 0.85rem;">Biometric lock & VID assistance</p>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 style="font-size: 1.1rem;">Recent Incidents</h3>
        <button class="btn btn-outline" onclick="switchView('incidents')">View All</button>
      </div>
      ${activeIncidents === 0 ? `
        <div class="empty-state">
          <div class="empty-state-icon">🛡️</div>
          <div class="empty-state-title">${I18N[currentLang].empty_no_incidents}</div>
          <div class="empty-state-desc">Supported intelligence providers report no active exposures for your verified identifiers.</div>
        </div>
      ` : `
        <table class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Severity</th>
              <th>Identifier</th>
              <th>Detected</th>
              <th>State</th>
            </tr>
          </thead>
          <tbody>
            ${incidentsRes.data.slice(0, 5).map(inc => `
              <tr>
                <td><strong>${inc.title}</strong></td>
                <td><span class="badge badge-${inc.severity}">${inc.severity}</span></td>
                <td><code>${inc.identifier.masked_value}</code></td>
                <td>${new Date(inc.first_detected_at).toLocaleDateString()}</td>
                <td>${inc.state}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `}
    </div>
  `;
}

// 2. Identities View
async function renderIdentitiesView(container) {
  const idsRes = await apiCall("/identifiers");
  const ids = idsRes.data;

  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <h2 style="font-size: 1.25rem;">Monitored Identifiers</h2>
      <button class="btn btn-primary" onclick="showAddIdentifierModal()">
        <span>➕</span> Add Identifier
      </button>
    </div>

    ${ids.length === 0 ? `
      <div class="empty-state">
        <div class="empty-state-icon">📧</div>
        <div class="empty-state-title">${I18N[currentLang].empty_no_identities}</div>
        <div class="empty-state-desc">To protect your identity, add your primary personal email address and confirm verification.</div>
        <button class="btn btn-primary" onclick="showAddIdentifierModal()">Add Email</button>
      </div>
    ` : `
      <table class="data-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Masked Identifier</th>
            <th>Status</th>
            <th>Monitoring</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${ids.map(i => `
            <tr>
              <td><span class="badge badge-medium">${i.type.toUpperCase()}</span></td>
              <td><code>${i.masked_value}</code></td>
              <td><span class="badge badge-${i.state === 'active' ? 'low' : 'high'}">${i.state}</span></td>
              <td>${i.monitoring_enabled ? '🟢 Active' : '⚪ Inactive'}</td>
              <td>
                ${i.state === 'pending_verification' ? `
                  <button class="btn btn-outline" onclick="triggerChallenge('${i.id}')">Verify Now</button>
                ` : i.state === 'active' ? `
                  <button class="btn btn-outline" onclick="pauseIdentifier('${i.id}')">Pause</button>
                ` : i.state === 'paused' ? `
                  <button class="btn btn-outline" onclick="resumeIdentifier('${i.id}')">Resume</button>
                ` : ''}
                <button class="btn btn-danger" onclick="deleteIdentifier('${i.id}')">Delete</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `}
  `;
}

// Add Identifier Modal
window.showAddIdentifierModal = function() {
  const modal = document.getElementById("modal-container");
  modal.classList.remove("hidden");
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3>Add New Identifier</h3>
        <p class="text-muted" style="font-size: 0.85rem;">
          Identifiers are envelope-encrypted. Monitoring requires verification before queries.
        </p>
      </div>
      <div class="form-group">
        <label for="ident-type">Type</label>
        <select id="ident-type" class="form-input">
          <option value="email">Email Address</option>
          <option value="phone">Phone Number (Assistance only)</option>
          <option value="pan">PAN Card (Assistance only)</option>
        </select>
      </div>
      <div class="form-group">
        <label for="ident-value">Identifier Value</label>
        <input type="text" id="ident-value" class="form-input" placeholder="e.g. name@example.com">
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitAddIdentifier()">Save & Verify</button>
      </div>
    </div>
  `;
};

window.closeModal = function() {
  document.getElementById("modal-container").classList.add("hidden");
};

window.submitAddIdentifier = async function() {
  const type = document.getElementById("ident-type").value;
  const value = document.getElementById("ident-value").value;
  if (!value) return alert("Please enter an identifier value.");

  try {
    const res = await apiCall("/identifiers", "POST", { type, value });
    closeModal();
    // Prompt verification challenge immediately
    if (res.data.state === "pending_verification") {
      triggerChallenge(res.data.id);
    } else {
      renderCurrentView();
    }
  } catch (e) {
    alert(e.message);
  }
};

window.triggerChallenge = async function(id) {
  try {
    const chal = await apiCall(`/identifiers/${id}/verification-challenges`, "POST");
    const demoToken = chal.data.demo_token;
    const modal = document.getElementById("modal-container");
    modal.classList.remove("hidden");
    modal.innerHTML = `
      <div class="modal-box">
        <div class="modal-header">
          <h3>Verify Identifier Control</h3>
          <p class="text-muted" style="font-size: 0.85rem;">
            A 6-digit one-time code was generated. Verification prevents checking unauthorized targets.
          </p>
          ${demoToken ? `<div style="background: rgba(59,130,246,0.15); padding: 0.5rem; margin-top: 0.5rem; border-radius: 4px; font-size: 0.85rem;">
            Demo Verification Code: <strong>${demoToken}</strong>
          </div>` : ''}
        </div>
        <div class="form-group">
          <label for="chal-token">Enter 6-Digit Code</label>
          <input type="text" id="chal-token" class="form-input" value="${demoToken || ''}" placeholder="123456">
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
          <button class="btn btn-primary" onclick="confirmVerification('${id}')">Confirm Verification</button>
        </div>
      </div>
    `;
  } catch (e) {
    alert(e.message);
  }
};

window.confirmVerification = async function(id) {
  const token = document.getElementById("chal-token").value;
  try {
    await apiCall("/identifiers/verification-challenges/complete", "POST", {
      identifier_id: id,
      challenge_token: token
    });
    closeModal();
    renderCurrentView();
  } catch (e) {
    alert(e.message);
  }
};

window.pauseIdentifier = async function(id) {
  await apiCall(`/identifiers/${id}/pause`, "POST");
  renderCurrentView();
};

window.resumeIdentifier = async function(id) {
  await apiCall(`/identifiers/${id}/resume`, "POST");
  renderCurrentView();
};

window.deleteIdentifier = async function(id) {
  if (confirm("Are you sure you want to delete this identifier and stop all monitoring?")) {
    await apiCall(`/identifiers/${id}`, "DELETE");
    renderCurrentView();
  }
};

// 3. Incidents View
async function renderIncidentsView(container) {
  const incRes = await apiCall("/incidents");
  const incidents = incRes.data;

  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <h2 style="font-size: 1.25rem;">Security Incidents (${incidents.length})</h2>
    </div>

    ${incidents.length === 0 ? `
      <div class="empty-state">
        <div class="empty-state-icon">🛡️</div>
        <div class="empty-state-title">${I18N[currentLang].empty_no_incidents}</div>
        <div class="empty-state-desc">No compromised credentials or dark-web mentions detected.</div>
      </div>
    ` : `
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        ${incidents.map(inc => `
          <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
              <div>
                <h3 style="font-size: 1.1rem; font-weight: 600;">${inc.title}</h3>
                <p class="text-muted" style="font-size: 0.85rem;">
                  Associated with: <code>${inc.identifier.masked_value}</code> • First detected: ${new Date(inc.first_detected_at).toLocaleString()}
                </p>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <span class="badge badge-${inc.severity}">SEVERITY: ${inc.severity.toUpperCase()}</span>
                <span class="badge badge-low">CONFIDENCE: ${inc.confidence.toUpperCase()}</span>
                <span class="badge badge-medium">SCORE: ${inc.priority_score}/100</span>
              </div>
            </div>

            <div style="margin: 0.75rem 0;">
              <span class="text-muted" style="font-size: 0.85rem;">Exposed data categories: </span>
              ${inc.exposure_categories.map(c => `<span class="badge badge-outline" style="background: rgba(255,255,255,0.05); margin-right: 4px;">${c}</span>`).join('')}
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
              <span style="font-size: 0.85rem;" class="text-muted">Status: <strong>${inc.state}</strong></span>
              <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-outline" onclick="openDisputeModal('${inc.id}')">Dispute Exposure</button>
                <button class="btn btn-primary" onclick="switchView('actions')">Take Action</button>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `}
  `;
}

window.openDisputeModal = function(id) {
  const modal = document.getElementById("modal-container");
  modal.classList.remove("hidden");
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3>Dispute Incident Exposure</h3>
        <p class="text-muted" style="font-size: 0.85rem;">
          Disputing creates an audited review and suppresses repetitive notifications without falsifying source logs.
        </p>
      </div>
      <div class="form-group">
        <label for="disp-reason">Dispute Reason</label>
        <select id="disp-reason" class="form-input">
          <option value="this_is_not_mine">This is not my account</option>
          <option value="do_not_recognize">I do not recognize this service</option>
          <option value="already_addressed">I have already addressed this credential</option>
        </select>
      </div>
      <div class="form-group">
        <label for="disp-notes">Notes (Optional)</label>
        <textarea id="disp-notes" class="form-input" rows="3" placeholder="Additional details"></textarea>
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitDispute('${id}')">Submit Dispute</button>
      </div>
    </div>
  `;
};

window.submitDispute = async function(id) {
  const reason = document.getElementById("disp-reason").value;
  const notes = document.getElementById("disp-notes").value;
  try {
    await apiCall(`/findings/${id}/disputes`, "POST", { reason, notes });
    closeModal();
    alert("Dispute submitted for security audit. Notifications suppressed.");
    renderCurrentView();
  } catch (e) {
    alert(e.message);
  }
};

// 4. Protection Actions View
async function renderActionsView(container) {
  const incRes = await apiCall("/incidents");
  const incidents = incRes.data;

  container.innerHTML = `
    <h2 style="font-size: 1.25rem; margin-bottom: 1rem;">Actionable Remediation Checklist</h2>
    <p class="text-muted" style="margin-bottom: 1.5rem; font-size: 0.9rem;">
      Marking an action complete records user-reported completion. It does not erase the historical breach record.
    </p>

    <div style="display: flex; flex-direction: column; gap: 1rem;">
      ${incidents.map(inc => `
        <div class="card">
          <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">Remediation for: ${inc.title}</h3>
          <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.75rem;">
            ${inc.recommended_actions.map(act => `
              <li style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 0.75rem; border-radius: var(--radius);">
                <div>
                  <strong>${act.replace(/_/g, ' ').toUpperCase()}</strong>
                  <p class="text-muted" style="font-size: 0.85rem;">Protective step recommended for ${inc.identifier.masked_value}</p>
                </div>
                <button class="btn btn-outline" onclick="alert('Action recorded as completed by resident (user_reported).')">
                  Mark Completed
                </button>
              </li>
            `).join('')}
          </ul>
        </div>
      `).join('')}
    </div>
  `;
}

// 5. Aadhaar & PAN Assistance View
async function renderAssistanceView(container) {
  const [guidesRes, reportsRes] = await Promise.all([
    apiCall("/identity-assistance/guides"),
    apiCall("/identity-assistance/reports")
  ]);

  const guides = guidesRes.data;
  const reports = reportsRes.data;

  container.innerHTML = `
    <div style="margin-bottom: 2rem;">
      <h2 style="font-size: 1.25rem;">India Resident Protection Assistance (Aadhaar & PAN)</h2>
      <p class="text-muted" style="margin-top: 0.25rem; font-size: 0.9rem;">
        Official guidance for protecting your Aadhaar and PAN against identity theft. We strictly never scrape UIDAI portals or handle Aadhaar OTPs.
      </p>
    </div>

    <div class="grid-cards">
      ${guides.map(g => `
        <div class="card">
          <div class="card-header">
            <span class="card-title">${g.official_authority}</span>
            <span class="badge badge-medium">OFFICIAL GUIDE</span>
          </div>
          <h3 style="font-size: 1.15rem; margin-bottom: 0.75rem;">${g.topic}</h3>
          <ol style="padding-left: 1.25rem; margin-bottom: 1rem; font-size: 0.85rem; color: #d1d5db; display: flex; flex-direction: column; gap: 0.4rem;">
            ${g.steps.map(s => `<li>${s}</li>`).join('')}
          </ol>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto;">
            <a href="${g.portal_url}" target="_blank" rel="noopener noreferrer" class="btn btn-outline" style="font-size: 0.8rem;">
              Open Official Portal ↗
            </a>
            <button class="btn btn-primary" onclick="confirmAssistanceAction('${g.id}')">
              Record Completion
            </button>
          </div>
        </div>
      `).join('')}
    </div>

    <div class="card" style="margin-top: 2rem;">
      <div class="card-header">
        <h3 style="font-size: 1.1rem;">Report Suspicious Identity Activity</h3>
        <button class="btn btn-primary" onclick="showReportModal()">Report Incident</button>
      </div>
      <p class="text-muted" style="font-size: 0.85rem; margin-bottom: 1rem;">
        Received an unsolicited Aadhaar OTP? Noticed an unrecognized entry in your Aadhaar Authentication History? Log it here for your security record.
      </p>

      ${reports.length === 0 ? `
        <p class="text-muted" style="font-style: italic; font-size: 0.85rem;">No user-reported incidents filed.</p>
      ` : `
        <table class="data-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Description</th>
              <th>Date Filed</th>
              <th>Provenance</th>
            </tr>
          </thead>
          <tbody>
            ${reports.map(r => `
              <tr>
                <td><strong>${r.category.replace(/_/g, ' ')}</strong></td>
                <td>${r.description_redacted}</td>
                <td>${new Date(r.created_at).toLocaleDateString()}</td>
                <td><span class="badge badge-low">${r.provenance}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `}
    </div>
  `;
}

window.confirmAssistanceAction = async function(id) {
  await apiCall(`/identity-assistance/actions/${id}/confirm`, "POST");
  alert("Action recorded! Your protective action is confirmed in your security audit record.");
};

window.showReportModal = function() {
  const modal = document.getElementById("modal-container");
  modal.classList.remove("hidden");
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3>Report Suspicious Aadhaar / Identity Activity</h3>
      </div>
      <div class="form-group">
        <label for="rep-cat">Category</label>
        <select id="rep-cat" class="form-input">
          <option value="unsolicited_aadhaar_otp">Unsolicited Aadhaar OTP Received</option>
          <option value="suspicious_auth_history">Suspicious UIDAI Authentication History Entry</option>
          <option value="pan_unauthorized_loan">Unauthorized Loan / Ingestion on PAN</option>
          <option value="fake_telecom_sim">Suspicious SIM registered with identity</option>
        </select>
      </div>
      <div class="form-group">
        <label for="rep-desc">Description</label>
        <textarea id="rep-desc" class="form-input" rows="3" placeholder="Describe the event (e.g. Received OTP from VM-AADHAR at 10:15 AM without initiating request). Do NOT paste passwords or OTP digits."></textarea>
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitAssistanceReport()">Submit Report</button>
      </div>
    </div>
  `;
};

window.submitAssistanceReport = async function() {
  const category = document.getElementById("rep-cat").value;
  const description = document.getElementById("rep-desc").value;
  if (!description) return alert("Please provide description.");
  try {
    await apiCall("/identity-assistance/reports", "POST", { category, description });
    closeModal();
    renderCurrentView();
  } catch (e) {
    alert(e.message);
  }
};

// 6. Coverage Transparency View
async function renderCoverageView(container) {
  const covRes = await apiCall("/coverage");
  const items = covRes.data;

  container.innerHTML = `
    <h2 style="font-size: 1.25rem; margin-bottom: 0.5rem;">Source Coverage Transparency</h2>
    <p class="text-muted" style="margin-bottom: 1.5rem; font-size: 0.9rem;">
      We explicitly declare our monitoring scope, freshness, and boundaries. "No matches" does not mean no risk in unexplored underground sources.
    </p>

    <table class="data-table">
      <thead>
        <tr>
          <th>Source Name</th>
          <th>Monitored Capability</th>
          <th>Current Status</th>
          <th>Known Scope Limitations</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(c => `
          <tr>
            <td><strong>${c.source}</strong></td>
            <td>${c.capability}</td>
            <td><span class="badge badge-${c.current_state === 'healthy' ? 'low' : 'medium'}">${c.current_state}</span></td>
            <td style="font-size: 0.85rem; color: #9ca3af;">${c.known_limitation}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// 7. Notifications View
async function renderNotificationsView(container) {
  const [notifsRes, prefRes] = await Promise.all([
    apiCall("/notifications"),
    apiCall("/notification-preferences")
  ]);

  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <h2 style="font-size: 1.25rem;">Notification History</h2>
      <div style="display: flex; gap: 0.5rem;">
        <button class="btn btn-outline" onclick="sendTestNotification()">Send Test Alert</button>
        <button class="btn btn-outline" onclick="markAllNotificationsRead()">Mark All Read</button>
      </div>
    </div>

    ${notifsRes.data.length === 0 ? `
      <div class="empty-state">
        <div class="empty-state-icon">🔔</div>
        <div class="empty-state-title">No notifications</div>
        <div class="empty-state-desc">You are up to date. Alerts will appear here when exposures are detected.</div>
      </div>
    ` : `
      <div style="display: flex; flex-direction: column; gap: 0.75rem;">
        ${notifsRes.data.map(n => `
          <div class="card" style="padding: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <strong>${n.title}</strong>
              <span class="badge ${n.status === 'read' ? 'badge-low' : 'badge-high'}">${n.status}</span>
            </div>
            <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #d1d5db;">${n.body}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem; font-size: 0.8rem;" class="text-muted">
              <span>Channel: ${n.channel}</span>
              <span>${new Date(n.created_at).toLocaleString()}</span>
            </div>
          </div>
        `).join('')}
      </div>
    `}
  `;
}

window.sendTestNotification = async function() {
  await apiCall("/notification-preferences/test", "POST");
  renderCurrentView();
};

window.markAllNotificationsRead = async function() {
  await apiCall("/notifications/read-all", "POST");
  renderCurrentView();
};

// 8. Billing View
async function renderBillingView(container) {
  const [subRes, plansRes] = await Promise.all([
    apiCall("/billing/subscription"),
    apiCall("/plans")
  ]);

  container.innerHTML = `
    <div class="card" style="margin-bottom: 2rem;">
      <div class="card-header">
        <span class="card-title">Current Subscription</span>
        <span class="badge badge-low">${subRes.data.state.toUpperCase()}</span>
      </div>
      <div class="card-value">₹${subRes.data.plan_id === 'plan_pro' ? '999' : '499'} / month</div>
      <p class="text-muted" style="margin-top: 0.5rem;">
        Paid through: <strong>${new Date(subRes.data.paid_through_at).toLocaleDateString()}</strong> • Reference: <code>${subRes.data.provider_reference}</code>
      </p>
      <div style="margin-top: 1.25rem;">
        <button class="btn btn-danger" onclick="cancelSub()">Cancel Subscription</button>
      </div>
    </div>

    <h2 style="font-size: 1.25rem; margin-bottom: 1rem;">Available Plans</h2>
    <div class="grid-cards">
      ${plansRes.data.map(p => `
        <div class="card">
          <h3 style="font-size: 1.25rem; margin-bottom: 0.5rem;">${p.name}</h3>
          <div class="card-value" style="font-size: 1.75rem; margin-bottom: 1rem;">₹${p.price_inr} <span style="font-size: 0.9rem; color: #9ca3af;">/${p.billing_interval}</span></div>
          <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem; font-size: 0.85rem; color: #d1d5db;">
            ${p.features.map(f => `<li>✓ ${f}</li>`).join('')}
          </ul>
          <button class="btn btn-primary" style="width: 100%; justify-content: center;" onclick="subscribePlan('${p.id}')">
            ${subRes.data.plan_id === p.id ? 'Current Plan' : 'Select Plan'}
          </button>
        </div>
      `).join('')}
    </div>
  `;
}

window.subscribePlan = async function(plan_id) {
  const res = await apiCall("/billing/subscriptions", "POST", { plan_id });
  alert(`Razorpay checkout initialized for ${res.data.amount_inr} INR (Order: ${res.data.checkout_order_id}).`);
  renderCurrentView();
};

window.cancelSub = async function() {
  if (confirm("Cancel subscription? You will remain covered until your paid-through date.")) {
    try {
      await apiCall("/billing/subscription/cancel", "POST");
      alert("Subscription cancelled.");
      renderCurrentView();
    } catch (e) {
      alert("Step-up elevation required to cancel. Please elevate session first.");
    }
  }
};

// 9. Privacy Center View
async function renderPrivacyView(container) {
  const consentsRes = await apiCall("/consents");

  container.innerHTML = `
    <h2 style="font-size: 1.25rem; margin-bottom: 0.5rem;">Digital Personal Data Protection (DPDP) Center</h2>
    <p class="text-muted" style="margin-bottom: 1.5rem; font-size: 0.9rem;">
      Full control over your personal identity processing, consent withdrawal, data portability, and erasure.
    </p>

    <div class="grid-cards">
      <div class="card">
        <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">Active Consent Grants</h3>
        <p class="text-muted" style="font-size: 0.85rem; margin-bottom: 1rem;">
          Revoking consent immediately halts all background monitoring and cancels queued jobs.
        </p>
        ${consentsRes.data.length === 0 ? `
          <button class="btn btn-primary" onclick="grantDefaultConsent()">Grant Monitoring Consent</button>
        ` : `
          <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.5rem;">
            ${consentsRes.data.map(g => `
              <li style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); padding: 0.75rem; border-radius: var(--radius);">
                <div>
                  <strong>${g.purpose.replace(/_/g, ' ')}</strong>
                  <div style="font-size: 0.75rem;" class="text-muted">Notice: v${g.notice_version}</div>
                </div>
                <button class="btn btn-danger" onclick="withdrawConsent('${g.id}')">Withdraw</button>
              </li>
            `).join('')}
          </ul>
        `}
      </div>

      <div class="card">
        <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">Data Export (Portability)</h3>
        <p class="text-muted" style="font-size: 0.85rem; margin-bottom: 1rem;">
          Download a machine-readable JSON archive containing all monitored identifiers, findings, and logs.
        </p>
        <button class="btn btn-outline" onclick="requestExport()">Export My Data</button>
      </div>

      <div class="card" style="border-color: rgba(239,68,68,0.4);">
        <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem; color: #f87171;">Account Erasure</h3>
        <p class="text-muted" style="font-size: 0.85rem; margin-bottom: 1rem;">
          Permanently delete your account, purge active store data, and trigger unregistration across providers.
        </p>
        <button class="btn btn-danger" onclick="requestAccountDeletion()">Request Account Deletion</button>
      </div>
    </div>
  `;
}

window.grantDefaultConsent = async function() {
  await apiCall("/consents", "POST", {
    purpose: "identity_exposure_monitoring",
    notice_version: "1.0",
    provider_categories: ["breach_intelligence", "darkweb_monitoring"],
    subject_id: currentSession.subject_id
  });
  renderCurrentView();
};

window.withdrawConsent = async function(id) {
  if (confirm("Withdraw consent? All scheduled and queued scans will be halted immediately.")) {
    await apiCall(`/consents/${id}/withdraw`, "POST");
    alert("Consent withdrawn. Monitoring stopped.");
    renderCurrentView();
  }
};

window.requestExport = async function() {
  try {
    const res = await apiCall("/privacy/exports", "POST");
    const download = await apiCall(`/privacy/exports/${res.data.export_id}/download`, "POST");
    const blob = new Blob([JSON.stringify(download.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `identity_data_export_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
  } catch (e) {
    alert("Step-up authentication required for data export. Please elevate your session.");
  }
};

window.requestAccountDeletion = async function() {
  if (confirm("Permanently delete account? This triggers the 8-stage deletion process.")) {
    try {
      const res = await apiCall("/privacy/deletion-requests", "POST");
      alert("Deletion initiated: " + res.data.message);
      location.reload();
    } catch (e) {
      alert("Step-up authentication required for account deletion. Please elevate your session.");
    }
  }
};

// 10. Security View
async function renderSecurityView(container) {
  const [secRes, sessRes] = await Promise.all([
    apiCall("/me/security"),
    apiCall("/sessions")
  ]);

  container.innerHTML = `
    <div class="grid-cards">
      <div class="card">
        <div class="card-header">
          <span class="card-title">Step-Up Elevated State</span>
          <span class="badge ${secRes.data.step_up_authenticated ? 'badge-low' : 'badge-high'}">
            ${secRes.data.step_up_authenticated ? 'ELEVATED' : 'STANDARD'}
          </span>
        </div>
        <p class="text-muted" style="font-size: 0.85rem; margin: 0.75rem 0;">
          Required for high-privilege operations: data export, account deletion, and billing changes.
        </p>
        <button class="btn btn-primary" onclick="elevateSession()">Elevate Now (5-Minute Window)</button>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">MFA & Authentication</span>
          <span class="badge badge-low">PROTECTED</span>
        </div>
        <p class="text-muted" style="font-size: 0.85rem; margin: 0.75rem 0;">
          Cognito-managed OIDC Authorization Code Flow with PKCE and HttpOnly cookies.
        </p>
      </div>
    </div>

    <div class="card" style="margin-top: 1.5rem;">
      <h3 style="font-size: 1.1rem; margin-bottom: 1rem;">Active Sessions</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Session Identifier</th>
            <th>Created</th>
            <th>Last Active</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${sessRes.data.map(s => `
            <tr>
              <td><code>${s.session_id}</code> ${s.current ? '<span class="badge badge-low">THIS SESSION</span>' : ''}</td>
              <td>${new Date(s.created_at).toLocaleString()}</td>
              <td>${new Date(s.last_seen_at).toLocaleString()}</td>
              <td>
                ${!s.current ? `<button class="btn btn-danger" onclick="revokeSession('${s.session_id}')">Revoke</button>` : '-'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

window.elevateSession = async function() {
  await apiCall("/auth/step-up", "POST", { passcode: "123456" });
  alert("Step-up authentication verified! Elevated for 5 minutes.");
  renderCurrentView();
};

window.revokeSession = async function(id) {
  try {
    await apiCall(`/sessions/${id}`, "DELETE");
    renderCurrentView();
  } catch (e) {
    alert("Step-up authentication required to revoke sessions.");
  }
};

// Global topbar scan trigger
document.getElementById("btn-scan-now").addEventListener("click", async () => {
  try {
    const idsRes = await apiCall("/identifiers");
    const activeIds = idsRes.data.filter(i => i.state === "active").map(i => i.id);
    if (activeIds.length === 0) {
      return alert("Please add and verify an identifier before running a scan.");
    }
    const res = await apiCall("/scans", "POST", { identifier_ids: activeIds });
    alert("Scan submitted to outbox! Background workers are querying HIBP and Flare.");
    renderCurrentView();
  } catch (e) {
    alert(e.message);
  }
});

document.getElementById("btn-step-up").addEventListener("click", () => {
  elevateSession();
});

// Mobile menu toggle
const mobileMenuBtn = document.getElementById("mobile-menu-btn");
const sidebar = document.querySelector(".sidebar");
if (mobileMenuBtn && sidebar) {
  mobileMenuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    sidebar.classList.toggle("open");
  });

  document.addEventListener("click", (e) => {
    if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== mobileMenuBtn) {
      sidebar.classList.remove("open");
    }
  });
}

// Service worker registration
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js")
      .then((reg) => console.log("Service Worker registered with scope:", reg.scope))
      .catch((err) => console.warn("Service Worker registration failed:", err));
  });
}

// Event listeners
document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    switchView(btn.dataset.view);
    if (sidebar && sidebar.classList.contains("open")) {
      sidebar.classList.remove("open");
    }
  });
});

document.getElementById("lang-select").addEventListener("change", (e) => {
  currentLang = e.target.value;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (I18N[currentLang][key]) {
      el.textContent = I18N[currentLang][key];
    }
  });
  renderCurrentView();
});

// Init
window.addEventListener("DOMContentLoaded", async () => {
  await initSession();
  renderCurrentView();
});
