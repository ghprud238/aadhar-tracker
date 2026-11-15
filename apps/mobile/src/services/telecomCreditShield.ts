/**
 * Telecom SIM (DoT Sanchar Saathi / TAFCOP) & Credit Impersonation Radar
 * 
 * Protects against:
 * 1. Ghost telecom SIM issuance using stolen Aadhaar/PAN photocopies.
 * 2. Unauthorized BNPL / personal loan inquiries on credit bureaus (CIBIL/Experian).
 * 3. Mobile handset theft reporting via Central Equipment Identity Register (CEIR).
 */

export interface SimConnectionInfo {
  id: string;
  mobileNumberMasked: string;
  telecomOperator: 'Jio' | 'Airtel' | 'Vodafone Idea' | 'BSNL';
  status: 'active_authorized' | 'unauthorized_ghost' | 'pending_verification';
  issuedDate: string;
  linkedDocument: 'aadhaar' | 'pan' | 'voter_id';
}

export interface CreditInquiryAlert {
  id: string;
  lenderName: string;
  inquiryType: 'personal_loan' | 'credit_card' | 'bnpl_paylater' | 'microfinance';
  inquiryDate: string;
  amountRequestedInr?: number;
  authorizedByCitizen: boolean;
  bureauReported: 'CIBIL' | 'Experian' | 'CRIF High Mark';
}

export class TelecomCreditShieldService {
  public static TAFCOP_PORTAL_URL = 'https://tafcop.sancharsaathi.gov.in/telecomUser/';
  public static CEIR_PORTAL_URL = 'https://www.ceir.gov.in/Home/index.jsp';
  public static RBI_OMBUDSMAN_URL = 'https://cms.rbi.org.in/';

  /**
   * Retrieves active SIM connections registered against the citizen's identity documents.
   */
  public static getMonitoredSimConnections(): SimConnectionInfo[] {
    return [
      {
        id: 'sim_01',
        mobileNumberMasked: '+91 98*** **210',
        telecomOperator: 'Airtel',
        status: 'active_authorized',
        issuedDate: '2021-04-12',
        linkedDocument: 'aadhaar',
      },
      {
        id: 'sim_02',
        mobileNumberMasked: '+91 91*** **849',
        telecomOperator: 'Jio',
        status: 'active_authorized',
        issuedDate: '2023-08-20',
        linkedDocument: 'aadhaar',
      },
      {
        id: 'sim_ghost_03',
        mobileNumberMasked: '+91 88*** **491',
        telecomOperator: 'Vodafone Idea',
        status: 'unauthorized_ghost',
        issuedDate: '2026-10-04',
        linkedDocument: 'voter_id',
      },
    ];
  }

  /**
   * Retrieves credit inquiries across CIBIL, Experian, and CRIF High Mark on citizen's PAN.
   */
  public static getCreditInquiries(): CreditInquiryAlert[] {
    return [
      {
        id: 'inq_01',
        lenderName: 'HDFC Bank Ltd',
        inquiryType: 'credit_card',
        inquiryDate: '2026-02-15',
        authorizedByCitizen: true,
        bureauReported: 'CIBIL',
      },
      {
        id: 'inq_fraud_02',
        lenderName: 'QuickCash Instant FinTech NBFC',
        inquiryType: 'personal_loan',
        inquiryDate: '2026-11-02',
        amountRequestedInr: 45000,
        authorizedByCitizen: false,
        bureauReported: 'Experian',
      },
    ];
  }

  /**
   * Generates a formal RBI Ombudsman & CIBIL dispute letter regarding an unauthorized loan inquiry.
   */
  public static generateLoanDisputeLetter(inquiry: CreditInquiryAlert, victimName: string, panMasked: string): string {
    return (
`TO:
The Nodal Officer / Grievance Redressal Officer, ${inquiry.lenderName} &
The Banking Ombudsman (Reserve Bank of India - cms.rbi.org.in)

SUBJECT: FORMAL DISPUTE REGARDING FRAUDULENT CREDIT INQUIRY ON PAN ${panMasked}

Respected Sir / Madam,

I am writing to register an urgent grievance against an unauthorized credit inquiry logged on my credit report:

1. Institution: ${inquiry.lenderName}
2. Bureau: ${inquiry.bureauReported}
3. Date of Inquiry: ${inquiry.inquiryDate}
4. Product Type: ${inquiry.inquiryType.toUpperCase()} ${inquiry.amountRequestedInr ? `(₹${inquiry.amountRequestedInr.toLocaleString('en-IN')})` : ''}

I solemnly declare that I have NEVER applied for any credit facility, loan, or BNPL service with ${inquiry.lenderName}.
My identity documents have been impersonated without my consent in violation of RBI Master Directions on KYC and the DPDP Act 2023.

I hereby demand:
1. Immediate cancellation of any pending application or loan account opened under my PAN.
2. Written confirmation that this inquiry will be expunged from all credit bureaus (CIBIL / Experian / CRIF).
3. The IP address, device telemetry, and KYC documents submitted by the fraudster for cybercrime reporting.

Sincerely,
${victimName}
Date: ${new Date().toLocaleDateString('en-IN')}`
    );
  }
}
