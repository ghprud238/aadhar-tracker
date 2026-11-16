"""
Synthetic data generator for Indian Identity Protection Platform (Suraksha).
Generates mathematically valid, privacy-safe synthetic test identities:
- Aadhaar (Verhoeff Dihedral D5 Checksum in sandbox 9999... range)
- PAN (Income Tax format)
- Virtual ID (VID 16 digits)
- Driving License (Indian RTO 15-char standard)
- Voter ID (EPIC 10-char format)
- Indian Passport (8-char format)
- Bank Account & IFSC details
- Vehicle RC (Registration Certificate)
- Monitored Telecom SIMs (with Ghost SIM detection)
- Credit Bureau Inquiry Profiles (CIBIL/Experian)
- Simulated dark-web breach catalog dumps (15 multi-sector threat templates)
- Scam & Phishing labeled corpus (Digital Arrest, APK sideload, Disconnection, Clean controls)
- Certified Ed25519 & UIDAI Secure QR pass payloads
- WhatsApp DLP chat threads with sensitive identifier disclosures
"""
import json
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta

# Ensure project root is accessible for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.domain.verhoeff import (
    generate_verhoeff_checksum,
    validate_aadhaar,
    validate_pan,
    validate_verhoeff,
)


FIRST_NAMES = [
    "Aarav", "Diya", "Rohan", "Pooja", "Karthik", "Ananya", "Vikram", "Sneha",
    "Arjun", "Priya", "Rajesh", "Meera", "Siddharth", "Ishaan", "Kavya", "Aditya",
    "Tanvi", "Nikhil", "Ritu", "Amit", "Deepa", "Suresh", "Lakshmi", "Varun", "Sunita",
    "Harish", "Preeti", "Gautam", "Neha", "Manish", "Divya", "Sanjay", "Swati",
    "Venkatesh", "Anjali", "Pranav", "Nandini", "Abhishek", "Shruti", "Kunal"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Iyer", "Reddy", "Gupta", "Mukherjee", "Nair",
    "Kulkarni", "Singh", "Das", "Menon", "Joshi", "Bose", "Choudhury", "Pillai",
    "Rao", "Agarwal", "Bhat", "Deshmukh", "Ghosh", "Chatterjee", "Pandey", "Mehta",
    "Natarajan", "Bhattacharya", "Sengupta", "Chauhan", "Trivedi", "Banerjee", "Soni"
]

CITIES_AND_STATES = [
    ("Mumbai", "Maharashtra", "MH", "400001"),
    ("Bengaluru", "Karnataka", "KA", "560001"),
    ("New Delhi", "Delhi", "DL", "110001"),
    ("Hyderabad", "Telangana", "TS", "500001"),
    ("Chennai", "Tamil Nadu", "TN", "600001"),
    ("Kolkata", "West Bengal", "WB", "700001"),
    ("Pune", "Maharashtra", "MH", "411001"),
    ("Ahmedabad", "Gujarat", "GJ", "380001"),
    ("Jaipur", "Rajasthan", "RJ", "302001"),
    ("Kochi", "Kerala", "KL", "682001"),
    ("Lucknow", "Uttar Pradesh", "UP", "226001"),
    ("Chandigarh", "Punjab", "PB", "160001"),
    ("Bhopal", "Madhya Pradesh", "MP", "462001"),
    ("Patna", "Bihar", "BR", "800001"),
    ("Bhubaneswar", "Odisha", "OD", "751001"),
]

INDIAN_BANKS = [
    ("State Bank of India", "SBIN", "0001234"),
    ("HDFC Bank", "HDFC", "0005678"),
    ("ICICI Bank", "ICIC", "0001122"),
    ("Axis Bank", "UTIB", "0000987"),
    ("Punjab National Bank", "PUNB", "0004321"),
    ("Bank of Baroda", "BARB", "0008899"),
    ("Kotak Mahindra Bank", "KKBK", "0003344"),
]

