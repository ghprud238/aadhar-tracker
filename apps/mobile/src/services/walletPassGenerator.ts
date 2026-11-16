/**
 * Apple Wallet (.pkpass) & Google Wallet Digital Pass Generator (Client)
 * 
 * Formats single-use watermarked passes into:
 * 1. Apple Wallet pass.json structure with Ed25519 QR barcode and statutory warning clause.
 * 2. Google Wallet generic pass class & object claims.
 */

export interface MobileWalletPassPayload {
  passId: string;
  applePassJson: Record<string, any>;
  googleWalletJwtPayload: Record<string, any>;
  barcodePayload: string;
  exportedAt: string;
}

export class WalletPassGeneratorService {
  public static generatePass(params: {
    passId: string;
    holderName: string;
    documentType: string;
    maskedIdentifier: string;
    recipientEntity: string;
    purpose: string;
    validUntil: string;
    signerPublicKey: string;
    signatureHex: string;
  }): MobileWalletPassPayload {
    const applePassJson = {
      formatVersion: 1,
      passTypeIdentifier: 'pass.in.suraksha.identity',
      serialNumber: params.passId,
      teamIdentifier: 'SURAKSHA_INDIA',
      organizationName: 'Suraksha Citizen Identity Shield',
      description: `Purpose-Restricted Identity Pass for ${params.recipientEntity}`,
      logoText: 'SURAKSHA SHIELD',
      foregroundColor: 'rgb(255, 255, 255)',
      backgroundColor: 'rgb(15, 23, 42)',
      labelColor: 'rgb(56, 189, 248)',
      generic: {
        headerFields: [
          {
            key: 'expiry',
            label: 'VALID UNTIL',
            value: params.validUntil,
          },
        ],
        primaryFields: [
          {
            key: 'masked_id',
            label: `MASKED ${params.documentType.toUpperCase()}`,
            value: params.maskedIdentifier,
          },
        ],
        secondaryFields: [
          {
            key: 'holder',
            label: 'AUTHORIZED HOLDER',
            value: params.holderName,
          },
          {
            key: 'recipient',
            label: 'PERMITTED ENTITY',
            value: params.recipientEntity,
          },
        ],
        auxiliaryFields: [
          {
            key: 'purpose',
            label: 'EXCLUSIVE PURPOSE',
            value: params.purpose.replace(/_/g, ' ').toUpperCase(),
          },
          {
            key: 'sig',
            label: 'ED25519 SIGNATURE',
            value: `${params.signatureHex.slice(0, 16)}...`,
          },
        ],
        backFields: [
          {
            key: 'statutory_notice',
            label: 'LEGAL CLAUSE (AADHAAR ACT SEC 29 & 43)',
            value: 'This certified pass is single-use and restricted solely to the named recipient entity. Unauthorized photocopying, resale, or secondary KYC verification is a criminal offense under Section 43 of the Aadhaar Act, 2016 and Section 66C/66D of the Information Technology Act, 2000.',
          },
          {
            key: 'signer_pubkey',
            label: 'DEVICE PUBLIC KEY',
            value: params.signerPublicKey,
          },
        ],
      },
      barcodes: [
        {
          format: 'PKBarcodeFormatQR',
          message: `suraksha://pass/${params.passId}?sig=${params.signatureHex}&pk=${params.signerPublicKey}&doc=${params.maskedIdentifier}`,
          messageEncoding: 'iso-8859-1',
          altText: `Pass ID: ${params.passId} (Ed25519 Verified)`,
        },
      ],
    };

    const googleWalletJwtPayload = {
      iss: 'suraksha-identity-shield@google-cloud.iam.gserviceaccount.com',
      aud: 'google',
      origins: ['https://suraksha.in'],
      typ: 'savetogooglewallet',
      payload: {
        genericObjects: [
          {
            id: `3388000000022211.suraksha_${params.passId}`,
            classId: '3388000000022211.suraksha_identity_pass_class',
            cardTitle: {
              defaultValue: {
                language: 'en-US',
                value: `Masked ${params.documentType.toUpperCase()} Pass`,
              },
            },
            subheader: {
              defaultValue: {
                language: 'en-US',
                value: params.holderName,
              },
            },
            header: {
              defaultValue: {
                language: 'en-US',
                value: params.maskedIdentifier,
              },
            },
            barcode: {
              type: 'QR_CODE',
              value: `suraksha://pass/${params.passId}?sig=${params.signatureHex}&pk=${params.signerPublicKey}`,
              alternateText: params.passId,
            },
            hexBackgroundColor: '#0f172a',
          },
        ],
      },
    };

    const barcodePayload = `suraksha://pass/${params.passId}?sig=${params.signatureHex}&pk=${params.signerPublicKey}`;

    return {
      passId: params.passId,
      applePassJson,
      googleWalletJwtPayload,
      barcodePayload,
      exportedAt: new Date().toISOString(),
    };
  }
}
