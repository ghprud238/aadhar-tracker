/**
 * Suraksha Wearable Companion Client
 * Micro-controller script for Wear OS / watchOS glance tile and quick-action complications.
 */

const STATE = {
  activeTile: 0,
  totalTiles: 3,
  isAmbient: false,
  glance: null,
  hapticSupported: 'vibrate' in navigator,
};

// Clock update
function updateClock() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const timeStr = `${hours}:${minutes}`;

  const topTimeEl = document.getElementById('watch-time');
  const ambientClockEl = document.getElementById('ambient-clock');
  if (topTimeEl) topTimeEl.textContent = timeStr;
  if (ambientClockEl) ambientClockEl.textContent = timeStr;
}

setInterval(updateClock, 1000);
updateClock();

// API Glance fetcher
async function fetchGlance() {
  try {
    const res = await fetch('/api/v1/companion/glance', {
      headers: {
        'Accept': 'application/json',
        'X-Request-ID': 'watch_' + Math.random().toString(36).substring(2, 9),
      },
    });

    if (!res.ok) {
      // Fallback: try to initialize session if needed
      await fetch('/api/v1/auth/callback?email=resident@example.in&full_name=Aarav+Sharma');
      const retry = await fetch('/api/v1/companion/glance');
      const data = await retry.json();
      return updateUIWithGlance(data.data);
    }

    const data = await res.json();
    updateUIWithGlance(data.data);
  } catch (err) {
    console.warn('Glance sync fallback to offline state:', err);
    document.getElementById('sync-indicator').textContent = '🟡';
  }
}

function updateUIWithGlance(glance) {
  STATE.glance = glance;
  document.getElementById('sync-indicator').textContent = '🟢';

  // Ring & Shield Status
  const statusLabel = document.getElementById('shield-state-label');
  const glyph = document.getElementById('shield-glyph');
  const ring = document.getElementById('ring-progress');
  const ambientShield = document.getElementById('ambient-shield');

  const circumference = 477.5; // 2 * PI * 76

  if (glance.shield_status === 'critical') {
    statusLabel.textContent = 'CRITICAL';
    statusLabel.style.color = '#ef4444';
    glyph.textContent = '🚨';
    ring.style.stroke = '#ef4444';
    ring.style.strokeDashoffset = String(circumference * 0.1);
    ambientShield.textContent = '🚨 THREAT';
    ambientShield.style.color = '#ef4444';
  } else if (glance.shield_status === 'warning') {
    statusLabel.textContent = 'WARNING';
    statusLabel.style.color = '#f59e0b';
    glyph.textContent = '⚠️';
    ring.style.stroke = '#f59e0b';
    ring.style.strokeDashoffset = String(circumference * 0.35);
    ambientShield.textContent = '⚠️ ALERT';
    ambientShield.style.color = '#f59e0b';
  } else {
    statusLabel.textContent = 'SECURE';
    statusLabel.style.color = '#10b981';
    glyph.textContent = '🛡️';
    ring.style.stroke = '#10b981';
    ring.style.strokeDashoffset = '0';
    ambientShield.textContent = '🛡️ SECURE';
    ambientShield.style.color = '#4b5563';
  }

  // Counters
  document.getElementById('val-incidents').textContent = String(glance.active_incidents);
  document.getElementById('val-monitored').textContent = String(glance.active_monitored_count);

  // Biometrics Pill
  const bioDot = document.getElementById('bio-dot');
  const bioText = document.getElementById('bio-text');
  if (glance.biometrics_locked) {
    bioDot.style.backgroundColor = '#10b981';
    bioText.textContent = 'Biometrics: Locked ✓';
  } else {
    bioDot.style.backgroundColor = '#f59e0b';
    bioText.textContent = 'Biometrics: Unlocked';
  }

  // Urgent Alert Tile
  if (glance.urgent_alert) {
    document.getElementById('urgent-severity').textContent = glance.urgent_alert.severity.toUpperCase() + ' ALERT';
    document.getElementById('urgent-title').textContent = glance.urgent_alert.title;
    document.getElementById('urgent-desc').textContent = `High-priority incident detected. Tap below to acknowledge.`;
  } else {
    document.getElementById('urgent-severity').textContent = 'STATUS NORMAL';
    document.getElementById('urgent-title').textContent = 'No Active Breaches';
    document.getElementById('urgent-desc').textContent = 'All monitored accounts match zero known breaches.';
  }
}