BREACH_TEMPLATES = [
    {
        "name": "Bharat Telecom KYC Leak 2026",
        "source": "BreachForums v3 (Tor)",
        "source_type": "telecom_breach",
        "severity": "critical",
        "compromised_data_classes": ["email", "phone", "aadhaar", "pan", "address"],
        "description": "Exfiltrated customer onboarding KYC database dump containing verified Aadhaar and PAN documents.",
    },
    {
        "name": "QuickRupee Microfinance Applicant Archive",
        "source": "Exploit.in (Darknet)",
        "source_type": "fintech_leak",
        "severity": "critical",
        "compromised_data_classes": ["email", "phone", "pan", "bank_account", "salary_slip"],
        "description": "SQL injection exploit dumping loan applicant records and unmasked PAN identifiers.",
    },
    {
        "name": "Lumma Stealer Botnet Campaign #812",
        "source": "Telegram Private Stealer Channel",
        "source_type": "stealer_log",
        "severity": "critical",
        "compromised_data_classes": ["email", "password_hash", "browser_autofill", "aadhaar_pdf", "session_cookies"],
        "description": "Infostealer log bundle dumped from infected Windows workstations with cached government documents.",
    },
    {
        "name": "Metro Diagnostics Health Records Leak",
        "source": "Dark Web Pastebin / I2P",
        "source_type": "healthcare_leak",
        "severity": "high",
        "compromised_data_classes": ["name", "phone", "aadhaar", "medical_reports"],
        "description": "Unprotected Amazon S3 cloud bucket containing patient registration files and Aadhaar photocopies.",
    },
    {
        "name": "HotelEase Guest Registry Exposure",
        "source": "Ransomware Data Leak Site (LockBit)",
        "source_type": "hospitality_leak",
        "severity": "medium",
        "compromised_data_classes": ["name", "phone", "id_proof_masked", "stay_history"],
        "description": "Hospitality booking database exposing guest identity proofs submitted during check-in.",
    },
    {
        "name": "SkyHigh Airlines Passenger Manifest Dump",
        "source": "Underground Aviation Leaks Forum",
        "source_type": "travel_leak",
        "severity": "high",
        "compromised_data_classes": ["name", "email", "phone", "passport_number", "travel_history"],
        "description": "Compromised internal API gateway exposing frequent flyer profiles and passport numbers.",
    },
    {
        "name": "EduLearn Student Aadhaar & Fee Ledger",
        "source": "Public GitHub Repository Scraping",
        "source_type": "edtech_leak",
        "severity": "high",
        "compromised_data_classes": ["student_name", "email", "parent_aadhaar", "fee_receipt"],
        "description": "Accidentally committed database dump file containing parent Aadhaar numbers and contact info.",
    },
    {
        "name": "CoinDesi Crypto KYC Vault Leak",
        "source": "RaidForums Mirror",
        "source_type": "crypto_leak",
        "severity": "critical",
        "compromised_data_classes": ["email", "phone", "pan_image", "aadhaar_image", "selfie_photo"],
        "description": "Compromised AWS S3 bucket holding unmasked citizen KYC verification images for crypto trading.",
    },
    {
        "name": "PayDirect Merchant Bank Account Dump",
        "source": "Dark Web Marketplace Dump",
        "source_type": "payment_gateway_leak",
        "severity": "critical",
        "compromised_data_classes": ["merchant_name", "phone", "pan_number", "bank_account", "ifsc"],
        "description": "Aggregated merchant settlements archive exposing PAN and active business bank accounts.",
    },
    {
        "name": "CityRide Driver Licensing Database",
        "source": "BreachForums Database Listing",
        "source_type": "rideshare_leak",
        "severity": "medium",
        "compromised_data_classes": ["driver_name", "phone", "driving_license", "vehicle_rc"],
        "description": "Onboarding database for commercial cab drivers with driving license numbers and vehicle registrations.",
    },
    {
        "name": "RedLine Stealer Credential Dump #441",
        "source": "Stealer Log Torrent",
        "source_type": "stealer_log",
        "severity": "critical",
        "compromised_data_classes": ["email", "password_hash", "netbanking_login", "pan_card_doc"],
        "description": "Consumer endpoint logs containing saved browser passwords and downloaded e-Aadhaar PDFs.",
    },
    {
        "name": "BharatPay AePS Micro-ATM Transaction Log",
        "source": "Telegram Financial Fraud Feed",
        "source_type": "aeps_leak",
        "severity": "critical",
        "compromised_data_classes": ["aadhaar_last4", "iinp", "terminal_id", "biometric_auth_status", "amount"],
        "description": "Leaked AePS transaction telemetry used by fraudsters for fingerprint clone financial attacks.",
    },
    {
        "name": "Apex Hospital Patient Diagnostic Records",
        "source": "Dark Web Pastebin",
        "source_type": "healthcare_leak",
        "severity": "high",
        "compromised_data_classes": ["patient_name", "age", "aadhaar", "prescription_history"],
        "description": "Hospital lab information system exposing patient demographic profiles and scanned identity cards.",
    },
    {
        "name": "SpeedPost Delivery Roster Leak",
        "source": "Darknet Forum Post",
        "source_type": "courier_leak",
        "severity": "low",
        "compromised_data_classes": ["recipient_name", "phone", "address", "consignment_type"],
        "description": "Exposed delivery consignment roster utilized by phishing groups for fake parcel arrival scams.",
    },
    {
        "name": "DoT Sanchar Saathi Bulk TAFCOP Scrape",
        "source": "Underground Telecom SIM Ring",
        "source_type": "telecom_leak",
        "severity": "critical",
        "compromised_data_classes": ["name", "aadhaar_masked", "registered_sim_count", "active_phone_numbers"],
        "description": "Aggregated list of citizens with multiple SIM cards targeted for SIM-swap extortion.",
    },
]


def generate_synthetic_aadhaar(
    prefix_range: str = "9999",
    formatted: bool = True,
    seed: Optional[int] = None
) -> str:
    """
    Generates a mathematically valid 12-digit Aadhaar number with Verhoeff dihedral D5 checksum.
    By default uses prefix_range '9999' (official developer sandbox range) to ensure zero collisions
    with real citizens.
    """
    rng = random.Random(seed) if seed is not None else random
    
    clean_prefix = "".join(filter(str.isdigit, prefix_range))
    if not clean_prefix or clean_prefix[0] in ("0", "1"):
        clean_prefix = "9999"

    needed_random = 11 - len(clean_prefix)
    if needed_random > 0:
        middle_digits = "".join(str(rng.randint(0, 9)) for _ in range(needed_random))
    else:
        middle_digits = ""
    
    prefix_11 = (clean_prefix + middle_digits)[:11]
    check_digit = generate_verhoeff_checksum(prefix_11)
    full_aadhaar = prefix_11 + check_digit

    is_valid, _, _ = validate_aadhaar(full_aadhaar)
    assert is_valid, f"Generated synthetic Aadhaar {full_aadhaar} failed Verhoeff validation"

    if formatted:
        return f"{full_aadhaar[:4]} {full_aadhaar[4:8]} {full_aadhaar[8:]}"
    return full_aadhaar


