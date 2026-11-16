/**
 * On-Device Scam & Digital Arrest Threat Radar
 * 
 * Provides heuristics for:
 * 1. "Digital Arrest" & Fake Law Enforcement Video Call Scams (CBI / Mumbai Police / ED / Customs).
 * 2. Malicious Android APK Sideload SMS Scams (Electricity Bill / Traffic Challan / Courier hold).
 * 3. Urgent Utility / SIM Disconnection Threats.
 */

export interface ScamAnalysisResult {
  isScam: boolean;
  threatLevel: 'critical' | 'high' | 'medium' | 'safe';
  scamCategory: 'digital_arrest_impersonation' | 'malicious_apk_sideload' | 'electricity_bill_urgency' | 'traffic_challan_fraud' | 'legitimate_notice';
  matchedIndicators: string[];
  mhaOfficialAdvisory: string;
  statutoryClauses: string[];
  prefilledFirDraft: string;
  confidenceScore: number;
}

const DIGITAL_ARREST_KEYWORDS = [
  /digital\s*arrest/i,
  /cbi\s*(officer|investigation|headquarters)/i,
  /narcotics\s*control\s*bureau|ncb/i,
  /enforcement\s*directorate|ed\s*office/i,
  /mumbai\s*cyber\s*police|crime\s*branch/i,
  /skype\s*(call|interrogation|verification)/i,
  /customs\s*(clearance|confiscation|parcel)/i,
  /illegal\s*(substance|contraband|drugs)\s*found/i,
  /stay\s*on\s*video\s*call/i,
  /do\s*not\s*disconnect\s*the\s*call/i,
  /money\s*laundering\s*case/i,
  /warrant\s*issued/i,
];

const APK_SIDELOAD_PATTERNS = [
  /\.apk(\b|\?|$)/i,
  /download\s*(app|application|update)\s*from/i,
  /bit\.ly\/|tinyurl\.com\/|is\.gd\/|t\.co\//i,
  /(bescom|mahadiscom|tneb|dhbvn|uppcl|bill).*\.apk/i,
  /(challan|parivahan|traffic).*\.apk/i,
  /(india-post|speedpost|courier).*\.apk/i,
  /install\s*to\s*update\s*(kyc|pan|aadhaar)/i,
];

const DISCONNECTION_PATTERNS = [
  /power\s*will\s*be\s*disconnected\s*tonight/i,
  /electricity\s*supply\s*will\s*be\s*cut/i,
  /sim\s*card\s*will\s*be\s*blocked\s*within\s*\d+\s*(hours|minutes)/i,
  /bank\s*account\s*frozen\s*immediately/i,
  /contact\s*officer\s*at\s*(\+91|\d{10})/i,
];