// Navigation between tiles
function selectTile(index) {
  STATE.activeTile = index;
  const tiles = document.querySelectorAll('.watch-tile');
  const dots = document.querySelectorAll('.tile-dots .dot');

  tiles.forEach((t, i) => {
    t.classList.toggle('active', i === index);
  });
  dots.forEach((d, i) => {
    d.classList.toggle('active', i === index);
  });

  if (STATE.hapticSupported) {
    navigator.vibrate(20);
  }
}

// 1-Tap Biometric Lock Quick Action
document.getElementById('btn-watch-lock').addEventListener('click', async () => {
  const btn = document.getElementById('btn-watch-lock');
  const resEl = document.getElementById('action-result');
  btn.disabled = true;
  btn.textContent = 'Recording...';

  try {
    const res = await fetch('/api/v1/identity-assistance/actions/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action_type: 'lock_biometrics',
        confirmation_note: 'Smartwatch 1-tap confirmation: Resident locked biometrics via mAadhaar',
      }),
    });

    if (STATE.hapticSupported) {
      navigator.vibrate([80, 40, 80]);
    }

    resEl.classList.remove('hidden');
    btn.textContent = '✓ Locked Confirmed';
    await fetchGlance();
  } catch (err) {
    btn.textContent = 'Retry Confirmation';
    btn.disabled = false;
  }
});

// Acknowledge alert button
document.getElementById('btn-ack-alert').addEventListener('click', () => {
  if (STATE.hapticSupported) {
    navigator.vibrate(30);
  }
  selectTile(0);
});

// Dot click handlers
document.querySelectorAll('.tile-dots .dot').forEach((dot) => {
  dot.addEventListener('click', () => {
    selectTile(parseInt(dot.dataset.index, 10));
  });
});

// Swipe support for touchscreens / watch emulator
let touchStartX = 0;
const watchScreen = document.getElementById('watch-screen');

watchScreen.addEventListener('touchstart', (e) => {
  touchStartX = e.changedTouches[0].screenX;
}, { passive: true });

watchScreen.addEventListener('touchend', (e) => {
  const touchEndX = e.changedTouches[0].screenX;
  const diff = touchEndX - touchStartX;
  if (Math.abs(diff) > 40) {
    if (diff < 0 && STATE.activeTile < STATE.totalTiles - 1) {
      selectTile(STATE.activeTile + 1);
    } else if (diff > 0 && STATE.activeTile > 0) {
      selectTile(STATE.activeTile - 1);
    }
  }
}, { passive: true });

// Simulator Controls
const ambientOverlay = document.getElementById('ambient-overlay');
const btnModeActive = document.getElementById('btn-mode-active');
const btnModeAmbient = document.getElementById('btn-mode-ambient');

btnModeActive.addEventListener('click', () => {
  btnModeActive.classList.add('active');
  btnModeAmbient.classList.remove('active');
  ambientOverlay.classList.add('hidden');
});

btnModeAmbient.addEventListener('click', () => {
  btnModeAmbient.classList.add('active');
  btnModeActive.classList.remove('active');
  ambientOverlay.classList.remove('hidden');
});

ambientOverlay.addEventListener('click', () => {
  btnModeActive.click();
});

// Simulator button to inject simulated red alert & haptic buzz
document.getElementById('btn-sim-breach').addEventListener('click', () => {
  updateUIWithGlance({
    shield_status: 'critical',
    active_incidents: 2,
    highest_severity: 'critical',
    active_monitored_count: 1,
    biometrics_locked: false,
    urgent_alert: {
      incident_id: 'inc_sim_999',
      title: 'Telecom Mega Breach (Passwords Leaked)',
      severity: 'critical',
      priority_score: 95,
    },
    last_synced_at: new Date().toISOString(),
  });

  // Switch to Urgent Tile
  selectTile(1);

  // Trigger double buzz
  if (STATE.hapticSupported) {
    navigator.vibrate([150, 80, 150, 80, 300]);
  }
});

// Initial boot
window.addEventListener('DOMContentLoaded', () => {
  fetchGlance();
  setInterval(fetchGlance, 15000); // 15-second background glance refresh
});