def generate_synthetic_pan(
    last_name: str = "Sharma",
    entity_type: str = "P",
    seed: Optional[int] = None
) -> str:
    """
    Generates a valid 10-character PAN number matching Indian Income Tax format:
    Characters 1-3: Random uppercase letters
    Character 4: Entity status code ('P' for Individual, 'C' for Company, 'H' for HUF)
    Character 5: First letter of surname
    Characters 6-9: 4 sequential or random digits
    Character 10: Alphabetic check character
    """
    rng = random.Random(seed) if seed is not None else random
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    c1_3 = "".join(rng.choice(letters) for _ in range(3))
    
    status = entity_type.upper() if entity_type.upper() in "PCHFA" else "P"
    surname_initial = last_name[0].upper() if last_name else "S"
    if not surname_initial.isalpha():
        surname_initial = "S"
        
    digits_4 = f"{rng.randint(1000, 9999):04d}"
    last_char = rng.choice(letters)
    
    pan = f"{c1_3}{status}{surname_initial}{digits_4}{last_char}"
    is_valid, _, _ = validate_pan(pan)
    assert is_valid, f"Generated synthetic PAN {pan} failed validation"
    return pan


def generate_synthetic_vid(seed: Optional[int] = None) -> str:
    """Generates a synthetic 16-digit UIDAI Virtual ID (VID)."""
    rng = random.Random(seed) if seed is not None else random
    digits = "".join(str(rng.randint(0, 9)) for _ in range(16))
    return f"{digits[:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:]}"


def generate_synthetic_driving_license(
    state_code: Optional[str] = None,
    issue_year: Optional[int] = None,
    seed: Optional[int] = None
) -> Tuple[str, str]:
    """
    Generates a valid 15-character Indian Driving License number:
    State (2) + RTO Code (2 digits) + Year (4 digits) + 7 Sequential digits.
    Returns: (raw_dl, masked_dl) e.g. ("KA0120190012345", "KA01-****-12345").
    """
    rng = random.Random(seed) if seed is not None else random
    st = state_code.upper() if state_code and len(state_code) == 2 else rng.choice(["KA", "MH", "DL", "TN", "UP", "GJ"])
    rto = f"{rng.randint(1, 99):02d}"
    year = issue_year if issue_year else rng.randint(2012, 2024)
    serial = f"{rng.randint(1, 9999999):07d}"
    
    raw_dl = f"{st}{rto}{year}{serial}"
    masked_dl = f"{st}{rto}-****-{serial[-5:]}"
    return raw_dl, masked_dl


def generate_synthetic_voter_id(seed: Optional[int] = None) -> Tuple[str, str]:
    """
    Generates a valid 10-character Indian Voter ID (EPIC) number:
    3 uppercase letters (Constituency Code) + 7 digits.
    Returns: (raw_epic, masked_epic) e.g. ("ABC1234567", "AB****567").
    """
    rng = random.Random(seed) if seed is not None else random
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    constituency = "".join(rng.choice(letters) for _ in range(3))
    digits = f"{rng.randint(1000000, 9999999):07d}"
    
    raw_epic = f"{constituency}{digits}"
    masked_epic = f"{constituency[:2]}****{digits[-3:]}"
    return raw_epic, masked_epic


def generate_synthetic_passport(seed: Optional[int] = None) -> Tuple[str, str]:
    """
    Generates a valid 8-character Indian Passport number:
    1 uppercase letter (J, K, L, M, P, R, S, T, U, V, W, X, Y, Z) + 7 digits.
    Returns: (raw_passport, masked_passport) e.g. ("J1234567", "J****567").
    """
    rng = random.Random(seed) if seed is not None else random
    valid_letters = "JKLMNPRSTUVWXYZ"
    prefix = rng.choice(valid_letters)
    digits = f"{rng.randint(1000000, 9999999):07d}"
    
    raw_passport = f"{prefix}{digits}"
    masked_passport = f"{prefix}****{digits[-3:]}"
    return raw_passport, masked_passport


def generate_synthetic_bank_account(
    bank_name: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, str]:
    """
    Generates realistic Indian bank account details with valid 11-character IFSC:
    e.g. Bank: State Bank of India, IFSC: SBIN0001234, Account: 309988776655.
    """
    rng = random.Random(seed) if seed is not None else random
    if bank_name:
        bank_match = next((b for b in INDIAN_BANKS if bank_name.lower() in b[0].lower()), INDIAN_BANKS[0])
    else:
        bank_match = rng.choice(INDIAN_BANKS)

    name, code, branch_code = bank_match
    branch_num = f"{rng.randint(1000, 9999):04d}"
    ifsc = f"{code}000{branch_num}"
    
    account_len = rng.choice([11, 12, 14, 16])
    account_digits = "".join(str(rng.randint(0, 9)) for _ in range(account_len))
    account_masked = "X" * (account_len - 4) + account_digits[-4:]
    
    return {
        "bank_name": name,
        "ifsc_code": ifsc,
        "account_raw": account_digits,
        "account_masked": account_masked
    }


