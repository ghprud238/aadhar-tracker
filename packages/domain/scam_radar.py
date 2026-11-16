"""
Scam Radar & Adversarial Threat Analyzer.
Provides heuristics and pattern matching for Indian cybercrime epidemics:
1. "Digital Arrest" & Fake Law Enforcement Video Call Scams (CBI / Mumbai Police / ED / Customs).
2. Malicious Android APK Sideload SMS Scams (Electricity Bill / Traffic Challan / Courier hold).
3. Urgent SIM / Banking Disconnection Threats.
"""
import re
from typing import List, Dict, Any, Tuple
from packages.domain.schemas import ScamAnalysisDTO


DIGITAL_ARREST_KEYWORDS = [
    r"digital\s*arrest",
    r"cbi\s*(officer|investigation|headquarters)",
    r"narcotics\s*control\s*bureau|ncb",
    r"enforcement\s*directorate|ed\s*office",
    r"mumbai\s*cyber\s*police|crime\s*branch",
    r"skype\s*(call|interrogation|verification)",
    r"customs\s*(clearance|confiscation|parcel)",
    r"illegal\s*(substance|contraband|drugs)\s*found",
    r"stay\s*on\s*video\s*call",
    r"do\s*not\s*disconnect\s*the\s*call",
    r"money\s*laundering\s*case",
    r"warrant\s*issued",
]

APK_SIDELOAD_PATTERNS = [
    r"\.apk(\b|\?|$)",
    r"download\s*(app|application|update)\s*from",
    r"bit\.ly/|tinyurl\.com/|is\.gd/|t\.co/",
    r"(bescom|mahadiscom|tneb|dhbvn|uppcl|bill).*\.apk",
    r"(challan|parivahan|traffic).*\.apk",
    r"(india-post|speedpost|courier).*\.apk",
    r"install\s*to\s*update\s*(kyc|pan|aadhaar)",
]

DISCONNECTION_THREAT_PATTERNS = [
    r"power\s*will\s*be\s*disconnected\s*tonight",
    r"electricity\s*supply\s*will\s*be\s*cut",
    r"sim\s*card\s*will\s*be\s*blocked\s*within\s*\d+\s*(hours|minutes)",
    r"bank\s*account\s*frozen\s*immediately",
    r"contact\s*officer\s*at\s*(\+91|\d{10})",
]


