/**
 * Verhoeff Dihedral (D5) Algorithm & Government Identifier Detector (Client-Side)
 * 100% on-device mathematical verification.
 * Zero cloud dependency.
 */

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
 * Enforces:
 * 1. Exactly 12 digits.
 * 2. Cannot start with 0 or 1.
 * 3. Verhoeff dihedral D5 checksum verification.
 */
export function validateAadhaar(rawInput: string): ValidationResult {
  const clean = rawInput.replace(/[\s-]/g, '');
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
 * Format: 5 uppercase letters + 4 digits + 1 uppercase letter (e.g. ABCDE1234F).
 * Fourth character must be one of: P, C, H, F, A, T, B, L, J, G.
 */
export function validatePan(rawInput: string): ValidationResult {
  const clean = rawInput.trim().toUpperCase();
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

export interface DetectedIdentifier {
  raw: string;
  masked: string;
  type: 'aadhaar' | 'pan';
}

/**
 * Scans an arbitrary block of text for unmasked Aadhaar and PAN numbers.
 * Validates each match using Verhoeff checksum to eliminate false positives.
 */
export function detectIdentifiersInText(text: string): {
  aadhaar: DetectedIdentifier[];
  pan: DetectedIdentifier[];
} {
  const findings: { aadhaar: DetectedIdentifier[]; pan: DetectedIdentifier[] } = {
    aadhaar: [],
    pan: [],
  };

  // 1. Scan for Aadhaar candidate tokens (12 consecutive digits, or 4-4-4 groupings)
  const aadhaarRegex = /\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b/g;
  const matches = text.match(aadhaarRegex) || [];
  for (const m of matches) {
    const val = validateAadhaar(m);
    if (val.valid) {
      findings.aadhaar.push({
        raw: m,
        masked: val.masked,
        type: 'aadhaar',
      });
    }
  }

  // 2. Scan for PAN candidates
  const panRegex = /\b[A-Z]{5}[0-9]{4}[A-Z]\b/g;
  const panMatches = text.match(panRegex) || [];
  for (const p of panMatches) {
    const val = validatePan(p);
    if (val.valid) {
      findings.pan.push({
        raw: p,
        masked: val.masked,
        type: 'pan',
      });
    }
  }

  return findings;
}
