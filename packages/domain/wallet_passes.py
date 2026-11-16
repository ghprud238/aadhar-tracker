"""
Apple Wallet (.pkpass) & Google Wallet Digital Pass Generator.
Produces compliant JSON manifests for single-use watermarked identity passes.
"""
from typing import Dict, Any
from packages.domain.schemas import WalletPassRequest, WalletPassDTO


class WalletPassGenerator:
    @classmethod
    def generate_wallet_pass(cls, req: WalletPassRequest) -> WalletPassDTO:
        # 1. Apple Wallet pass.json structure
        apple_pass_json = {
            "formatVersion": 1,
            "passTypeIdentifier": "pass.in.suraksha.identity",
            "serialNumber": req.pass_id,
            "teamIdentifier": "SURAKSHA_INDIA",
            "organizationName": "Suraksha Citizen Identity Shield",
            "description": f"Purpose-Restricted Identity Pass for {req.recipient_entity}",
            "logoText": "SURAKSHA SHIELD",
            "foregroundColor": "rgb(255, 255, 255)",
            "backgroundColor": "rgb(15, 23, 42)",
            "labelColor": "rgb(56, 189, 248)",
            "generic": {
                "headerFields": [
                    {
                        "key": "expiry",
                        "label": "VALID UNTIL",
                        "value": req.valid_until,
                    }
                ],
                "primaryFields": [
                    {
                        "key": "masked_id",
                        "label": f"MASKED {req.document_type.upper()}",
                        "value": req.masked_identifier,
                    }
                ],
                "secondaryFields": [
                    {
                        "key": "holder",
                        "label": "AUTHORIZED HOLDER",
                        "value": req.holder_name,
                    },
                    {
                        "key": "recipient",
                        "label": "PERMITTED ENTITY",
                        "value": req.recipient_entity,
                    }
                ],
                "auxiliaryFields": [
                    {
                        "key": "purpose",
                        "label": "EXCLUSIVE PURPOSE",
                        "value": req.purpose.replace("_", " ").upper(),
                    },
                    {
                        "key": "signer",
                        "label": "ED25519 SIGNATURE",
                        "value": f"{req.signature_hex[:16]}...",
                    }
                ],
                "backFields": [
                    {
                        "key": "statutory_notice",
                        "label": "LEGAL CLAUSE (AADHAAR ACT SEC 29 & 43)",
                        "value": "This certified pass is single-use and restricted solely to the named recipient entity. Unauthorized photocopying, resale, or secondary KYC verification is a criminal offense under Section 43 of the Aadhaar Act, 2016 and Section 66C/66D of the Information Technology Act, 2000."
                    },
                    {
                        "key": "signer_pubkey",
                        "label": "DEVICE PUBLIC KEY",
                        "value": req.signer_public_key
                    }
                ]
            },
            "barcodes": [
                {
                    "format": "PKBarcodeFormatQR",
                    "message": f"suraksha://pass/{req.pass_id}?sig={req.signature_hex}&pk={req.signer_public_key}&doc={req.masked_identifier}",
                    "messageEncoding": "iso-8859-1",
                    "altText": f"Pass ID: {req.pass_id} (Ed25519 Verified)"
                }
            ]
        }

        # 2. Google Wallet Generic Object Claims
        google_wallet_jwt_payload = {
            "iss": "suraksha-identity-shield@google-cloud.iam.gserviceaccount.com",
            "aud": "google",
            "origins": ["https://suraksha.in"],
            "typ": "savetogooglewallet",
            "payload": {
                "genericObjects": [
                    {
                        "id": f"3388000000022211.suraksha_{req.pass_id}",
                        "classId": "3388000000022211.suraksha_identity_pass_class",
                        "logo": {
                            "sourceUri": {
                                "uri": "https://suraksha.in/assets/logo-shield.png"
                            },
                            "contentDescription": {
                                "defaultValue": {
                                    "language": "en-US",
                                    "value": "Suraksha Shield Logo"
                                }
                            }
                        },
                        "cardTitle": {
                            "defaultValue": {
                                "language": "en-US",
                                "value": f"Masked {req.document_type.upper()} Pass"
                            }
                        },
                        "subheader": {
                            "defaultValue": {
                                "language": "en-US",
                                "value": req.holder_name
                            }
                        },
                        "header": {
                            "defaultValue": {
                                "language": "en-US",
                                "value": req.masked_identifier
                            }
                        },
                        "barcode": {
                            "type": "QR_CODE",
                            "value": f"suraksha://pass/{req.pass_id}?sig={req.signature_hex}&pk={req.signer_public_key}",
                            "alternateText": req.pass_id
                        },
                        "hexBackgroundColor": "#0f172a"
                    }
                ]
            }
        }

        barcode_payload = f"suraksha://pass/{req.pass_id}?sig={req.signature_hex}&pk={req.signer_public_key}"

        return WalletPassDTO(
            apple_pass_json=apple_pass_json,
            google_wallet_jwt_payload=google_wallet_jwt_payload,
            barcode_payload=barcode_payload,
            mime_type="application/json"
        )
