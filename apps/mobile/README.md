# Suraksha Mobile Client (React Native / Expo + TypeScript)

Cross-platform iOS and Android identity monitoring, breach intelligence, and Aadhaar/PAN assistance application.

---

## 📱 Features

- **🛡️ Real-Time Shield Glance:** Instant snapshot of identity protection status (Secure, Warning, Critical) calculated deterministically from active incidents and verified coverage.
- **🔑 Consent-First Identities:** Enrol, verify via challenge tokens, pause, resume, and revoke email identifiers. All values are stored server-side with AES-256-GCM envelope encryption and blind indexes.
- **⚠️ Incident Triage & Remediation:** Browse breach alerts attributed to verified intelligence sources (HIBP, Flare), review exposed data classes, complete step-by-step remediation checklists, and log false-positive disputes.
- **🇮🇳 Aadhaar & PAN Assistance:** Offline-ready, step-by-step guidance on locking Aadhaar biometrics via UIDAI `myaadhaar.uidai.gov.in` and mAadhaar, checking PAN-Aadhaar linkage, and filing unauthorized authentication reports.
- **🔐 Mobile Security & Biometrics:** Local device biometric protection (Face ID, Touch ID, Fingerprint), step-up password authentication for privileged actions, data export, and DPDP Act account erasure requests.

---

## 🛠️ Architecture

```
apps/mobile/
├── App.tsx                     # Entrypoint with bottom tab navigation & top app bar
├── app.json                    # Expo configuration & native permissions (Biometrics, Vibrate)
├── package.json                # Dependencies (React Native 0.74, Expo 51, TypeScript)
├── tsconfig.json               # TypeScript compiler options
└── src/
    ├── types/index.ts          # Shared TypeScript domain contracts
    ├── services/api.ts         # Backend API client with token caching & session handling
    └── screens/
        ├── DashboardScreen.tsx # Shield status, quick scan, urgent breach ticker
        ├── IdentitiesScreen.tsx # Monitored email management with OTP verification
        ├── IncidentsScreen.tsx # Breach list, severity pills, dispute flow, remediations
        ├── AadhaarPanScreen.tsx# Offline biometric lock guide & fraud reporting
        └── SecurityScreen.tsx  # Biometric app lock, step-up auth, DPDP data export
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Node.js 18+ (tested on Node v24.15)
- npm or yarn

### 2. Install Dependencies
```bash
cd apps/mobile
npm install
```

### 3. Run Development Server
```bash
# Start Expo bundler
npx expo start

# Run on iOS simulator (macOS with Xcode)
npm run ios

# Run on Android emulator (with Android Studio / AVD)
npm run android

# Run in Web browser
npm run web
```

### 4. Connecting to Backend
By default, `api.ts` connects to `http://localhost:8000/api/v1`.
When running on a physical phone with Expo Go, update the backend host to your computer's local Wi-Fi IP address in `src/services/api.ts` (e.g. `http://192.168.1.50:8000/api/v1`) or configure environment variables.
