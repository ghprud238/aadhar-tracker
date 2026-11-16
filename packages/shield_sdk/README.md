# @suraksha/shield-sdk

**Embedded Mobile & Web Banking Fraud Defense SDK**  
*Built for Tier-1 Indian Banks (HDFC, ICICI, SBI) and UPI Applications (PhonePe, Paytm, CRED)*

---

## 🛡️ Overview

`@suraksha/shield-sdk` is an ultra-lightweight, zero-external-dependency embedded fraud prevention library designed to protect Indian banking and digital lending applications directly on the client device.

It complies with **RBI Digital Payment Security Guidelines (2021)**, **UIDAI Masked Aadhaar Circular (2022)**, and **DPDP Act (2023)**.

### Key Capabilities:
- **Client-Side Scam Radar (<1ms latency)**: Identifies MHA/I4C Digital Arrest extortion patterns, malicious APK sideload links, and utility disconnection scams offline on-device.
- **Mathematical Verhoeff & PAN Validator**: Validates Aadhaar Dihedral $D_5$ checksums and PAN structure client-side, enforcing the Zero-Plaintext Invariant before any network transmission.
- **10-Minute Biometric Window Countdown**: Automatically manages temporary biometric unlock windows for legitimate AePS/KYC operations with automated re-lock callbacks.
- **Device Posture & Remote Access Monitor**: Detects screen sharing (AnyDesk, TeamViewer) and accessibility abuse risks.
- **Self-Destructing Clipboard Buffer**: Memory-wipes sensitive OTPs and masked credentials after 45 seconds to neutralize background spyware.
- **Aggregated Zero-PII Telemetry**: Delivers security posture telemetry to bank CISO dashboards without ever logging resident PII.

---

## 📦 Installation

```bash
npm install @suraksha/shield-sdk
# or
yarn add @suraksha/shield-sdk
```

---

## 🚀 Quick Start (React Native / Web)

```typescript
import { SurakshaShield } from "@suraksha/shield-sdk";

// 1. Initialize inside your Bank App entry point
const shield = SurakshaShield.init({
  apiKey: "sk_live_bank_sample_key",
  tenantId: "tenant_hdfc_bank_prod",
  bankIdentifier: "HDFC_BANK",
  environment: "production",
  enforceZeroPlaintext: true,
  sensitivity: "strict"
});

// 2. Scan incoming message or clipboard text for scams
const result = shield.evaluateMessage(
  "Urgent: CBI Mumbai has issued an arrest warrant. Join Skype video call immediately.",
  "+919876543210"
);

if (result.isScam) {
  console.warn("BLOCKED SCAM:", result.advisory);
  // Display official MHA advisory to the customer
}

// 3. Client-side Aadhaar Verhoeff validation & automatic masking
const val = shield.validateIdentifier("aadhaar", "999924467773");
if (val.isValid) {
  console.log("Safe Masked Aadhaar:", val.maskedValue); // "XXXX-XXXX-7773"
}

// 4. Managed 10-Minute Biometric Unlock Window
const bioWindow = shield.startBiometricWindow(10, () => {
  // Callback when 10 minutes expire:
  console.log("Window expired! Prompting user to re-lock Aadhaar biometrics.");
});
```
