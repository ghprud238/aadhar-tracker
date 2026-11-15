/**
 * SurakshaShield B2B Developer SDK
 * 
 * Standalone client-side and server-side TypeScript toolkit for Indian digital identity
 * protection, zero-leak verification, and compliance with UIDAI circulars & DPDP Act 2023.
 * 
 * Used by hotels, car rentals, co-working spaces, fintechs, and visitor kiosks to:
 * 1. Validate government credentials on-device without cloud transmission.
 * 2. Redact and mask raw identity numbers before any image or text is persisted.
 * 3. Generate purpose-bound watermarked credentials that legally prevent loan/SIM reuse fraud.
 * 4. Generate 16-digit UIDAI Virtual IDs (VID).
 * 5. Generate statutory legal FIR drafts under IT Act 66C/66D and 1930 helpline dossiers.
 */

import {
  validateAadhaar,
  validatePan,
  validateDrivingLicense,
  validateVoterId,
  validatePassport,
  detectIdentifiersInText,
  ValidationResult,
  DocumentType,
  DetectedIdentifier,
} from './verhoeff';

import {
  generateCertifiedIdentityPass,
  verifyCertifiedIdentityPass,
  PassRequest,
  CertifiedIdentityPass,
} from './passGenerator';

import {
  generateCybercrimeComplaint,
  CybercrimeComplaintRequest,
  CybercrimeComplaintDossier,
} from './cybercrimeToolkit';

import { localEngine } from './localEngine';
import { antiTamperShield, DeviceIntegrityReport } from './antiTamperShield';
import { HomoglyphSanitizer } from './homoglyphSanitizer';
import { ThreatFeedEngine, KAnonymityCheckResult } from './bloomFilter';
import { BackupRecoveryEngine, VaultBackupData, EncryptedBackupPackage } from './backupRecovery';

export interface ShieldSdkConfig {
  organizationName?: string;
  environment?: 'production' | 'sandbox';
  enforceVerhoeff?: boolean;
}

export class SurakshaShield {
  private config: ShieldSdkConfig;

  constructor(config: ShieldSdkConfig = {}) {
    this.config = {
      organizationName: 'Default Organization',
      environment: 'production',
      enforceVerhoeff: true,
      ...config,
    };
  }

  /**
   * Mathematically validates a 12-digit Indian Aadhaar number using the Verhoeff D5 algorithm.
   * Ensures the number is non-zero/non-one prefixed and returns a masked token (XXXX-XXXX-1234).
   */
  public static validateAadhaar(rawInput: string): ValidationResult {
    return validateAadhaar(rawInput);
  }

  /**
   * Validates an Indian Permanent Account Number (PAN) according to the Income Tax Department format.
   * Returns a masked PAN token (AB***12*4F).
   */
  public static validatePan(rawInput: string): ValidationResult {
    return validatePan(rawInput);
  }

  /**
   * Validates an Indian Driving License (Parivahan schema).
   * Format: State (2) + RTO (2) + Year (4) + Digits (7).
   */
  public static validateDrivingLicense(rawInput: string): ValidationResult {
    return validateDrivingLicense(rawInput);
  }

  /**
   * Validates an Indian Voter ID (EPIC - Electors Photo Identity Card).
   * Format: 3 uppercase letters followed by 7 digits.
   */
  public static validateVoterId(rawInput: string): ValidationResult {
    return validateVoterId(rawInput);
  }

  /**
   * Validates an Indian Passport Number.
   * Format: 1 uppercase letter followed by 7 digits.
   */
  public static validatePassport(rawInput: string): ValidationResult {
    return validatePassport(rawInput);
  }

  /**
   * Scans unstructured text (chat, emails, OCR outputs, form inputs) to detect and flag
   * unmasked Aadhaar, PAN, Driving License, Voter ID, or Passport strings (Data Loss Prevention).
   */
  public static detectIdentifiersInText(text: string): {
    aadhaar: DetectedIdentifier[];
    pan: DetectedIdentifier[];
    driving_license: DetectedIdentifier[];
    voter_id: DetectedIdentifier[];
    passport: DetectedIdentifier[];
  } {
    return detectIdentifiersInText(text);
  }

  /**
   * Generates a single-use certified masked identity pass with indelible purpose watermark
   * and tamper-evident QR code checksum.
   */
  public static generateCertifiedIdentityPass(req: PassRequest): CertifiedIdentityPass {
    return generateCertifiedIdentityPass(req);
  }

  /**
   * Generates a formal legal cybercrime complaint dossier ready for cybercrime.gov.in
   * pre-citing Sections 66C and 66D of the IT Act 2000 and Section 43 of the Aadhaar Act.
   */
  public static generateCybercrimeComplaint(req: CybercrimeComplaintRequest): CybercrimeComplaintDossier {
    return generateCybercrimeComplaint(req);
  }

  /**
   * Verifies an offline cryptographic signature on a CertifiedIdentityPass.
   * Can be executed by verifiers completely offline with zero server dependency.
   */
  public static verifyCertifiedIdentityPass(pass: CertifiedIdentityPass): { verified: boolean; error?: string } {
    return verifyCertifiedIdentityPass(pass);
  }

  /**
   * Evaluates the host device for root, jailbreak, debugger, or automated testing environments.
   */
  public static checkDeviceIntegrity(): DeviceIntegrityReport {
    return antiTamperShield.checkDeviceIntegrity();
  }

  /**
   * Sanitizes unstructured text by stripping zero-width characters and normalizing homoglyphs.
   */
  public static sanitizeText(text: string): string {
    return HomoglyphSanitizer.sanitize(text);
  }

  /**
   * Performs an on-device K-Anonymity dark web breach scan using the local Bloom Filter.
   */
  public static checkIdentifierThreat(value: string): KAnonymityCheckResult {
    return ThreatFeedEngine.checkIdentifier(value);
  }

  /**
   * Safely copies sensitive credentials to clipboard and schedules automatic 45-second memory purge.
   */
  public static safeCopyToClipboard(text: string, label?: string): void {
    antiTamperShield.safeCopyToClipboard(text, label);
  }

  /**
   * Generates a 16-digit disposable UIDAI Virtual ID (VID) with Verhoeff checksum.
   */
  public static generateVirtualId(): { vid: string; formatted: string; validUntil: string } {
    return localEngine.generateVirtualId();
  }

  // Instance wrappers for dependency injection
  public validateAadhaar(rawInput: string): ValidationResult {
    return SurakshaShield.validateAadhaar(rawInput);
  }

  public validatePan(rawInput: string): ValidationResult {
    return SurakshaShield.validatePan(rawInput);
  }

  public detectIdentifiers(text: string) {
    return SurakshaShield.detectIdentifiersInText(text);
  }

  public createHotelPass(holderName: string, maskedId: string, hotelName: string): CertifiedIdentityPass {
    return SurakshaShield.generateCertifiedIdentityPass({
      documentType: 'aadhaar',
      holderName,
      maskedIdentifier: maskedId,
      recipientEntity: hotelName,
      purpose: 'hotel_checkin',
    });
  }
}

export default SurakshaShield;
export type {
  ValidationResult,
  DocumentType,
  DetectedIdentifier,
  PassRequest,
  CertifiedIdentityPass,
  CybercrimeComplaintRequest,
  CybercrimeComplaintDossier,
  DeviceIntegrityReport,
  KAnonymityCheckResult,
  VaultBackupData,
  EncryptedBackupPackage,
};
