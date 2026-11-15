/**
 * Verhoeff Dihedral (D5) Algorithm & Multi-Document Government Identifier Detector
 * 100% on-device mathematical verification & pattern matching.
 * Covers Aadhaar, PAN, Driving License, Voter ID (EPIC), and Passport.
 * Zero cloud dependency.
 */

import { HomoglyphSanitizer } from './homoglyphSanitizer';

// The multiplication table for the dihedral group D5
const D5_TABLE: number[][] = [
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
  [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
  [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
  [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
  [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
  [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
  [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
  [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
  [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
];

// The permutation table (p)
const P_TABLE: number[][] = [
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
  [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
  [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
  [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
  [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
  [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
  [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
];

// The inverse table (inv)
const INV_TABLE: number[] = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9];

/**
 * Validates a numeric string against the Verhoeff algorithm.
 */
export function validateVerhoeff(numStr: string): boolean {
  const clean = numStr.replace(/\D/g, '');
  if (!clean) return false;

  let c = 0;
  const reversed = clean.split('').reverse().map(Number);
  for (let i = 0; i < reversed.length; i++) {
    c = D5_TABLE[c][P_TABLE[i % 8][reversed[i]]];
  }
  return c === 0;
}

/**
 * Generates the single Verhoeff check digit for an 11-digit or n-digit prefix.
 */
export function generateVerhoeffChecksum(numStr: string): number {
  const clean = numStr.replace(/\D/g, '');
  let c = 0;
  const reversed = clean.split('').reverse().map(Number);
  for (let i = 0; i < reversed.length; i++) {
    c = D5_TABLE[c][P_TABLE[(i + 1) % 8][reversed[i]]];
  }
  return INV_TABLE[c];
}

export interface ValidationResult {
  valid: boolean;
  error: string;
  masked: string;
}

/**
 * Validates a 12-digit Indian Aadhaar number.
 */
export function validateAadhaar(rawInput: string): ValidationResult {
  const sanitized = HomoglyphSanitizer.sanitizeAadhaar(rawInput);
  const clean = sanitized.replace(/[\s-]/g, '');
  if (!/^\d+$/.test(clean)) {
    return { valid: false, error: 'Aadhaar must contain only digits.', masked: '' };
  }
  if (clean.length !== 12) {
    return { valid: false, error: `Aadhaar must be exactly 12 digits (got ${clean.length}).`, masked: '' };
  }
  if (clean.startsWith('0') || clean.startsWith('1')) {
    return { valid: false, error: 'Aadhaar number cannot start with 0 or 1.', masked: '' };
  }
  if (!validateVerhoeff(clean)) {
    return { valid: false, error: 'Failed Verhoeff D5 checksum verification (invalid number).', masked: '' };
  }
  const masked = `XXXX-XXXX-${clean.slice(8)}`;
  return { valid: true, error: '', masked };
}

/**
 * Validates an Indian Permanent Account Number (PAN).
 * Format: 5 uppercase letters + 4 digits + 1 uppercase letter.
 */
export function validatePan(rawInput: string): ValidationResult {
  const clean = HomoglyphSanitizer.sanitizePan(rawInput);
  const panRegex = /^[A-Z]{3}[PCHFATBLJG][A-Z][0-9]{4}[A-Z]$/;
  if (!panRegex.test(clean)) {
    return {
      valid: false,
      error: 'Invalid PAN structure. Must match [A-Z]{5}[0-9]{4}[A-Z] with a valid taxpayer category character.',
      masked: '',
    };
  }
  const masked = `${clean.slice(0, 2)}***${clean.slice(5, 7)}*${clean.slice(9)}`;
  return { valid: true, error: '', masked };
}

/**
 * Validates an Indian Driving License (DL).
 * Format: 2-letter state code + 2-digit RTO code + 4-digit issue year + 7 sequential digits.
 * e.g. MH-1220150012345 or DL1420110012345.
 */
export function validateDrivingLicense(rawInput: string): ValidationResult {
  const sanitized = HomoglyphSanitizer.sanitize(rawInput);
  const clean = sanitized.replace(/[\s-]/g, '').toUpperCase();
  const dlRegex = /^[A-Z]{2}[0-9]{2}(19[0-9]{2}|20[0-2][0-9])[0-9]{7}$/;
  if (!dlRegex.test(clean)) {
    return {
      valid: false,
      error: 'Invalid Driving License format. Expected State (2) + RTO (2) + Year (4) + Digits (7).',
      masked: '',
    };
  }
  const masked = `${clean.slice(0, 4)}****${clean.slice(-4)}`;
  return { valid: true, error: '', masked };
}

/**
 * Validates an Indian Voter ID (EPIC - Electors Photo Identity Card).
 * Format: 3 uppercase letters followed by 7 digits (e.g. ABC1234567).
 */
export function validateVoterId(rawInput: string): ValidationResult {
  const sanitized = HomoglyphSanitizer.sanitize(rawInput);
  const clean = sanitized.trim().toUpperCase();
  const epicRegex = /^[A-Z]{3}[0-9]{7}$/;
  if (!epicRegex.test(clean)) {
    return {
      valid: false,
      error: 'Invalid Voter ID (EPIC) format. Must be 3 letters followed by 7 digits.',
      masked: '',
    };
  }
  const masked = `${clean.slice(0, 3)}****${clean.slice(-3)}`;
  return { valid: true, error: '', masked };
}

/**
 * Validates an Indian Passport Number.
 * Format: 1 uppercase letter followed by 7 digits (e.g. A1234567).
 */
export function validatePassport(rawInput: string): ValidationResult {
  const sanitized = HomoglyphSanitizer.sanitize(rawInput);
  const clean = sanitized.trim().toUpperCase();
  const passportRegex = /^[A-Z][0-9]{7}$/;
  if (!passportRegex.test(clean)) {
    return {
      valid: false,
      error: 'Invalid Passport format. Must be 1 letter followed by 7 digits.',
      masked: '',
    };
  }
  const masked = `${clean.slice(0, 1)}****${clean.slice(-2)}`;
  return { valid: true, error: '', masked };
}

export type DocumentType = 'aadhaar' | 'pan' | 'driving_license' | 'voter_id' | 'passport';

export interface DetectedIdentifier {
  raw: string;
  masked: string;
  type: DocumentType;
}

/**
 * Scans an arbitrary block of text for unmasked government identifiers:
 * Aadhaar, PAN, Driving License, Voter ID, and Passport.
 */
export function detectIdentifiersInText(text: string): {
  aadhaar: DetectedIdentifier[];
  pan: DetectedIdentifier[];
  driving_license: DetectedIdentifier[];
  voter_id: DetectedIdentifier[];
  passport: DetectedIdentifier[];
} {
  const sanitizedText = HomoglyphSanitizer.sanitize(text);
  const findings: {
    aadhaar: DetectedIdentifier[];
    pan: DetectedIdentifier[];
    driving_license: DetectedIdentifier[];
    voter_id: DetectedIdentifier[];
    passport: DetectedIdentifier[];
  } = {
    aadhaar: [],
    pan: [],
    driving_license: [],
    voter_id: [],
    passport: [],
  };

  // 1. Aadhaar (12 digits, Verhoeff validated)
  const aadhaarRegex = /\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b/g;
  const aadhaarMatches = sanitizedText.match(aadhaarRegex) || [];
  for (const m of aadhaarMatches) {
    const val = validateAadhaar(m);
    if (val.valid) {
      findings.aadhaar.push({ raw: m, masked: val.masked, type: 'aadhaar' });
    }
  }

  // 2. PAN (5 letters + 4 digits + 1 letter)
  const panRegex = /\b[A-Z]{5}[0-9]{4}[A-Z]\b/g;
  const panMatches = text.match(panRegex) || [];
  for (const p of panMatches) {
    const val = validatePan(p);
    if (val.valid) {
      findings.pan.push({ raw: p, masked: val.masked, type: 'pan' });
    }
  }

  // 3. Driving License (e.g. MH-12-2015-0012345 or DL1420110012345)
  const dlRegex = /\b[A-Z]{2}[-\s]?[0-9]{2}[-\s]?(?:19|20)[0-9]{2}[-\s]?[0-9]{7}\b/gi;
  const dlMatches = text.match(dlRegex) || [];
  for (const dl of dlMatches) {
    const val = validateDrivingLicense(dl);
    if (val.valid) {
      findings.driving_license.push({ raw: dl, masked: val.masked, type: 'driving_license' });
    }
  }

  // 4. Voter ID / EPIC (3 letters + 7 digits)
  const epicRegex = /\b[A-Z]{3}[0-9]{7}\b/g;
  const epicMatches = text.match(epicRegex) || [];
  for (const e of epicMatches) {
    const val = validateVoterId(e);
    if (val.valid) {
      findings.voter_id.push({ raw: e, masked: val.masked, type: 'voter_id' });
    }
  }

  // 5. Passport (1 letter + 7 digits, preceded by word boundary / context)
  const passportRegex = /\b[A-PR-WYa-pr-wy][1-9][0-9]{6}\b/g;
  const passportMatches = text.match(passportRegex) || [];
  for (const pass of passportMatches) {
    const val = validatePassport(pass);
    if (val.valid) {
      findings.passport.push({ raw: pass, masked: val.masked, type: 'passport' });
    }
  }

  return findings;
}
