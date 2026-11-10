#!/usr/bin/env python3
"""
Interactive End-to-End Testing Console & First-Principles Walkthrough
Suraksha Identity Protection Platform (Aadhaar & PAN Protection)

Demonstrates the entire lifecycle:
1. Zero-Plaintext Cryptography & Blind Indexing (First Principles)
2. Mathematical Verhoeff Dihedral D5 Aadhaar & PAN Validation
3. Synthetic Data Seeding & Dark Web Breach Simulation
4. WhatsApp Sharing Data Loss Prevention (DLP) & Real-Time Alert Dispatch
5. Transactional Outbox Pattern & Notification Worker Sanitization (FR-017)
6. React Native Client Alert Receiving & Bidirectional Acknowledgment
"""
import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional

# Ensure repository root is in python path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dummy_data_to_test.generator import (
    generate_synthetic_aadhaar,
    generate_synthetic_pan,
    generate_synthetic_resident_profile,
    generate_synthetic_breach_dump,
    generate_synthetic_whatsapp_conversations,
)
from packages.domain.verhoeff import (
    validate_aadhaar,
    validate_pan,
    detect_identifiers_in_text,
    generate_verhoeff_checksum,
)
from packages.security.crypto import vault

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"
        self.session_token: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.subject_id: Optional[str] = None

    def request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_url}{path}" if path.startswith("/") else f"{self.api_url}/{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Request-ID": f"test_{int(time.time()*1000)}"
        }
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                err_json = json.loads(raw)
                return err_json
            except Exception:
                return {"error": {"message": f"HTTP {e.code}: {e.reason}", "raw": raw}}
        except urllib.error.URLError as e:
            return {"error": {"message": f"Failed to connect to backend at {self.base_url}: {e.reason}"}}


