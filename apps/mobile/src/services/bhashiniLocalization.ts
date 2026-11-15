/**
 * Project Bhashini Vernacular Localization & Voice Assistance Service
 * 
 * Provides localized guidance in 7 major Indian languages:
 * English, Hindi (हिन्दी), Tamil (தமிழ்), Telugu (తెలుగు), Bengali (বাংলা), Marathi (मराठी), and Kannada (ಕನ್ನಡ).
 * 
 * Includes voice-script generators for rural citizens and elderly parents navigating
 * biometric locking and cybercrime reporting.
 */

export type SupportedLanguage = 'en' | 'hi' | 'ta' | 'te' | 'bn' | 'mr' | 'kn';

export interface LanguageMeta {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageMeta[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳' },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳' },
];

export interface VernacularPhrases {
  shieldActive: string;
  biometricLockGuide: string;
  emergencyHelpline1930: string;
  passWatermarkNotice: string;
  voicePromptBiometricLock: string;
  voicePromptCybercrimeReport: string;
}

const LOCALIZATION_DICTIONARY: Record<SupportedLanguage, VernacularPhrases> = {
  en: {
    shieldActive: 'Identity Shield Active & Protected',
    biometricLockGuide: 'Lock your Aadhaar biometrics on the official myAadhaar portal to prevent AePS banking fraud.',
    emergencyHelpline1930: 'Dial 1930 immediately to report financial fraud to the National Cyber Crime Portal.',
    passWatermarkNotice: 'Certified Single-Use Pass: Strictly not valid for banking KYC or SIM issuance.',
    voicePromptBiometricLock: 'Open the mAadhaar application, log in with OTP, select Security Services, and tap Lock Biometrics.',
    voicePromptCybercrimeReport: 'If money was deducted from your account, dial toll-free number 1930 immediately and provide your transaction details.',
  },
  hi: {
    shieldActive: 'सुरक्षा कवच सक्रिय और सुरक्षित है',
    biometricLockGuide: 'AePS बैंकिंग धोखाधड़ी रोकने के लिए myAadhaar पोर्टल पर अपने बायोमेट्रिक्स को लॉक करें।',
    emergencyHelpline1930: 'वित्तीय धोखाधड़ी की शिकायत के लिए तुरंत 1930 पर कॉल करें।',
    passWatermarkNotice: 'प्रमाणित पहचान पास: केवल इस उद्देश्य हेतु मान्य, बैंक लोन या सिम कार्ड के लिए अमान्य।',
    voicePromptBiometricLock: 'mAadhaar ऐप खोलें, OTP से लॉगिन करें, सुरक्षा सेवाओं में जाएं और बायोमेट्रिक्स लॉक विकल्प चुनें।',
    voicePromptCybercrimeReport: 'यदि आपके खाते से अनाधिकृत पैसे कटे हैं, तो तुरंत 1930 पर कॉल करें और बैंक का नाम व UTR नंबर बताएं।',
  },
  ta: {
    shieldActive: 'அடையாள பாதுகாப்பு கவசம் செயல்படுகிறது',
    biometricLockGuide: 'வங்கி மோசடியைத் தடுக்க myAadhaar போர்ட்டலில் உங்கள் பயோமெட்ரிக்ஸைப் பூட்டவும்.',
    emergencyHelpline1930: 'சைபர் நிதி மோசடி குறித்து புகாரளிக்க உடனடியாக 1930 எண்ணை அழைக்கவும்.',
    passWatermarkNotice: 'சான்றளிக்கப்பட்ட பாஸ்: ஹோட்டல் சோதனைக்கு மட்டுமே, சிம் அல்லது கடனுக்கு செல்லாது.',
    voicePromptBiometricLock: 'mAadhaar செயலியைத் திறந்து, பயோமெட்ரிக்ஸ் பூட்டு என்பதைத் தேர்ந்தெடுக்கவும்.',
    voicePromptCybercrimeReport: 'பணம் திருடப்பட்டால் உடனடியாக 1930 ஐ அழைத்து வங்கி விவரங்களை வழங்கவும்.',
  },
  te: {
    shieldActive: 'గుర్తింపు రక్షణ కవచం చురుకుగా ఉంది',
    biometricLockGuide: 'AePS బ్యాంకింగ్ మోసాలను నివారించడానికి myAadhaar పోర్టల్‌లో మీ బయోమెట్రిక్స్‌ను లాక్ చేయండి.',
    emergencyHelpline1930: 'సైబర్ మోసాలను నివేదించడానికి వెంటనే 1930 కి కాల్ చేయండి.',
    passWatermarkNotice: 'సర్టిఫైడ్ పాస్: హోటల్ చెక్-ఇన్ కొరకు మాత్రమే, రుణాలు లేదా సిమ్ కార్డుల కొరకు చెల్లదు.',
    voicePromptBiometricLock: 'mAadhaar యాప్‌ను తెరిచి, బయోమెట్రిక్స్ లాక్ చేయండి.',
    voicePromptCybercrimeReport: 'మీ ఖాతా నుండి అనధికారికంగా డబ్బు డెబిట్ చేయబడితే, వెంటనే 1930 కి డయల్ చేయండి.',
  },
  bn: {
    shieldActive: 'পরিচয় সুরক্ষা কবচ সক্রিয় রয়েছে',
    biometricLockGuide: 'ব্যাংকিং জালিয়াতি রোধ করতে myAadhaar পোর্টালে আপনার বায়োমেট্রিক্স লক করুন।',
    emergencyHelpline1930: 'আর্থিক জালিয়াতির অভিযোগ জানাতে অবিলম্বে ১৯৩০ নম্বরে কল করুন।',
    passWatermarkNotice: 'প্রত্যয়িত পাস: শুধুমাত্র যাচাইকরণের জন্য, লোন বা সিম কার্ডের জন্য নয়।',
    voicePromptBiometricLock: 'mAadhaar অ্যাপ খুলুন এবং বায়োমেট্রিক্স লক নির্বাচন করুন।',
    voicePromptCybercrimeReport: 'টাকা কেটে নেওয়া হলে অবিলম্বে ১৯৩০ নম্বরে ফোন করে পুলিশে অভিযোগ করুন।',
  },
  mr: {
    shieldActive: 'सुरक्षा कवच सक्रिय आणि सुरक्षित आहे',
    biometricLockGuide: 'बँकिंग फसवणूक रोखण्यासाठी myAadhaar पोर्टलवर तुमचे बायोमेट्रिक्स लॉक करा.',
    emergencyHelpline1930: 'सायबर फसवणुकीची तक्रार करण्यासाठी ताबडतोब 1930 वर कॉल करा.',
    passWatermarkNotice: 'प्रमाणित ओळख पास: केवळ हॉटेल चेक-इनसाठी, बँक कर्ज किंवा सिम कार्डसाठी अमान्य.',
    voicePromptBiometricLock: 'mAadhaar ॲप उघडा, सुरक्षेत जा आणि बायोमेट्रिक्स लॉक करा.',
    voicePromptCybercrimeReport: 'खात्यातून अनधिकृत पैसे कापले गेल्यास त्वरित 1930 वर संपर्क साधा.',
  },
  kn: {
    shieldActive: 'ಗುರುತಿನ ರಕ್ಷಣೆ ಸಕ್ರಿಯವಾಗಿದೆ',
    biometricLockGuide: 'ಬ್ಯಾಂಕಿಂಗ್ ವಂಚನೆಯನ್ನು ತಡೆಗಟ್ಟಲು myAadhaar ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ನಿಮ್ಮ ಬಯೋಮೆಟ್ರಿಕ್ಸ್ ಲಾಕ್ ಮಾಡಿ.',
    emergencyHelpline1930: 'ಸೈಬರ್ ವಂಚನೆಯನ್ನು ವರದಿ ಮಾಡಲು ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ.',
    passWatermarkNotice: 'ಪ್ರಮಾಣೀಕೃತ ಪಾಸ್: ಪರಿಶೀಲನೆಗೆ ಮಾತ್ರ, ಸಾಲ ಅಥವಾ ಸಿಮ್ ಕಾರ್ಡ್‌ಗೆ ಅನ್ವಯಿಸುವುದಿಲ್ಲ.',
    voicePromptBiometricLock: 'mAadhaar ಅಪ್ಲಿಕೇಶನ್ ತೆರೆಯಿರಿ ಮತ್ತು ಬಯೋಮೆಟ್ರಿಕ್ಸ್ ಲಾಕ್ ಮಾಡಿ.',
    voicePromptCybercrimeReport: 'ಹಣ ಕಡಿತಗೊಂಡರೆ ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ ದೂರು ದಾಖಲಿಸಿ.',
  },
};

export class BhashiniService {
  private static currentLang: SupportedLanguage = 'en';

  public static setLanguage(lang: SupportedLanguage): void {
    this.currentLang = lang;
  }

  public static getLanguage(): SupportedLanguage {
    return this.currentLang;
  }

  public static getStrings(lang: SupportedLanguage = this.currentLang): VernacularPhrases {
    return LOCALIZATION_DICTIONARY[lang] || LOCALIZATION_DICTIONARY['en'];
  }
}
