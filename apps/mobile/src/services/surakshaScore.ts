/**
 * Suraksha Citizen Health Score & Gamified Privacy Engine
 * 
 * Computes a dynamic 0 to 1,000 score representing holistic identity hygiene:
 * - Aadhaar Biometric Lock (+250)
 * - Verified Identity & 2FA (+150)
 * - TAFCOP SIM Audit Status (+100)
 * - Zero Unaddressed Breaches (+150)
 * - Family Mesh Protection (+150)
 * - Single-Use Masked Pass Usage (+200)
 */

export interface ScorePillar {
  id: string;
  title: string;
  currentPoints: number;
  maxPoints: number;
  status: 'achieved' | 'partial' | 'pending';
  actionPrompt: string;
  actionScreen: 'dashboard' | 'identities' | 'incidents' | 'aadhaar' | 'security';
}

export interface AchievementBadge {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlockedDate?: string;
}

export interface SurakshaScoreReport {
  score: number;
  maxScore: number;
  tier: 'FORTRESS GUARDIAN' | 'VIGILANT SENTINEL' | 'PROTECTED CITIZEN' | 'ACTION REQUIRED';
  tierColor: string;
  percentileText: string;
  pillars: ScorePillar[];
  badges: AchievementBadge[];
  topRecommendations: string[];
}

export class SurakshaScoreService {
  public static calculateScore(params: {
    biometricsLocked: boolean;
    activeIdentifiersCount: number;
    hasActiveBreaches: boolean;
    unauthorizedGhostSimsCount: number;
    familyMembersProtectedCount: number;
    hasGeneratedMaskedPass: boolean;
  }): SurakshaScoreReport {
    const pillars: ScorePillar[] = [
      {
        id: 'pillar_bio_lock',
        title: 'UIDAI Biometric Lock',
        currentPoints: params.biometricsLocked ? 250 : 0,
        maxPoints: 250,
        status: params.biometricsLocked ? 'achieved' : 'pending',
        actionPrompt: params.biometricsLocked ? 'Locked on official myAadhaar portal.' : 'Lock biometrics to stop AePS micro-ATM theft.',
        actionScreen: 'aadhaar',
      },
      {
        id: 'pillar_verified_identity',
        title: 'Verified 2FA & Blind Indexing',
        currentPoints: params.activeIdentifiersCount > 0 ? 150 : 0,
        maxPoints: 150,
        status: params.activeIdentifiersCount > 0 ? 'achieved' : 'pending',
        actionPrompt: params.activeIdentifiersCount > 0 ? `${params.activeIdentifiersCount} verified identifier(s) monitored.` : 'Add and verify an email identifier.',
        actionScreen: 'identities',
      },
      {
        id: 'pillar_sim_audit',
        title: 'DoT TAFCOP SIM Audit',
        currentPoints: params.unauthorizedGhostSimsCount === 0 ? 100 : 0,
        maxPoints: 100,
        status: params.unauthorizedGhostSimsCount === 0 ? 'achieved' : 'pending',
        actionPrompt: params.unauthorizedGhostSimsCount === 0 ? 'Zero ghost SIMs detected.' : `Disconnect ${params.unauthorizedGhostSimsCount} unknown SIM(s) immediately on TAFCOP.`,
        actionScreen: 'aadhaar',
      },
      {
        id: 'pillar_breach_hygiene',
        title: 'Dark Web & Breach Hygiene',
        currentPoints: !params.hasActiveBreaches ? 150 : 50,
        maxPoints: 150,
        status: !params.hasActiveBreaches ? 'achieved' : 'partial',
        actionPrompt: !params.hasActiveBreaches ? 'Zero compromised credentials detected.' : 'Review exposed breach incidents and remediate.',
        actionScreen: 'incidents',
      },
      {
        id: 'pillar_family_mesh',
        title: 'Elderly Parents P2P Mesh',
        currentPoints: params.familyMembersProtectedCount > 0 ? 150 : 0,
        maxPoints: 150,
        status: params.familyMembersProtectedCount > 0 ? 'achieved' : 'pending',
        actionPrompt: params.familyMembersProtectedCount > 0 ? `${params.familyMembersProtectedCount} family device(s) protected.` : 'Pair parents via 1-scan QR handshake.',
        actionScreen: 'security',
      },
      {
        id: 'pillar_masked_pass',
        title: 'Single-Use Watermarked Passes',
        currentPoints: params.hasGeneratedMaskedPass ? 200 : 80,
        maxPoints: 200,
        status: params.hasGeneratedMaskedPass ? 'achieved' : 'partial',
        actionPrompt: params.hasGeneratedMaskedPass ? 'Never share unmasked photocopies.' : 'Generate watermarked pass before hotel check-in.',
        actionScreen: 'aadhaar',
      },
    ];

    const totalScore = pillars.reduce((acc, p) => acc + p.currentPoints, 0);

    let tier: SurakshaScoreReport['tier'] = 'ACTION REQUIRED';
    let tierColor = '#ef4444';
    let percentileText = 'Below average. Take immediate protective action.';

    if (totalScore >= 850) {
      tier = 'FORTRESS GUARDIAN';
      tierColor = '#10b981';
      percentileText = 'Top 1% of privacy-conscious Indian citizens.';
    } else if (totalScore >= 700) {
      tier = 'VIGILANT SENTINEL';
      tierColor = '#3b82f6';
      percentileText = 'Top 10% protected. Excellent defense hygiene.';
    } else if (totalScore >= 550) {
      tier = 'PROTECTED CITIZEN';
      tierColor = '#f59e0b';
      percentileText = 'Good foundation. Address remaining gaps below.';
    }

    const badges: AchievementBadge[] = [
      {
        id: 'badge_fortress',
        title: 'Fortress Guardian',
        description: 'Attained a Suraksha score exceeding 850 points.',
        icon: '🏰',
        unlocked: totalScore >= 850,
        unlockedDate: totalScore >= 850 ? '2026-11-16' : undefined,
      },
      {
        id: 'badge_elder_shield',
        title: 'Elder Protector',
        description: 'Successfully paired elderly parents over local P2P mesh.',
        icon: '👨‍👩‍👧',
        unlocked: params.familyMembersProtectedCount > 0,
        unlockedDate: params.familyMembersProtectedCount > 0 ? '2026-11-15' : undefined,
      },
      {
        id: 'badge_zero_leak',
        title: 'Zero-Leak Traveler',
        description: 'Certified single-use masked pass generated for hotel check-in.',
        icon: '🎫',
        unlocked: params.hasGeneratedMaskedPass,
        unlockedDate: params.hasGeneratedMaskedPass ? '2026-11-14' : undefined,
      },
      {
        id: 'badge_sim_buster',
        title: 'Ghost SIM Buster',
        description: 'Audited DoT TAFCOP with zero unauthorized SIM connections.',
        icon: '📶',
        unlocked: params.unauthorizedGhostSimsCount === 0,
        unlockedDate: '2026-11-15',
      },
    ];

    const topRecommendations = pillars
      .filter((p) => p.status !== 'achieved')
      .map((p) => `+${p.maxPoints - p.currentPoints} pts: ${p.title} — ${p.actionPrompt}`);

    return {
      score: totalScore,
      maxScore: 1000,
      tier,
      tierColor,
      percentileText,
      pillars,
      badges,
      topRecommendations,
    };
  }
}
