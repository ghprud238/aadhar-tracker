/**
 * Adversarial OCR & Homoglyph Sanitization Engine
 * 
 * Protects government document parsers from:
 * 1. Unicode confusable homoglyphs (e.g. Cyrillic 'А' U+0410 mimicking Latin 'A' U+0041).
 * 2. Invisible zero-width attack vectors (ZWSP, ZWNJ, ZWJ, RTL overrides).
 * 3. Optical Character Recognition (OCR) letter/digit ambiguities (0 vs O, 1 vs I).
 * 4. Regex Denial of Service (ReDoS) by enforcing maximum linear length bounds.
 */

// Mapping of Cyrillic and Greek homoglyphs to ASCII uppercase Latin equivalents
const HOMOGLYPH_MAP: Record<string, string> = {
  // Cyrillic Uppercase
  '\u0410': 'A',
  '\u0412': 'B',
  '\u0421': 'C',
  '\u0415': 'E',
  '\u041D': 'H',
  '\u0406': 'I',
  '\u0408': 'J',
  '\u041A': 'K',
  '\u041C': 'M',
  '\u041E': 'O',
  '\u0420': 'P',
  '\u0422': 'T',
  '\u0423': 'Y',
  '\u0425': 'X',
  // Cyrillic Lowercase
  '\u0430': 'A',
  '\u0435': 'E',
  '\u043E': 'O',
  '\u0440': 'P',
  '\u0441': 'C',
  '\u0443': 'Y',
  '\u0445': 'X',
  // Greek Uppercase
  '\u0391': 'A',
  '\u0392': 'B',
  '\u0393': 'G',
  '\u0395': 'E',
  '\u0396': 'Z',
  '\u0397': 'H',
  '\u0399': 'I',
  '\u039A': 'K',
  '\u039C': 'M',
  '\u039D': 'N',
  '\u039F': 'O',
  '\u03A1': 'P',
  '\u03A4': 'T',
  '\u03A5': 'Y',
  '\u03A7': 'X',
};

// Invisible control characters and bidirectional overrides
const INVISIBLE_CHARS_REGEX = /[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E\u2060-\u206F\u00AD]/g;

export class HomoglyphSanitizer {
  private static MAX_INPUT_LENGTH = 10000;

  /**
   * Sanitizes generic unstructured text by stripping invisible zero-width characters,
   * normalizing Unicode to NFKC, and mapping homoglyph lookalikes to Latin ASCII.
   */
  public static sanitize(text: string): string {
    if (!text || typeof text !== 'string') return '';

    // Enforce linear length ceiling against memory/ReDoS attacks
    const bounded = text.slice(0, this.MAX_INPUT_LENGTH);

    // 1. Strip zero-width & bidirectional override characters
    const stripped = bounded.replace(INVISIBLE_CHARS_REGEX, '');

    // 2. Normalize via Unicode NFKC (Normal Form Compatibility Composition)
    const normalized = stripped.normalize('NFKC');

    // 3. Map homoglyphs to ASCII
    let result = '';
    for (let i = 0; i < normalized.length; i++) {
      const char = normalized[i];
      result += HOMOGLYPH_MAP[char] || char;
    }

    return result;
  }

  /**
   * Normalizes Indian Permanent Account Number (PAN) specifically, correcting OCR ambiguities:
   * Positions 0-4: Must be Letters (e.g. '0' -> 'O')
   * Positions 5-8: Must be Digits  (e.g. 'O' -> '0', 'I'/'l' -> '1')
   * Position 9:    Must be Letter  (e.g. '0' -> 'O')
   */
  public static sanitizePan(raw: string): string {
    const clean = this.sanitize(raw).replace(/[\s-]/g, '').toUpperCase();
    if (clean.length !== 10) return clean;

    const chars = clean.split('');

    // Positions 0 to 4: Letters only
    for (let i = 0; i <= 4; i++) {
      if (chars[i] === '0') chars[i] = 'O';
      if (chars[i] === '1') chars[i] = 'I';
      if (chars[i] === '5') chars[i] = 'S';
      if (chars[i] === '8') chars[i] = 'B';
    }

    // Positions 5 to 8: Digits only
    for (let i = 5; i <= 8; i++) {
      if (chars[i] === 'O' || chars[i] === 'o') chars[i] = '0';
      if (chars[i] === 'I' || chars[i] === 'l' || chars[i] === 'L') chars[i] = '1';
      if (chars[i] === 'S' || chars[i] === 's') chars[i] = '5';
      if (chars[i] === 'B') chars[i] = '8';
    }

    // Position 9: Letter only
    if (chars[9] === '0') chars[9] = 'O';
    if (chars[9] === '1') chars[9] = 'I';

    return chars.join('');
  }

  /**
   * Normalizes Indian Aadhaar number specifically, converting common digit OCR misreads.
   */
  public static sanitizeAadhaar(raw: string): string {
    const clean = this.sanitize(raw).replace(/[\s-]/g, '');
    let result = '';
    for (let i = 0; i < clean.length; i++) {
      const c = clean[i];
      if (c === 'O' || c === 'o') result += '0';
      else if (c === 'I' || c === 'l' || c === 'L' || c === '|') result += '1';
      else if (c === 'S' || c === 's') result += '5';
      else if (c === 'B') result += '8';
      else result += c;
    }
    return result;
  }
}