class ScamRadarEngine:
    @classmethod
    def analyze_message(
        cls,
        message_text: str,
        sender_header: str | None = None,
        channel: str = "sms",
        suspect_claims: str | None = None
    ) -> ScamAnalysisDTO:
        text_lower = (message_text + " " + (suspect_claims or "")).lower()
        matched_indicators: List[str] = []
        is_scam = False
        threat_level = "safe"
        scam_category = "legitimate_notice"
        confidence_score = 0.0

        # 1. Check for Digital Arrest Indicators
        digital_arrest_matches = [
            kw for kw in DIGITAL_ARREST_KEYWORDS if re.search(kw, text_lower, re.IGNORECASE)
        ]
        if digital_arrest_matches or channel == "video_call":
            if digital_arrest_matches:
                matched_indicators.extend([f"Digital arrest / Police impersonation keyword: '{m}'" for m in digital_arrest_matches])
                is_scam = True
                threat_level = "critical"
                scam_category = "digital_arrest_impersonation"
                confidence_score = min(0.99, round(0.70 + (len(digital_arrest_matches) * 0.10), 2))

        # 2. Check for Malicious APK Sideloading
        apk_matches = [
            pat for pat in APK_SIDELOAD_PATTERNS if re.search(pat, text_lower, re.IGNORECASE)
        ]
        if apk_matches:
            matched_indicators.extend([f"Dangerous Android package / shortened URL detected: '{p}'" for p in apk_matches])
            is_scam = True
            threat_level = "critical"
            if scam_category != "digital_arrest_impersonation":
                scam_category = "malicious_apk_sideload"
            confidence_score = max(confidence_score, 0.95)

        # 3. Check for Disconnection Urgency Extortion
        disconnect_matches = [
            pat for pat in DISCONNECTION_THREAT_PATTERNS if re.search(pat, text_lower, re.IGNORECASE)
        ]
        if disconnect_matches:
            matched_indicators.extend([f"Urgent utility disconnection extortion pattern: '{d}'" for d in disconnect_matches])
            is_scam = True
            if threat_level != "critical":
                threat_level = "high"
            if scam_category == "legitimate_notice":
                scam_category = "electricity_bill_urgency"
            confidence_score = max(confidence_score, 0.88)

        # Sender header heuristic check
        if sender_header:
            sh_clean = sender_header.strip().upper()
            if re.match(r"^\+?\d{10,13}$", sh_clean) and (apk_matches or disconnect_matches):
                matched_indicators.append(f"Official utility / bank notice sent from personal mobile number ({sender_header}) rather than authorized telemarketer header (e.g. VM-BESCOM)")
                is_scam = True
                confidence_score = min(1.0, confidence_score + 0.1)

        # Official Advisories
        mha_official_advisory = (
            "OFFICIAL MINISTRY OF HOME AFFAIRS (MHA) & INDIAN CYBER CRIME COORDINATION CENTRE (I4C) ADVISORY:\n"
            "1. NO POLICE OFFICER, CBI, ED, CUSTOMS, OR JUDICIAL AUTHORITY IN INDIA EVER CONDUCTS ARRESTS, "
            "INVESTIGATIONS, OR EVIDENCE HEARINGS VIA SKYPE, WHATSAPP, OR VIDEO CALLS.\n"
            "2. THERE IS NO PROVISION FOR 'DIGITAL ARREST' UNDER ANY INDIAN LAW (BNS, CrPC, IT ACT).\n"
            "3. DO NOT TRANSFER ANY 'CLEARANCE DEPOSIT' OR 'VERIFICATION FUNDS' TO ANY ACCOUNT.\n"
            "4. NEVER DOWNLOAD UNVERIFIED '.APK' FILES FROM SMS OR WHATSAPP. POWER COMPANIES DO NOT SEND APK LINKS.\n"
            "5. IMMEDIATELY DIAL 1930 OR REPORT AT CYBERCRIME.GOV.IN."
        )

        statutory_clauses = [
            "Section 66C, Information Technology Act, 2000 (Identity Theft & Impersonation)",
            "Section 66D, Information Technology Act, 2000 (Cheating by Personation using Computer Resource)",
            "Section 319 / 318, Bharatiya Nyaya Sanhita, 2023 (Cheating & Extortion)",
            "Section 43, Aadhaar (Targeted Delivery of Financial Subsidies) Act, 2016",
        ]

        prefilled_fir = (
            f"FORMAL COMPLAINT TO NATIONAL CYBER CRIME REPORTING PORTAL (cybercrime.gov.in) & 1930 HELPLINE\n"
            f"INCIDENT CATEGORY: {scam_category.upper().replace('_', ' ')}\n"
            f"SUSPECT DETAILS: Sender Header / Contact: {sender_header or 'Unknown Suspect'}\n"
            f"SUMMARY OF EXTORTION ATTEMPT:\n"
            f"The complainant received a deceptive communication on channel '{channel}' with message content:\n"
            f"\"{message_text[:300]}\"\n\n"
            f"INDICATORS DETECTED:\n" + "\n".join(f"- {i}" for i in matched_indicators) + "\n\n"
            f"STATUTORY PROVISIONS INVOKED: IT Act Sec 66C/66D & BNS Sec 318/319.\n"
            f"PRAYER: Immediate freezing of suspect phone number, UPI VPA, and bank beneficiary accounts."
        )

        return ScamAnalysisDTO(
            is_scam=is_scam,
            threat_level=threat_level,
            scam_category=scam_category,
            matched_indicators=matched_indicators,
            mha_official_advisory=mha_official_advisory,
            statutory_clauses=statutory_clauses,
            prefilled_fir_draft=prefilled_fir,
            confidence_score=confidence_score if is_scam else 0.05
        )
