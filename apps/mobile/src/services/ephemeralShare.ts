/**
 * Ephemeral Time-Bombed Sharing Service (Client)
 * 
 * Provides:
 * 1. Encrypted self-destructing links for sharing watermarked passes with hotels/car rentals.
 * 2. Configurable time-to-live (1 hour, 24 hours, or 1-view burn).
 * 3. Prevents permanent retention of identity photocopies in WhatsApp/email threads.
 */

export interface EphemeralShareLink {
  token: string;
  shareUrl: string;
  expiresAt: string;
  ttlText: string;
  singleBurn: boolean;
  rawPayload: string;
  createdAt: string;
}

export class EphemeralShareService {
  public static createEphemeralLink(params: {
    passId: string;
    recipientEntity: string;
    purpose: string;
    ttlHours?: number;
    singleBurn?: boolean;
    encryptedPayload: string;
  }): EphemeralShareLink {
    const hours = params.ttlHours || 24;
    const singleBurn = params.singleBurn !== false;
    const token = `suraksha_ephem_${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 6)}`;
    const expiresAt = new Date(Date.now() + hours * 3600 * 1000).toISOString();
    const shareUrl = `https://suraksha.in/p/${token}`;

    return {
      token,
      shareUrl,
      expiresAt,
      ttlText: singleBurn ? 'Self-destructs after single viewing or 24h' : `Valid for ${hours} hours`,
      singleBurn,
      rawPayload: params.encryptedPayload,
      createdAt: new Date().toISOString(),
    };
  }
}