def generate_synthetic_vehicle_rc(
    state_code: Optional[str] = None,
    seed: Optional[int] = None
) -> Tuple[str, str]:
    """
    Generates a valid Indian Vehicle Registration Certificate (RC) number:
    e.g. ("KA05MB1234", "KA05-**-1234").
    """
    rng = random.Random(seed) if seed is not None else random
    st = state_code.upper() if state_code and len(state_code) == 2 else rng.choice(["KA", "MH", "DL", "TN", "UP", "GJ"])
    rto = f"{rng.randint(1, 99):02d}"
    series = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(2))
    num = f"{rng.randint(1000, 9999):04d}"
    
    raw_rc = f"{st}{rto}{series}{num}"
    masked_rc = f"{st}{rto}-**-{num}"
    return raw_rc, masked_rc


def generate_synthetic_telecom_sims(
    resident_phone: Optional[str] = None,
    count: int = 2,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generates synthetic monitored SIM cards linked to an Indian resident (as reported by DoT TAFCOP).
    Includes ghost SIMs (unauthorized SIMs issued without citizen knowledge).
    """
    rng = random.Random(seed) if seed is not None else random
    carriers = ["Jio 5G", "Airtel 5G", "Vodafone Idea (Vi)", "BSNL"]
    circles = ["Karnataka", "Maharashtra", "Delhi NCR", "Tamil Nadu", "Mumbai", "Telangana"]
    
    sims = []
    # Primary SIM
    primary_num = resident_phone if resident_phone else f"+9198{rng.randint(10000000, 99999999)}"
    sims.append({
        "phone_number": primary_num,
        "carrier": rng.choice(carriers),
        "telecom_circle": rng.choice(circles),
        "is_primary": True,
        "is_authorized_by_resident": True,
        "issued_on": (datetime.now(timezone.utc) - timedelta(days=rng.randint(300, 1500))).strftime("%Y-%m-%d"),
        "status": "active"
    })
    
    # Secondary SIMs (some potentially ghost SIMs)
    for i in range(1, count):
        is_ghost = (i == count - 1 and rng.random() > 0.6)  # 40% chance of ghost SIM for last entry
        phone = f"+919{rng.randint(100000000, 999999999)}"
        sims.append({
            "phone_number": phone,
            "carrier": rng.choice(carriers),
            "telecom_circle": rng.choice(circles),
            "is_primary": False,
            "is_authorized_by_resident": not is_ghost,
            "flagged_as_ghost_sim": is_ghost,
            "issued_on": (datetime.now(timezone.utc) - timedelta(days=rng.randint(30, 200))).strftime("%Y-%m-%d"),
            "status": "flagged_unauthorized" if is_ghost else "active"
        })
        
    return sims


def generate_synthetic_credit_profile(
    pan_number: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Generates synthetic Credit Bureau (CIBIL/Experian) profile telemetry."""
    rng = random.Random(seed) if seed is not None else random
    score = rng.randint(650, 850)
    
    inquiries = []
    lenders = ["HDFC Bank", "Bajaj Finance", "SBI Cards", "Axis Bank", "Tata Capital", "KreditBee"]
    num_inquiries = rng.randint(0, 3)
    for _ in range(num_inquiries):
        is_unauthorized = rng.random() > 0.7
        inquiries.append({
            "institution": rng.choice(lenders),
            "purpose": rng.choice(["Personal Loan", "Credit Card", "Instant Micro-Credit", "Auto Loan"]),
            "inquiry_type": "Hard Pull",
            "date": (datetime.now(timezone.utc) - timedelta(days=rng.randint(2, 60))).strftime("%Y-%m-%d"),
            "is_authorized": not is_unauthorized,
            "flagged_suspicious": is_unauthorized
        })
        
    return {
        "pan_number": pan_number or "ABCPS1234D",
        "cibil_score": score,
        "score_band": "Excellent" if score >= 800 else "Good" if score >= 750 else "Fair",
        "credit_bureau": "TransUnion CIBIL",
        "active_credit_cards": rng.randint(1, 4),
        "recent_hard_inquiries": inquiries,
        "has_unauthorized_inquiries": any(i["flagged_suspicious"] for i in inquiries)
    }


def generate_synthetic_resident_profile(
    seed: Optional[int] = None,
    custom_name: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a comprehensive synthetic Indian resident identity profile with all statutory documents."""
    rng = random.Random(seed) if seed is not None else random
    
    if custom_name:
        parts = custom_name.strip().split()
        first_name = parts[0]
        last_name = parts[-1] if len(parts) > 1 else "Sharma"
    else:
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        
    full_name = f"{first_name} {last_name}"
    email_domain = rng.choice(["example.in", "testmail.co.in", "suraksha-test.org", "demo-resident.in"])
    email = f"{first_name.lower()}.{last_name.lower()}{rng.randint(10, 99)}@{email_domain}"
    phone = f"+9198{rng.randint(10000000, 99999999)}"
    
    city, state, st_code, pin_prefix = rng.choice(CITIES_AND_STATES)
    pincode = f"{pin_prefix[:3]}{rng.randint(100, 999):03d}"
    
    aadhaar_raw = generate_synthetic_aadhaar(formatted=False, seed=rng.randint(1, 100000))
    aadhaar_formatted = f"{aadhaar_raw[:4]} {aadhaar_raw[4:8]} {aadhaar_raw[8:]}"
    aadhaar_masked = f"XXXX-XXXX-{aadhaar_raw[-4:]}"
    
    pan = generate_synthetic_pan(last_name=last_name, entity_type="P", seed=rng.randint(1, 100000))
    pan_masked = f"{pan[:2]}***{pan[5:7]}*{pan[-1]}"
    
    vid = generate_synthetic_vid(seed=rng.randint(1, 100000))
    dl_raw, dl_masked = generate_synthetic_driving_license(state_code=st_code, seed=rng.randint(1, 100000))
    voter_raw, voter_masked = generate_synthetic_voter_id(seed=rng.randint(1, 100000))
    passport_raw, passport_masked = generate_synthetic_passport(seed=rng.randint(1, 100000))
    bank_info = generate_synthetic_bank_account(seed=rng.randint(1, 100000))
    rc_raw, rc_masked = generate_synthetic_vehicle_rc(state_code=st_code, seed=rng.randint(1, 100000))
    
    sims = generate_synthetic_telecom_sims(resident_phone=phone, count=rng.randint(2, 3), seed=rng.randint(1, 100000))
    credit = generate_synthetic_credit_profile(pan_number=pan, seed=rng.randint(1, 100000))

    return {
        "full_name": full_name,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "aadhaar_raw": aadhaar_raw,
        "aadhaar_formatted": aadhaar_formatted,
        "aadhaar_masked": aadhaar_masked,
        "pan_raw": pan,
        "pan_masked": pan_masked,
        "vid_number": vid,
        "driving_license_raw": dl_raw,
        "driving_license_masked": dl_masked,
        "voter_id_raw": voter_raw,
        "voter_id_masked": voter_masked,
        "passport_raw": passport_raw,
        "passport_masked": passport_masked,
        "bank_details": bank_info,
        "vehicle_rc_raw": rc_raw,
        "vehicle_rc_masked": rc_masked,
        "telecom_sims": sims,
        "credit_profile": credit,
        "address": {
            "street": f"Flat {rng.randint(101, 909)}, Surya Enclave",
            "city": city,
            "state": state,
            "state_code": st_code,
            "pincode": pincode,
            "country": "India"
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def generate_synthetic_breach_dump(
    num_records: int = 25,
    template_idx: int = 0,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Generates a realistic simulated dark web breach dump containing synthetic resident profiles."""
    rng = random.Random(seed) if seed is not None else random
    template = BREACH_TEMPLATES[template_idx % len(BREACH_TEMPLATES)]
    
    records = []
    for i in range(num_records):
        prof = generate_synthetic_resident_profile(seed=rng.randint(1, 10000000))
        record = {
            "record_id": f"rec_{i+1:04d}",
            "name": prof["full_name"],
            "email": prof["email"],
            "phone": prof["phone"],
            "aadhaar_number": prof["aadhaar_formatted"],
            "pan_number": prof["pan_raw"],
            "driving_license": prof["driving_license_raw"],
            "voter_id": prof["voter_id_raw"],
            "state": prof["address"]["state"],
            "pincode": prof["address"]["pincode"],
        }
        
        if "password_hash" in template["compromised_data_classes"]:
            record["password_hash"] = f"$2b$12${''.join(rng.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./') for _ in range(53))}"
            record["plaintext_password_redacted"] = "[REDACTED_BY_CTI_POLICY]"

        if "bank_account" in template["compromised_data_classes"]:
            record["bank_account"] = prof["bank_details"]["account_raw"]
            record["ifsc"] = prof["bank_details"]["ifsc_code"]

        if "passport_number" in template["compromised_data_classes"]:
            record["passport_number"] = prof["passport_raw"]

        records.append(record)

    dump_id = f"leak_{template['source_type']}_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{rng.randint(100, 999)}"
    
    return {
        "dump_id": dump_id,
        "breach_name": template["name"],
        "source": template["source"],
        "source_type": template["source_type"],
        "severity": template["severity"],
        "compromised_data_classes": template["compromised_data_classes"],
        "description": template["description"],
        "total_records_in_dump": num_records * 4000,
        "sampled_records": records,
        "dump_discovered_at": datetime.now(timezone.utc).isoformat(),
        "magnet_hash": f"urn:btih:{''.join(rng.choice('0123456789abcdef') for _ in range(40))}",
        "raw_evidence_sha256": f"{''.join(rng.choice('0123456789abcdef') for _ in range(64))}"
    }


def generate_synthetic_whatsapp_conversations(
    num_threads: int = 6,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Generates synthetic WhatsApp message threads with embedded IDs for Data Loss Prevention testing."""
    rng = random.Random(seed) if seed is not None else random
    threads = []
    scenarios = [
        ("HR Onboarding Verification", "office_hr", True),
        ("Hotel Room Booking KYC Proof", "hotel_agent", True),
        ("Personal Loan Executive Chat", "loan_rep", True),
        ("Self-Drive Car Rental Booking", "car_rental", True),
        ("Family Vacation Flight Details", "family_group", False),
        ("Society Maintenance Discussion", "apartment_rwa", False),
    ]

    for i in range(num_threads):
        scenario_title, channel_tag, contains_sensitive_id = scenarios[i % len(scenarios)]
        prof = generate_synthetic_resident_profile(seed=rng.randint(1, 10000000))
        sender_phone = prof["phone"]
        
        messages = []
        if contains_sensitive_id:
            if i % 3 == 0:
                messages = [
                    {"from": "recipient", "text": "Hi, please share your ID proof and PAN card so we can finalize the registration."},
                    {"from": "sender", "text": f"Sure, sending here. My Aadhaar number is {prof['aadhaar_formatted']} and PAN is {prof['pan_raw']}. Please verify."},
                    {"from": "recipient", "text": "Received, thank you!"}
                ]
            elif i % 3 == 1:
                messages = [
                    {"from": "recipient", "text": "Sir, room booking requires government ID proof copy."},
                    {"from": "sender", "text": f"Here is my Aadhaar card details: {prof['aadhaar_formatted']} (Name: {prof['full_name']})"},
                    {"from": "recipient", "text": "Noted. Your booking is confirmed."}
                ]
            else:
                messages = [
                    {"from": "recipient", "text": "Car rental self-drive requires Driving License copy."},
                    {"from": "sender", "text": f"Sharing my Driving License: {prof['driving_license_raw']} and PAN: {prof['pan_raw']}."},
                    {"from": "recipient", "text": "Car is reserved for pickup tomorrow."}
                ]
        else:
            messages = [
                {"from": "sender", "text": "Flight tickets have been booked for Saturday morning."},
                {"from": "recipient", "text": "Great! Did you use the Masked Aadhaar or VID for airport entry?"},
                {"from": "sender", "text": f"Yes, using official VID {prof['vid_number']}. No full Aadhaar shared."}
            ]

        threads.append({
            "thread_id": f"wa_thread_{i+1:03d}",
            "title": scenario_title,
            "channel": channel_tag,
            "sender_name": prof["full_name"],
            "sender_phone": sender_phone,
            "contains_sensitive_id": contains_sensitive_id,
            "sample_profile": prof,
            "messages": messages,
            "last_message_text": messages[1]["text"] if len(messages) > 1 else messages[0]["text"]
        })

    return threads


def generate_synthetic_scam_corpus(
    count: int = 100,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generates a rich labeled dataset of scam, phishing, extortion, and clean control messages.
    Covers Digital Arrest, APK sideloading, Disconnection threats, Vishing, Adversarial homoglyphs, and Clean SMS.
    """
    rng = random.Random(seed) if seed is not None else random
    corpus = []

    # 1. Digital Arrest Scenarios
    da_templates = [
        "Dear citizen, you are placed under DIGITAL ARREST by CBI and Cyber Cell {city}. Your Aadhaar was found in money laundering package at customs. Connect on Skype video call immediately within 2 hours or police team will arrest you.",
        "URGENT NOTICE: An arrest warrant has been issued by Enforcement Directorate (ED) New Delhi for illegal narcotics contraband in your name. Stay on video call for judicial verification.",
        "MUMBAI CRIME BRANCH ALERT: Your bank account is linked to Rs 3.8 Crore international hawala syndicate. Do not disconnect the video call or face non-bailable arrest.",
        "Narcotics Control Bureau (NCB): 16 passports and contraband drugs confiscated with your Aadhaar credentials. Immediate digital arrest order active. Cooperate on Skype.",
        "Supreme Court of India e-Warrant: Case No SC/2026/8192. CBI officer inspecting your premises. Connect via video call for clearance certificate."
    ]

    # 2. Malicious APK Sideload Scenarios
    apk_templates = [
        "Dear {utility} Consumer, your power supply will be disconnected tonight at 9:30 PM due to unpaid bill of Rs {amount}. Immediately update your electricity app by downloading: http://{utility_domain}/update.apk",
        "E-Challan Alert: Traffic violation recorded against your vehicle {vehicle}. Fine unpaid. Download official Parivahan e-Challan payment app: http://parivahan-traffic-fine.in/challan_{rand}.apk",
        "India Post Notice: Your consignment {consignment} is detained at regional hub due to incorrect address. Install postal delivery update app: http://indiapost-speedpost.com/track.apk",
        "PAN-Aadhaar Link Suspension Warning: Income Tax Dept mandates urgent verification. Install ITD-eFiling-Secure.apk from bit.ly/pan_update_{rand} to prevent account freeze.",
        "BSNL / Jio 5G SIM Expiry: Your SIM card will be deactivated in 24 hours. Update KYC immediately by downloading: http://sim-kyc-update.net/telecom.apk"
    ]

    # 3. Disconnection & Extortion Urgency Scenarios
    disconnect_templates = [
        "FINAL NOTICE: Electricity connection will be cut within 1 hour. Pay pending arrears of Rs {amount} immediately or contact Senior Engineer at +91{phone}.",
        "Department of Telecommunications: Your mobile number +91{phone} is involved in 14 fraudulent calls. SIM card will be blocked within 30 minutes. Call officer at +91{phone2}.",
        "Bank Account Suspended: Suspicious login detected from IP 185.220.101.4. Your account is frozen immediately. Contact nodal officer at +91{phone} to unblock."
    ]

    # 4. Bank Vishing & OTP Phishing Scenarios
    vishing_templates = [
        "Dear SBI Customer, your YONO reward points worth Rs 9,850 are expiring today. Claim cash credit to account immediately by entering OTP shared with verification agent.",
        "HDFC Credit Card Alert: International transaction of USD 840.00 initiated on your card at Dubai Mall. If not done by you, share incoming OTP to cancel immediately.",
        "ICICI Bank: KYC expired. NetBanking disabled. Please verify your debit card PIN and OTP on secure link to restore access."
    ]

    # 5. Adversarial Obfuscation Scenarios (Unicode zero-width, homoglyphs)
    adversarial_templates = [
        "D\u200Bi\u200Cg\u200Di\u200Bt\u200Ba\u200Bl A\u200Br\u200Br\u200Be\u200Bs\u200Bt Warrant: CBI Cyber Cell Mumbai requires immediate Skype video call.",
        "Dear BESCOM Customer: Your electricity bill is pending. Install update\u200B.\u200Capk from tinyurl.com/bescom{rand} to prevent disconnection.",
        "СВI Police Notice: Wаrrаnt issued for customs contraband. Stay on vidео cаll."  # Mixed Cyrillic homoglyphs
    ]

    # 6. Legitimate Clean Negative Controls
    clean_templates = [
        "Your one-time password (OTP) for SBI NetBanking transaction of Rs {amount} is {otp}. Valid for 5 mins. Do not share OTP with anyone.",
        "Swiggy: Your food delivery order #{order_id} from Meghana Foods is on the way. Delivery executive will reach in 14 minutes.",
        "IRCTC PNR {pnr}: Booking confirmed. Train 12658 Chennai Mail, Coach B2 Berth 34 (Side Lower). Departure 21:15 HRS. Happy Journey!",
        "Amazon.in: Package containing your order #{order_id} is out for delivery today with PIN {pin}. Track on the app.",
        "UIDAI: OTP for online Aadhaar authentication is {otp}. Generated at {time}. If not requested, visit myaadhaar.uidai.gov.in."
    ]

    utilities = [
        ("BESCOM", "bescom-karnataka-bill.in"),
        ("Mahadiscom", "mahadiscom-power-pay.net"),
        ("UPPCL", "uppcl-bijli-update.in"),
        ("TNEB", "tneb-electricity-bill.com"),
        ("DHBVN", "dhbvn-haryana-power.net")
    ]

    cities = ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Chennai", "Kolkata"]

    for i in range(count):
        cat_selector = i % 6
        rand_val = rng.randint(100, 999)
        amount = rng.randint(450, 9800)
        otp = f"{rng.randint(100000, 999999)}"
        phone1 = f"98{rng.randint(10000000, 99999999)}"
        phone2 = f"97{rng.randint(10000000, 99999999)}"

        if cat_selector == 0:
            # Digital arrest
            tmpl = rng.choice(da_templates)
            text = tmpl.format(city=rng.choice(cities))
            channel = rng.choice(["video_call", "whatsapp", "sms"])
            sender = rng.choice(["POLICE_HQ", "CBI_CRIME", "CYBER_CELL", "+91" + phone1])
            is_scam = True
            category = "digital_arrest_impersonation"
            threat = "critical"
        elif cat_selector == 1:
            # APK sideload
            u_name, u_domain = rng.choice(utilities)
            tmpl = rng.choice(apk_templates)
            text = tmpl.format(
                utility=u_name,
                utility_domain=u_domain,
                amount=amount,
                vehicle=f"KA01MB{rand_val}",
                rand=rand_val,
                consignment=f"IN{rand_val}8890"
            )
            channel = "sms"
            sender = "+91" + phone1 if rng.random() > 0.4 else f"VM-{u_name[:6]}"
            is_scam = True
            category = "malicious_apk_sideload"
            threat = "critical"
        elif cat_selector == 2:
            # Disconnection urgency
            tmpl = rng.choice(disconnect_templates)
            text = tmpl.format(amount=amount, phone=phone1, phone2=phone2)
            channel = "sms"
            sender = "+91" + phone1
            is_scam = True
            category = "electricity_bill_urgency"
            threat = "high"
        elif cat_selector == 3:
            # Vishing & OTP
            tmpl = rng.choice(vishing_templates)
            text = tmpl.format()
            channel = rng.choice(["phone", "sms"])
            sender = rng.choice(["+91" + phone1, "VK-HDFCBK", "CP-SBIBNK"])
            is_scam = True
            category = "bank_vishing_otp"
            threat = "high"
        elif cat_selector == 4:
            # Adversarial
            tmpl = rng.choice(adversarial_templates)
            text = tmpl.format(rand=rand_val)
            channel = "sms"
            sender = "+91" + phone1
            is_scam = True
            category = "adversarial_evasion"
            threat = "critical"
        else:
            # Clean control
            tmpl = rng.choice(clean_templates)
            text = tmpl.format(
                amount=amount,
                otp=otp,
                order_id=f"404-{rand_val}912-10",
                pnr=f"425{rand_val}819",
                pin=f"{rng.randint(10, 99)}",
                time=datetime.now(timezone.utc).strftime("%H:%M")
            )
            channel = "sms"
            sender = rng.choice(["SBIINB", "SWIGGY", "IRCTC", "AMAZON", "AADHAR"])
            is_scam = False
            category = "legitimate_notice"
            threat = "safe"

        corpus.append({
            "sample_id": f"scam_sample_{i+1:04d}",
            "text": text,
            "channel": channel,
            "sender_header": sender,
            "is_scam": is_scam,
            "expected_category": category,
            "expected_threat_level": threat,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    return corpus


def generate_synthetic_qr_pass_corpus(
    count: int = 50,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generates a corpus of certified passes, official UIDAI Secure QR codes, and adversarial/tampered QR codes
    for testing the Universal Offline Pass Verifier.
    """
    rng = random.Random(seed) if seed is not None else random
    corpus = []
    
    purposes = ["hotel_checkin", "car_rental", "visitor_pass", "bank_account_opening", "sim_purchase"]
    recipients = ["Taj Palace Hotel", "Grand Hyatt Bengaluru", "Zoomcar Rentals", "HDFC Bank Branch", "Airtel Store"]

    for i in range(count):
        prof = generate_synthetic_resident_profile(seed=rng.randint(1, 1000000))
        variant = i % 5

        if variant == 0:
            # 1. Valid Suraksha Certified Pass
            valid_until = (datetime.now(timezone.utc) + timedelta(days=rng.randint(10, 365))).strftime("%Y-%m-%d")
            sig_hex = "".join(rng.choice("0123456789abcdef") for _ in range(64))
            pubkey_hex = "".join(rng.choice("0123456789abcdef") for _ in range(32))
            recipient = rng.choice(recipients)
            
            payload_dict = {
                "suraksha_certified": True,
                "version": "1.0",
                "claim": {
                    "holder": prof["full_name"],
                    "masked_id": prof["aadhaar_masked"],
                    "doc_type": "aadhaar",
                    "recipient": recipient,
                    "purpose": rng.choice(purposes),
                    "valid_until": valid_until,
                },
                "sig": sig_hex,
                "pubkey": pubkey_hex
            }
            raw_qr = json.dumps(payload_dict)
            expected_type = "suraksha_certified_pass"
            is_valid = True
            notes = "Valid offline Ed25519 signature."

        elif variant == 1:
            # 2. Valid UIDAI Secure QR code (simulated XML barcode)
            raw_qr = f'<PrintLetterBarcodeData uid="{prof["aadhaar_raw"]}" name="{prof["full_name"]}" gender="M" yob="1992" co="S/O Ram Sharma" house="12" loc="Surya Enclave" vtc="{prof["address"]["city"]}" dist="{prof["address"]["city"]}" state="{prof["address"]["state"]}" pc="{prof["address"]["pincode"]}"/>'
            expected_type = "uidai_secure_qr"
            is_valid = True
            notes = "Official UIDAI 2048-bit RSA Secure QR."

        elif variant == 2:
            # 3. Expired Pass
            past_date = (datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 30))).strftime("%Y-%m-%d")
            payload_dict = {
                "suraksha_certified": True,
                "claim": {
                    "holder": prof["full_name"],
                    "masked_id": prof["aadhaar_masked"],
                    "recipient": "Grand Hyatt Bengaluru",
                    "purpose": "hotel_checkin",
                    "valid_until": past_date,
                },
                "sig": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
                "pubkey": "abcdef0123456789abcdef0123456789"
            }
            raw_qr = json.dumps(payload_dict)
            expected_type = "suraksha_certified_pass"
            is_valid = False
            notes = "Pass expired in the past."

        elif variant == 3:
            # 4. Tampered Signature Pass
            payload_dict = {
                "suraksha_certified": True,
                "claim": {
                    "holder": prof["full_name"],
                    "masked_id": prof["aadhaar_masked"],
                    "recipient": "Zoomcar Rentals",
                    "purpose": "car_rental",
                    "valid_until": "2028-12-31",
                },
                "sig": "corrupt_short_sig",
                "pubkey": "short_pk"
            }
            raw_qr = json.dumps(payload_dict)
            expected_type = "suraksha_certified_pass"
            is_valid = False
            notes = "Tampered or corrupted Ed25519 signature."

        else:
            # 5. Non-pass random QR payload
            raw_qr = rng.choice([
                "https://example.com/wifi_connect?pass=12345678",
                "upi://pay?pa=merchant@upi&pn=GroceryStore&am=150.00",
                "WIFI:T:WPA;S:HomeWiFi;P:secretPass123;;",
                "PLAIN_TEXT_NOT_A_PASS_DATA"
            ])
            expected_type = "unrecognized_text"
            is_valid = False
            notes = "Unrecognized QR format."

        corpus.append({
            "pass_id": f"qr_sample_{i+1:04d}",
            "raw_payload": raw_qr,
            "expected_pass_type": expected_type,
            "expected_valid": is_valid,
            "holder_name": prof["full_name"] if is_valid else None,
            "notes": notes
        })

    return corpus


def generate_complete_test_fixture_bundle(
    num_profiles: int = 30,
    seed: int = 42
) -> Dict[str, Any]:
    """Generates an authoritative, deterministic bundle of synthetic fixtures for testing."""
    profiles = [generate_synthetic_resident_profile(seed=seed + i) for i in range(num_profiles)]
    breaches = [generate_synthetic_breach_dump(num_records=10, template_idx=i, seed=seed + 100 + i) for i in range(len(BREACH_TEMPLATES))]
    chats = generate_synthetic_whatsapp_conversations(num_threads=6, seed=seed + 200)
    scam_corpus = generate_synthetic_scam_corpus(count=60, seed=seed + 300)
    qr_passes = generate_synthetic_qr_pass_corpus(count=30, seed=seed + 400)

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator_version": "2.0.0",
            "seed": seed,
            "profile_count": len(profiles),
            "breach_catalog_count": len(breaches),
            "whatsapp_thread_count": len(chats),
            "scam_corpus_count": len(scam_corpus),
            "qr_pass_count": len(qr_passes),
            "compliance_note": "All data generated using synthetic generators and Verhoeff test ranges (9999...). Zero real resident PII."
        },
        "identities": profiles,
        "breach_catalog": breaches,
        "whatsapp_dlp_samples": chats,
        "scam_phishing_corpus": scam_corpus,
        "qr_pass_samples": qr_passes
    }


if __name__ == "__main__":
    print("[*] Generating sample synthetic identity with full multi-document suite...")
    sample = generate_synthetic_resident_profile(seed=42)
    print(json.dumps(sample, indent=2))
