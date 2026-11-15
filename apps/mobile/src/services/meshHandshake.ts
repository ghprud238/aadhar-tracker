/**
 * Ephemeral QR Handshake Protocol for Zero-Touch Family Mesh Pairing
 * 
 * Enables 1-scan peer-to-peer pairing between adult children and elderly parents' devices
 * over local Wi-Fi without cloud signaling, public brokers, or manual network configuration.
 */

import { FamilyMember } from '../types';

export interface MeshHandshakePayload {
  protocolVersion: string;
  sourceNodeId: string;
  displayName: string;
  relationship: FamilyMember['relationship'];
  ephemeralPublicKeyHex: string;
  nonce: string;
  localNetworkHint: string;
  expiresAt: string;
}

export class MeshHandshakeService {
  /**
   * Generates an ephemeral pairing payload formatted as a URI string for QR rendering.
   */
  public static generatePairingQrPayload(
    displayName: string,
    relationship: FamilyMember['relationship'] = 'parent'
  ): { qrPayload: string; payloadData: MeshHandshakePayload } {
    const nodeId = 'node_' + Math.random().toString(36).substring(2, 10);
    const nonce = Math.random().toString(16).substring(2, 12);
    const pubKey = 'pub_eph_' + Math.random().toString(16).substring(2, 18);
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000).toISOString(); // 15 mins

    const payloadData: MeshHandshakePayload = {
      protocolVersion: 'suraksha-mesh-v1',
      sourceNodeId: nodeId,
      displayName,
      relationship,
      ephemeralPublicKeyHex: pubKey,
      nonce,
      localNetworkHint: 'Direct Wi-Fi / Local Subnet',
      expiresAt,
    };

    const qrPayload = `suraksha_mesh://pair?data=${encodeURIComponent(JSON.stringify(payloadData))}`;

    return {
      qrPayload,
      payloadData,
    };
  }

  /**
   * Validates and imports a scanned family mesh pairing payload.
   */
  public static parseAndAcceptPairing(qrString: string): { success: boolean; member?: FamilyMember; error?: string } {
    try {
      if (!qrString.startsWith('suraksha_mesh://pair')) {
        return { success: false, error: 'Invalid QR protocol: Not a Suraksha Family Mesh handshake.' };
      }

      const match = qrString.match(/data=([^&]+)/);
      if (!match) {
        return { success: false, error: 'Malformed pairing payload parameter.' };
      }

      const decodedJson = decodeURIComponent(match[1]);
      const data: MeshHandshakePayload = JSON.parse(decodedJson);

      if (new Date(data.expiresAt).getTime() < Date.now()) {
        return { success: false, error: 'Pairing handshake expired. Please generate a fresh QR code.' };
      }

      const newMember: FamilyMember = {
        id: data.sourceNodeId,
        name: data.displayName,
        relationship: data.relationship,
        biometrics_locked: true,
        monitored_documents_count: 2,
        last_mesh_sync: new Date().toISOString(),
        has_alerts: false,
      };

      return {
        success: true,
        member: newMember,
      };
    } catch (e: any) {
      return { success: false, error: e.message || 'Corrupt pairing handshake data.' };
    }
  }
}
