/**
 * National Cybercrime Emergency Toolkit & Legal Complaint Generator.
 * Provides instant 1-tap statutory reporting assistance for Indian citizens:
 * 1. Pre-formatted complaint for cybercrime.gov.in (National Cyber Crime Reporting Portal).
 * 2. IT Act Section 66C (Identity Theft) & 66D (Cheating by Personation) FIR draughting.
 * 3. 1930 Emergency Helpline integration.
 */

export interface CybercrimeComplaintRequest {
  victimName: string;
  victimPhone: string;
  victimEmail: string;
  maskedIdentifier: string;
  incidentType: 'aeps_biometric_fraud' | 'darkweb_leak' | 'sim_swap' | 'unauthorized_loan';
  breachSourceOrEntity?: string;
  approximateDate: string;
  financialLossInr?: number;
  suspectDetails?: string;
}

export interface CybercrimeComplaintDossier {
  helplinePhone: string;
  officialPortalUrl: string;
  complaintSubject: string;
  formalComplaintBody: string;
  statutoryClauses: string[];
  immediateChecklist: string[];
}

export function generateCybercrimeComplaint(req: CybercrimeComplaintRequest): CybercrimeComplaintDossier {
  const lossText = req.financialLossInr && req.financialLossInr > 0
    ? `Financial Loss Incurred: ₹${req.financialLossInr.toLocaleString('en-IN')}`
    : 'Financial Loss: Potential identity compromise / preventative registration';

  const clauses = [
    'Section 66C, Information Technology Act 2000 (Identity Theft & Fraudulent Use of Electronic Signature / Password)',
    'Section 66D, Information Technology Act 2000 (Cheating by Personation using Computer Resource)',
    'Section 43, Aadhaar Act 2016 (Penalty for unauthorized access to Central Identities Data Repository)',
    'Section 318 & 319, Bharatiya Nyaya Sanhita 2023 (Cheating & Cheating by Personation)',
  ];

  let incidentDesc = 'unauthorized disclosure and potential fraudulent use of government identity credentials';
  if (req.incidentType === 'aeps_biometric_fraud') {
    incidentDesc = 'unauthorized AePS (Aadhaar-enabled Payment System) biometric debit without citizen consent';
  } else if (req.incidentType === 'sim_swap') {
    incidentDesc = 'fraudulent telecom SIM issuance using forged identity documents';
  } else if (req.incidentType === 'unauthorized_loan') {
    incidentDesc = 'fraudulent instant personal loan application processed using forged identity records';
  }

  const formalComplaintBody =
`TO:
The Station House Officer (SHO) / Cyber Crime Police Station &
The National Cyber Crime Reporting Portal (MHA, Govt of India)
Portal: https://cybercrime.gov.in | Helpline: 1930

SUBJECT: FORMAL COMPLAINT UNDER SECTION 66C & 66D OF THE IT ACT, 2000 REGARDING ${incidentDesc.toUpperCase()}

Respected Sir / Madam,

I, ${req.victimName}, residing in India, wish to report a cybercrime incident involving ${incidentDesc}.

1. VICTIM DETAILS:
• Full Name: ${req.victimName}
• Registered Mobile: ${req.victimPhone}
• Email: ${req.victimEmail}
• Compromised Identity Credential: ${req.maskedIdentifier}

2. INCIDENT DETAILS:
• Date / Timeline of Discovery: ${req.approximateDate}
• Source / Disclosing Entity: ${req.breachSourceOrEntity || 'Dark Web Leak / Messaging Disclosure'}
• ${lossText}
• Known Suspect Details: ${req.suspectDetails || 'Unknown online perpetrators / malicious third-party actors'}

3. STATUTORY VIOLATIONS:
The accused parties have committed cognizable offences under:
${clauses.map((c) => `• ${c}`).join('\n')}

4. PRAYER / RELIEF SOUGHT:
I humbly request the Cyber Crime Investigation Division to:
a) Register an FIR under the aforementioned sections of law.
b) Issue freeze instructions to financial payment gateways / banks to prevent fraudulent withdrawals.
c) Direct UIDAI / telecom providers to audit recent authentication requests associated with this identity.

I declare that the information provided above is true to the best of my knowledge and belief.

Sincerely,
${req.victimName}
Date: ${new Date().toLocaleDateString('en-IN')}`;

  const immediateChecklist = [
    'Dial 1930 immediately if any money has been deducted from your bank accounts.',
    'Visit https://myaadhaar.uidai.gov.in and turn on Biometric Lock right away.',
    'Submit this formal complaint draft at https://cybercrime.gov.in under "Report Cyber Crime".',
    'Email your bank\'s Grievance Officer and the RBI Banking Ombudsman with your complaint copy.',
    'Check your CIBIL / Experian credit report to verify no unauthorized loans were opened.',
  ];

  return {
    helplinePhone: '1930',
    officialPortalUrl: 'https://cybercrime.gov.in',
    complaintSubject: `Formal Complaint: Identity Theft & Fraud (${req.maskedIdentifier})`,
    formalComplaintBody,
    statutoryClauses: clauses,
    immediateChecklist,
  };
}
