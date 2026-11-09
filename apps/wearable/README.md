# Suraksha Wearable Companion Client (Wear OS & watchOS)

Ultra-lightweight smartwatch companion client designed for Wear OS (Tiles & Complications) and Apple Watch (watchOS Smart Stack & Complications).

---

## ⌚ Overview

Smartwatch users require immediate, glanceable situational awareness of their identity protection status without pulling out their mobile phone. The Suraksha Wearable client delivers:

1. **🛡️ 1-Second Shield Glance:** A circular gauge complication showing green (Secure), yellow (Warning), or red (Critical threat).
2. **🚨 Urgent Breach Card with Haptics:** Direct wrist alerts when credential leaks (passwords, session tokens) match verified accounts.
3. **🔒 1-Tap Biometric Lock Confirmation:** Quickly mark and record that Aadhaar biometrics are locked via mAadhaar/UIDAI directly from your wrist.
4. **🔋 Battery & Data Efficiency:** Backed by `/api/v1/companion/glance` with an ultra-compact payload (<1 KB), true OLED black backgrounds (`#000000`), and Always-On Display (AOD) ambient mode.

---

## 📐 Architecture & Specifications

```
apps/wearable/
├── README.md               # Smartwatch architecture & integration guide
└── public/
    ├── index.html          # Circular 360x360 AMOLED UI & simulator chassis
    ├── wearable.css        # OLED dark mode, circular progress ring, transitions
    └── wearable.js         # Companion sync, tile switcher, haptics, 1-tap lock
```

### Display & Ergonomics
- **Display Resolution:** 360 × 360 px circular AMOLED (standard Wear OS & 41/45mm Apple Watch target)
- **Minimum Tap Target:** > 48 dp on all watch face buttons
- **Contrast Ratio:** > 7:1 (exceeds WCAG AAA requirements for sunlight readability)
- **Sync Protocol:** Periodic 15s polling or Bluetooth LE push from paired mobile device
- **Haptics:** Multi-pulse alert patterns for high/critical security events (`[150ms, 80ms, 150ms]`)

---

## 🚀 Running the Wearable Client

The wearable interface is served directly by the platform backend:

1. Start the API server:
   ```bash
   uv run uvicorn services.api.main:app --host 0.0.0.0 --port 8000
   ```
2. Open in your browser or Wear OS web view:
   ```
   http://localhost:8000/wearable
   ```
3. Use the **Simulator Controls** panel to test:
   - Switching between **Active AMOLED** and **Ambient AOD** modes.
   - Injecting a simulated **Red Threat Alert** with haptic vibration.
   - Swiping or tapping through the 3 watch tiles (Shield Glance, Urgent Alert, Biometrics Quick Lock).
