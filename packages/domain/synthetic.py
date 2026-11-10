"""
Synthetic data generator for Indian Identity Protection Platform (Suraksha).
Generates mathematically valid, privacy-safe synthetic test identities (Aadhaar, PAN, VID),
simulated dark-web breach catalog dumps, infostealer malware archives, and DLP chat threads.
"""
import random
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

from packages.domain.verhoeff import (
    generate_verhoeff_checksum,
    validate_aadhaar,
    validate_pan,
    validate_verhoeff,
)


FIRST_NAMES = [
    "Aarav", "Diya", "Rohan", "Pooja", "Karthik", "Ananya", "Vikram", "Sneha",
    "Arjun", "Priya", "Rajesh", "Meera", "Siddharth", "Ishaan", "Kavya", "Aditya",
    "Tanvi", "Nikhil", "Ritu", "Amit", "Deepa", "Suresh", "Lakshmi", "Varun", "Sunita"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Iyer", "Reddy", "Gupta", "Mukherjee", "Nair",
    "Kulkarni", "Singh", "Das", "Menon", "Joshi", "Bose", "Choudhury", "Pillai",
    "Rao", "Agarwal", "Bhat", "Deshmukh", "Ghosh", "Chatterjee", "Pandey", "Mehta"
]

CITIES_AND_STATES = [
    ("Mumbai", "Maharashtra", "400001"),
    ("Bengaluru", "Karnataka", "560001"),
    ("New Delhi", "Delhi", "110001"),
    ("Hyderabad", "Telangana", "500001"),
    ("Chennai", "Tamil Nadu", "600001"),
    ("Kolkata", "West Bengal", "700001"),
    ("Pune", "Maharashtra", "411001"),
    ("Ahmedabad", "Gujarat", "380001"),
    ("Jaipur", "Rajasthan", "302001"),
    ("Kochi", "Kerala", "682001"),
    ("Lucknow", "Uttar Pradesh", "226001"),
    ("Chandigarh", "Punjab", "160001"),
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
    
    # Prefix can be 4 digits (e.g. '9999', '2345') or custom
    clean_prefix = "".join(filter(str.isdigit, prefix_range))
    if not clean_prefix or clean_prefix[0] in ("0", "1"):
        clean_prefix = "9999"

    # Need 11 digits total before generating check digit
    needed_random = 11 - len(clean_prefix)
    if needed_random > 0:
        middle_digits = "".join(str(rng.randint(0, 9)) for _ in range(needed_random))
    else:
        middle_digits = ""
    
    prefix_11 = (clean_prefix + middle_digits)[:11]
    
    # Calculate Verhoeff check digit
    check_digit = generate_verhoeff_checksum(prefix_11)
    full_aadhaar = prefix_11 + check_digit

    # Assert invariant: must be valid
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


def generate_synthetic_resident_profile(
    seed: Optional[int] = None,
    custom_name: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a complete synthetic Indian resident identity profile for testing."""
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
    
    city, state, pin_prefix = rng.choice(CITIES_AND_STATES)
    pincode = f"{pin_prefix[:3]}{rng.randint(100, 999):03d}"
    
    # Generate valid synthetic Aadhaar and PAN
    aadhaar_raw = generate_synthetic_aadhaar(formatted=False, seed=rng.randint(1, 100000))
    aadhaar_formatted = f"{aadhaar_raw[:4]} {aadhaar_raw[4:8]} {aadhaar_raw[8:]}"
    aadhaar_masked = f"XXXX-XXXX-{aadhaar_raw[-4:]}"
    
    pan = generate_synthetic_pan(last_name=last_name, entity_type="P", seed=rng.randint(1, 100000))
    pan_masked = f"{pan[:2]}***{pan[5:7]}*{pan[-1]}"
    
    vid = generate_synthetic_vid(seed=rng.randint(1, 100000))

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
        "address": {
            "street": f"Flat {rng.randint(101, 909)}, Surya Enclave",
            "city": city,
            "state": state,
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
            "state": prof["address"]["state"],
            "pincode": prof["address"]["pincode"],
        }
        
        # Add password hash for stealer logs or account breaches
        if "password_hash" in template["compromised_data_classes"]:
            record["password_hash"] = f"$2b$12${''.join(rng.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./') for _ in range(53))}"
            record["plaintext_password_redacted"] = "[REDACTED_BY_CTI_POLICY]"
            
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
        "total_records_in_dump": num_records * 4000,  # Simulated overall breach size
        "sampled_records": records,
        "dump_discovered_at": datetime.now(timezone.utc).isoformat(),
        "magnet_hash": f"urn:btih:{''.join(rng.choice('0123456789abcdef') for _ in range(40))}",
        "raw_evidence_sha256": f"{''.join(rng.choice('0123456789abcdef') for _ in range(64))}"
    }


def generate_synthetic_whatsapp_conversations(
    num_threads: int = 5,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generates realistic synthetic WhatsApp message threads with embedded unmasked Aadhaar
    and PAN numbers for testing the Data Loss Prevention (DLP) scanner and webhook handler.
    """
    rng = random.Random(seed) if seed is not None else random
    
    threads = []
    scenarios = [
        ("HR Onboarding Verification", "office_hr", True),
        ("Hotel Room Booking KYC Proof", "hotel_agent", True),
        ("Personal Loan Executive Chat", "loan_rep", True),
        ("Family Vacation Flight Details", "family_group", False),
        ("Society Maintenance Discussion", "apartment_rwa", False),
    ]

    for i in range(num_threads):
        scenario_title, channel_tag, contains_sensitive_id = scenarios[i % len(scenarios)]
        prof = generate_synthetic_resident_profile(seed=rng.randint(1, 10000000))
        sender_phone = prof["phone"]
        
        messages = []
        if contains_sensitive_id:
            # Thread with unmasked sensitive identifier
            if i % 2 == 0:
                messages = [
                    {"from": "recipient", "text": "Hi, please share your ID proof and PAN card so we can finalize the registration."},
                    {"from": "sender", "text": f"Sure, sending here. My Aadhaar number is {prof['aadhaar_formatted']} and PAN is {prof['pan_raw']}. Please verify."},
                    {"from": "recipient", "text": "Received, thank you!"}
                ]
            else:
                messages = [
                    {"from": "recipient", "text": "Sir, room booking requires government ID proof copy."},
                    {"from": "sender", "text": f"Here is my Aadhaar card details: {prof['aadhaar_formatted']} (Name: {prof['full_name']})"},
                    {"from": "recipient", "text": "Noted. Your booking is confirmed."}
                ]
        else:
            # Clean thread without unmasked sensitive identifier
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


def generate_complete_test_fixture_bundle(
    num_profiles: int = 20,
    seed: int = 42
) -> Dict[str, Any]:
    """Generates an authoritative, deterministic bundle of synthetic fixtures for testing."""
    profiles = [generate_synthetic_resident_profile(seed=seed + i) for i in range(num_profiles)]
    breaches = [generate_synthetic_breach_dump(num_records=10, template_idx=i, seed=seed + 100 + i) for i in range(len(BREACH_TEMPLATES))]
    chats = generate_synthetic_whatsapp_conversations(num_threads=6, seed=seed + 200)

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator_version": "1.0.0",
            "seed": seed,
            "profile_count": len(profiles),
            "breach_catalog_count": len(breaches),
            "whatsapp_thread_count": len(chats),
            "compliance_note": "All data generated using synthetic generators and Verhoeff test ranges (9999...). Zero real resident PII."
        },
        "identities": profiles,
        "breach_catalog": breaches,
        "whatsapp_dlp_samples": chats
    }
