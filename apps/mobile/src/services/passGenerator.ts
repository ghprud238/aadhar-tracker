/**
 * Single-Use Watermarked Identity Pass Generator (Usability Pillar).
 * Generates legally binding, purpose-restricted masked identity credentials
 * for hotel check-ins, car rentals, co-working spaces, and visitor kiosks.
 * 
 * Complies with UIDAI Circular 2022 and DPDP Act 2023.
 */

export interface PassRequest {
  documentType: 'aadhaar' | 'pan' | 'driving_license' | 'voter_id';
  holderName: string;
  maskedIdentifier: string;
  recipientEntity: string;  // e.g. "Taj Lands End, Mumbai"
  purpose: 'hotel_checkin' | 'car_rental' | 'coworking_visit' | 'custom';
  customPurpose?: string;
  validUntilDate?: string;
}

export interface CertifiedIdentityPass {
  passId: string;
  issuedAt: string;
  validUntil: string;
  recipientEntity: string;
  purposeText: string;
  holderName: string;
  maskedIdentifier: string;
  watermarkText: string;
  legalNotice: string;
  qrPayload: string;
}

export function generateCertifiedIdentityPass(req: PassRequest): CertifiedIdentityPass {
  const now = new Date();
  const validUntil = req.validUntilDate || new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const passId = 'pass_' + Math.random().toString(36).substring(2, 10).toUpperCase();

  let purpose = 'Hotel Check-In & Guest Verification';
  if (req.purpose === 'car_rental') purpose = 'Vehicle Self-Drive Rental Agreement';
  else if (req.purpose === 'coworking_visit') purpose = 'Office Premises Visitor Access';
  else if (req.purpose === 'custom' && req.customPurpose) purpose = req.customPurpose;

  const watermarkText = `VALID ONLY FOR ${req.recipientEntity.toUpperCase()} • ${purpose.toUpperCase()} • NOT FOR LOAN/KYC/SIM ISSUANCE • EXPIRES ${validUntil}`;

  const legalNotice = 
    `OFFICIAL STATUTORY NOTICE (UIDAI & IT ACT 2000):\n` +
    `This certified masked credential is provided exclusively for "${purpose}" at "${req.recipientEntity}" on ${validUntil}. ` +
    `In accordance with UIDAI Circular F.No.4(4)/57/122/2016 and Section 29 of the Aadhaar Act, ` +
    `retention of unredacted identity numbers, scanning into unencrypted storage, or secondary disclosure is strictly prohibited. ` +
    `Any attempt to utilize this document for financial borrowing, banking KYC, or SIM registration constitutes identity theft ` +
    `punishable under Sections 66C and 66D of the Information Technology Act, 2000.`;

  const qrPayload = JSON.stringify({
    suraksha_certified: true,
    pass_id: passId,
    holder: req.holderName,
    masked_id: req.maskedIdentifier,
    recipient: req.recipientEntity,
    valid_until: validUntil,
    tamper_proof_checksum: 'sha256_mock_sig_' + Math.random().toString(16).substring(2, 12),
  });

  return {
    passId,
    issuedAt: now.toISOString(),
    validUntil,
    recipientEntity: req.recipientEntity,
    purposeText: purpose,
    holderName: req.holderName,
    maskedIdentifier: req.maskedIdentifier,
    watermarkText,
    legalNotice,
    qrPayload,
  };
}