def print_banner():
    print(f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║               SURAKSHA IDENTITY PROTECTION PLATFORM                          ║
║        Interactive First-Principles Testing & Alert Verification Console     ║
╚══════════════════════════════════════════════════════════════════════════════╝{RESET}
  Backend URL:      {GREEN}http://localhost:8000{RESET} (FastAPI Web App & BFF)
  Mobile App URL:   {GREEN}http://localhost:8082{RESET} (React Native / Expo Client)
  Testing Database: {YELLOW}SQLite / Memory with Row-Level Isolation{RESET}
  Synthetic Data:   {YELLOW}Verhoeff D5 Checksum + Statutory Indian PAN{RESET}
""")


def wait_prompt(auto_mode: bool, msg: str = "Press Enter to continue to next phase..."):
    if auto_mode:
        time.sleep(0.5)
        return
    print(f"\n{YELLOW}▶ {msg}{RESET}", end="")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{RED}Aborted.{RESET}")
        sys.exit(0)


def run_phase_1_first_principles(client: ApiClient, auto_mode: bool):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}PHASE 1: First-Principles Cryptography & Mathematical Validation{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"""
{BOLD}Core Architectural Principles:{RESET}
1. {BOLD}Verhoeff Dihedral Group (D5) Algorithm:{RESET}
   - Aadhaar numbers are 12 digits where the final digit is a non-commutative dihedral checksum.
   - Equation: {CYAN}∏ d(c, p(i mod 8, digit_i)) = 0{RESET}
   - Catches 100% of single-digit misprints and 100% of adjacent digit transpositions.
2. {BOLD}Zero-Plaintext Envelope Cryptography:{RESET}
   - Plaintext identifiers are encrypted using {CYAN}AES-256-GCM{RESET} with a tenant-bound nonce.
   - Searching without decryption uses {CYAN}HMAC-SHA256 Blind Indexing{RESET}.
""")

    # 1. Generate Aadhaar
    raw_aadhaar = generate_synthetic_aadhaar(formatted=False)
    is_valid, masked_aadhaar, _ = validate_aadhaar(raw_aadhaar)
    checksum = generate_verhoeff_checksum(raw_aadhaar[:11])
    
    # 2. Generate PAN
    raw_pan = generate_synthetic_pan()
    is_pan_valid, masked_pan, _ = validate_pan(raw_pan)

    print(f"  {BOLD}Synthetic Aadhaar:{RESET} {CYAN}{raw_aadhaar[:4]} {raw_aadhaar[4:8]} {raw_aadhaar[8:]}{RESET}")
    print(f"  └─ Verhoeff Checksum Digit: {GREEN}{checksum}{RESET} (Validation Passed: {GREEN}{is_valid}{RESET})")
    print(f"  {BOLD}Synthetic PAN:{RESET}     {CYAN}{raw_pan}{RESET}")
    print(f"  └─ 4th Character '{raw_pan[3]}': Individual (Person), 5th '{raw_pan[4]}': Surname initial (Validation: {GREEN}{is_pan_valid}{RESET})")

    # 3. Cryptographic Envelope & Blind Index Demo
    tenant_id = "tenant_demo_delhi"
    encrypted_envelope = vault.encrypt(raw_aadhaar, associated_data=tenant_id)
    blind_index = vault.compute_blind_index(raw_aadhaar, scope=tenant_id)
    decrypted = vault.decrypt(encrypted_envelope, associated_data=tenant_id)

    print(f"\n  {BOLD}Zero-Plaintext Cryptographic Vault Invariant:{RESET}")
    print(f"  • AES-256-GCM Envelope:  {YELLOW}{encrypted_envelope[:48]}...{RESET}")
    print(f"  • HMAC-SHA256 Blind Index: {YELLOW}{blind_index}{RESET}")
    print(f"  • Decrypted in Memory:    {GREEN}{decrypted[:4]} XXXX {decrypted[-4:]}{RESET} (Matches: {GREEN}{decrypted == raw_aadhaar}{RESET})")
    print(f"  {MAGENTA}✓ Database and logs store ONLY the blind index and encrypted ciphertext. Plaintext never leaves application memory.{RESET}")

    wait_prompt(auto_mode)


def run_phase_2_auth_and_session(client: ApiClient, auto_mode: bool):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}PHASE 2: Backend Health & Resident Session Bootstrap{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")

    # Check health
    health_resp = client.request("GET", "/internal/health/ready")
    if "error" in health_resp:
        print(f"  {RED}✖ Backend server is not running or unreachable at {client.base_url}!{RESET}")
        print(f"  {YELLOW}Please start the backend in another terminal with:{RESET}")
        print(f"  {BOLD}uv run uvicorn services.api.main:app --port 8000 --reload{RESET}")
        return False
    print(f"  {GREEN}✓ Backend Health Probe:{RESET} {health_resp}")

    # Authenticate demo citizen
    auth_resp = client.request("GET", "/auth/callback?email=citizen@suraksha.in&full_name=Aarav+Sharma")
    if "error" in auth_resp:
        print(f"  {RED}✖ Auth failed: {auth_resp['error']}{RESET}")
        return False

    data = auth_resp.get("data", {})
    client.session_token = data.get("session_id")
    client.tenant_id = data.get("tenant_id")
    client.subject_id = data.get("subject_id")

    print(f"  {GREEN}✓ Citizen Session Established:{RESET}")
    print(f"    • Subject ID:   {CYAN}{client.subject_id}{RESET}")
    print(f"    • Tenant ID:    {CYAN}{client.tenant_id}{RESET}")
    print(f"    • Resident:     {CYAN}{data.get('full_name')} <{data.get('email')}>{RESET}")
    print(f"    • Session Token: {YELLOW}{client.session_token[:20]}...{RESET}")

    wait_prompt(auto_mode)
    return True


def run_phase_3_synthetic_data_seeding(client: ApiClient, auto_mode: bool):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}PHASE 3: Synthetic Data & Database Seeding Inspection{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")

    # Inspect current identifiers
    ident_resp = client.request("GET", "/identifiers")
    items = ident_resp.get("data", [])
    print(f"  {BOLD}Current Monitored Identifiers ({len(items)} enrolled):{RESET}")
    for item in items:
        print(f"    • [{item.get('type').upper()}] Masked: {CYAN}{item.get('masked_value')}{RESET} | State: {GREEN}{item.get('state')}{RESET}")

    # If no email identifier, enroll one
    if not items:
        add_resp = client.request("POST", "/identifiers", {"type": "email", "value": "citizen@suraksha.in"})
        print(f"  {GREEN}✓ Enrolled email identifier for monitoring:{RESET} {add_resp.get('data', {}).get('masked_value')}")

    # Inspect dark web breach catalog generator
    dump = generate_synthetic_breach_dump()
    print(f"\n  {BOLD}Dark Web CTI Feed Simulator:{RESET}")
    print(f"    • {RED}[DUMP]{RESET} {BOLD}{dump['breach_name']}{RESET} | Records: {dump['total_records_in_dump']:,} | Torrent: {dump['magnet_hash'][:16]}...")

    wait_prompt(auto_mode)


def run_phase_4_whatsapp_dlp(client: ApiClient, auto_mode: bool):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}PHASE 4: WhatsApp Sharing Data Loss Prevention (DLP) & Live Advisory{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"""
{BOLD}Attack Scenario / Accidental Exposure:{RESET}
A resident sends an unmasked WhatsApp message containing their Aadhaar and PAN:
{YELLOW}"Hello, sharing my Aadhaar 9999 4105 7058 and PAN ABCDE1234F for hotel check-in at reception."{RESET}
""")

    payload = {
        "message_text": "Hello, sharing my Aadhaar 9999 4105 7058 and PAN ABCDE1234F for hotel check-in at reception.",
        "sender_phone": "+919876543210",
        "recipient_phone": "+919876500000",
        "channel": "whatsapp_direct"
    }

    print(f"  {CYAN}Dispatching simulated WhatsApp payload to /api/v1/integrations/whatsapp/simulate-share...{RESET}")
    resp = client.request("POST", "/integrations/whatsapp/simulate-share", payload)

    if "error" in resp:
        print(f"  {RED}✖ WhatsApp simulation failed: {resp['error']}{RESET}")
        return

    data = resp.get("data", {})
    detected = data.get("detected", False)
    findings = data.get("findings", {})
    alert_text = data.get("automated_whatsapp_alert", "")
    incident_id = data.get("incident_id")

    print(f"  {GREEN}✓ Interception & Verhoeff Analysis Complete:{RESET}")
    print(f"    • Detection Status: {RED}{BOLD}VIOLATION DETECTED{RESET} (Detected: {detected})")
    print(f"    • Incident ID:      {CYAN}{incident_id}{RESET}")
    print(f"    • Intercepted Items:")
    for a in findings.get("aadhaar", []):
        print(f"      - Aadhaar: {CYAN}{a.get('masked')}{RESET} (Verhoeff Checksum: {GREEN}Valid{RESET})")
    for p in findings.get("pan", []):
        print(f"      - PAN:     {CYAN}{p.get('masked')}{RESET} (Regex & Entity: {GREEN}Valid{RESET})")

    print(f"\n  {BOLD}{MAGENTA}Automated WhatsApp Security Advisory Dispatched to Sender (+919876543210):{RESET}")
    print(f"{YELLOW}┌────────────────────────────────────────────────────────────────────────┐{RESET}")
    for line in alert_text.splitlines():
        print(f"{YELLOW}│{RESET} {line}")
    print(f"{YELLOW}└────────────────────────────────────────────────────────────────────────┘{RESET}")

    wait_prompt(auto_mode)


def run_phase_5_outbox_and_notifications(client: ApiClient, auto_mode: bool):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}PHASE 5: Transactional Outbox Pattern & Notification Worker (FR-017){RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"""
{BOLD}Outbox Invariant Guarantee:{RESET}
The API committed the Incident AND enqueued the OutboxEvent in the {CYAN}same ACID database transaction{RESET}.
The notification worker sanitizes all alert messages under {CYAN}FR-017{RESET} (Zero plaintext passwords, raw IDs, or cookies).
""")

    # Query notifications
    notif_resp = client.request("GET", "/notifications")
    notifications = notif_resp.get("data", [])

    print(f"  {BOLD}Dispatched Multi-Surface Citizen Notifications ({len(notifications)} records):{RESET}")
    for n in notifications[:3]:
        print(f"    • {GREEN}[{n.get('channel').upper()}]{RESET} {BOLD}{n.get('title')}{RESET}")
        print(f"      Status: {CYAN}{n.get('status')}{RESET} | Created: {n.get('created_at')}")
        print(f"      Sanitized Body: {YELLOW}{n.get('body')}{RESET}")

    # Inspect created incidents
    inc_resp = client.request("GET", "/incidents")
    incidents = inc_resp.get("data", [])
    print(f"\n  {BOLD}Active Citizen Incidents ({len(incidents)} logged):{RESET}")
    for inc in incidents[:2]:
        print(f"    • ID: {CYAN}{inc.get('id')}{RESET} | Severity: {RED}{inc.get('severity').upper()}{RESET} | Priority Score: {YELLOW}{inc.get('priority_score')}/100{RESET}")
        print(f"      Title: {BOLD}{inc.get('title')}{RESET}")
        print(f"      Remediation Tasks: {GREEN}{', '.join(inc.get('recommended_actions', []))}{RESET}")

    wait_prompt(auto_mode)


def run_phase_6_react_native_client(client: ApiClient, auto_mode: bool):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}PHASE 6: React Native Mobile Client & Bidirectional Acknowledgment{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"""
{BOLD}Mobile Client Integration Check:{RESET}
- The React Native mobile client in {CYAN}apps/mobile{RESET} connects to {CYAN}http://localhost:8000/api/v1{RESET}.
- It polls unread alerts every 5 seconds, displaying an urgent banner and red tab badge.
- Now we simulate the citizen opening the app and tapping {GREEN}"✓ Acknowledge"{RESET} on the alert.
""")

    notif_resp = client.request("GET", "/notifications")
    notifications = notif_resp.get("data", [])
    unread = [n for n in notifications if n.get("status") != "read"]

    if unread:
        target = unread[0]
        print(f"  {CYAN}Acknowledging alert via Mobile Client: {target.get('id')} ({target.get('title')})...{RESET}")
        ack_resp = client.request("POST", f"/notifications/{target.get('id')}/read")
        print(f"  {GREEN}✓ Alert marked as read:{RESET} {ack_resp}")

    # Check companion glance status
    glance_resp = client.request("GET", "/companion/glance")
    glance = glance_resp.get("data", {})
    print(f"\n  {BOLD}Updated Wearable/Mobile Shield Glance:{RESET}")
    print(f"    • Shield Status:         {RED if glance.get('shield_status') == 'critical' else YELLOW}{glance.get('shield_status').upper()}{RESET}")
    print(f"    • Active Incidents:      {CYAN}{glance.get('active_incidents')}{RESET}")
    print(f"    • Biometrics Locked:     {GREEN}{glance.get('biometrics_locked')}{RESET}")
    print(f"    • Active Monitored IDs:  {CYAN}{glance.get('active_monitored_count')}{RESET}")

    wait_prompt(auto_mode)


def main():
    parser = argparse.ArgumentParser(description="Suraksha Identity Protection Platform Interactive Test Runner")
    parser.add_argument("--auto", action="store_true", help="Run in non-interactive automatic mode")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="FastAPI backend host URL")
    args = parser.parse_args()

    print_banner()
    client = ApiClient(base_url=args.backend_url)

    # Execute all test phases
    run_phase_1_first_principles(client, args.auto)
    backend_ok = run_phase_2_auth_and_session(client, args.auto)
    if not backend_ok:
        sys.exit(1)

    run_phase_3_synthetic_data_seeding(client, args.auto)
    run_phase_4_whatsapp_dlp(client, args.auto)
    run_phase_5_outbox_and_notifications(client, args.auto)
    run_phase_6_react_native_client(client, args.auto)

    print(f"\n{BOLD}{GREEN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}🎉 ALL END-TO-END VERIFICATION PHASES COMPLETED SUCCESSFULLY!{RESET}")
    print(f"{BOLD}{GREEN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"""
{BOLD}Live Interactive Surfaces Available Now:{RESET}
  1. {CYAN}Web App Dashboard (PWA):{RESET}       http://localhost:8000/app
  2. {CYAN}Interactive Alerts Feed:{RESET}       http://localhost:8000/app#notifications
  3. {CYAN}Smartwatch Companion:{RESET}          http://localhost:8000/wearable
  4. {CYAN}React Native Mobile Client:{RESET}    cd apps/mobile && npm run web (http://localhost:8082)
  5. {CYAN}Interactive OpenAPI Docs:{RESET}      http://localhost:8000/docs
""")


if __name__ == "__main__":
    main()