export class ScamRadarService {
  public static analyzeMessage(
    messageText: string,
    senderHeader?: string,
    channel: 'sms' | 'whatsapp' | 'video_call' | 'phone' = 'sms'
  ): ScamAnalysisResult {
    const text = messageText.trim();
    const matchedIndicators: string[] = [];
    let isScam = false;
    let threatLevel: ScamAnalysisResult['threatLevel'] = 'safe';
    let scamCategory: ScamAnalysisResult['scamCategory'] = 'legitimate_notice';
    let confidence = 0.05;

    // 1. Digital Arrest Checks
    const digitalArrestMatches = DIGITAL_ARREST_KEYWORDS.filter((pat) => pat.test(text));
    if (digitalArrestMatches.length > 0 || channel === 'video_call') {
      if (digitalArrestMatches.length > 0) {
        matchedIndicators.push(...digitalArrestMatches.map((m) => `Digital arrest / Police impersonation keyword detected: ${m.source}`));
        isScam = true;
        threatLevel = 'critical';
        scamCategory = 'digital_arrest_impersonation';
        confidence = Math.min(0.99, 0.75 + digitalArrestMatches.length * 0.08);
      }
    }

    // 2. APK Sideload & Malicious Links
    const apkMatches = APK_SIDELOAD_PATTERNS.filter((pat) => pat.test(text));
    if (apkMatches.length > 0) {
      matchedIndicators.push(...apkMatches.map((p) => `Dangerous Android package / shortened URL detected: ${p.source}`));
      isScam = true;
      threatLevel = 'critical';
      if (scamCategory !== 'digital_arrest_impersonation') {
        scamCategory = 'malicious_apk_sideload';
      }
      confidence = Math.max(confidence, 0.95);
    }

    // 3. Disconnection Extortion Lures
    const disconnectMatches = DISCONNECTION_PATTERNS.filter((pat) => pat.test(text));
    if (disconnectMatches.length > 0) {
      matchedIndicators.push(...disconnectMatches.map((d) => `Urgent utility disconnection extortion pattern: ${d.source}`));
      isScam = true;
      if (threatLevel !== 'critical') threatLevel = 'high';
      if (scamCategory === 'legitimate_notice') scamCategory = 'electricity_bill_urgency';
      confidence = Math.max(confidence, 0.88);
    }

    // Header heuristic
    if (senderHeader && /^\+?\d{10,13}$/.test(senderHeader.trim()) && (apkMatches.length > 0 || disconnectMatches.length > 0)) {
      matchedIndicators.push(`Notice sent from personal mobile number (${senderHeader}) rather than official carrier telemarketer header (e.g. VM-BESCOM)`);
      isScam = true;
      confidence = Math.min(1.0, confidence + 0.1);
    }

    const mhaOfficialAdvisory = 
      "OFFICIAL MHA & I4C CYBERCRIME ADVISORY:\n" +
      "1. NO POLICE OFFICER, CBI, ED, CUSTOMS, OR JUDICIAL AUTHORITY IN INDIA EVER CONDUCTS ARRESTS OR INVESTIGATIONS OVER SKYPE, WHATSAPP, OR VIDEO CALLS.\n" +
      "2. THERE IS NO PROVISION FOR 'DIGITAL ARREST' UNDER ANY INDIAN LAW.\n" +
      "3. NEVER TRANSFER 'CLEARANCE FUNDS' TO ANY BANK ACCOUNT OR UPI ID.\n" +
      "4. NEVER DOWNLOAD '.APK' FILES FROM UNVERIFIED SMS OR WHATSAPP.\n" +
      "5. REPORT IMMEDIATELY BY DIALING 1930 OR VISITING CYBERCRIME.GOV.IN.";

    const statutoryClauses = [
      "Section 66C, Information Technology Act, 2000 (Identity Theft & Impersonation)",
      "Section 66D, Information Technology Act, 2000 (Cheating by Personation using Computer Resource)",
      "Section 319 / 318, Bharatiya Nyaya Sanhita, 2023 (Cheating & Extortion)",
      "Section 43, Aadhaar Act, 2016 (Penalty for Unauthorized Access)",
    ];

    const prefilledFir = 
      `FORMAL COMPLAINT TO NATIONAL CYBER CRIME REPORTING PORTAL (cybercrime.gov.in) & 1930 HELPLINE\n` +
      `INCIDENT CATEGORY: ${scamCategory.toUpperCase().replace(/_/g, ' ')}\n` +
      `SUSPECT DETAILS: Sender Header / Contact: ${senderHeader || 'Unknown Suspect'}\n` +
      `SUMMARY OF EXTORTION ATTEMPT:\n` +
      `The complainant received a deceptive communication on channel '${channel}' with message content:\n` +
      `"${text.slice(0, 300)}"\n\n` +
      `INDICATORS DETECTED:\n` + matchedIndicators.map((i) => `- ${i}`).join('\n') + `\n\n` +
      `STATUTORY PROVISIONS INVOKED: IT Act Sec 66C/66D & BNS Sec 318/319.\n` +
      `PRAYER: Immediate freezing of suspect phone number, UPI VPA, and bank beneficiary accounts.`;

    return {
      isScam,
      threatLevel,
      scamCategory,
      matchedIndicators,
      mhaOfficialAdvisory,
      statutoryClauses,
      prefilledFirDraft: prefilledFir,
      confidenceScore: confidence,
    };
  }
}
