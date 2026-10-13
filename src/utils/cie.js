// Pure calculation functions for Continuous Internal Evaluation (CIE) & Attendance

/**
 * Computes attendance percentage.
 * Returns null if total is 0 or invalid.
 * Otherwise returns a number rounded to 1 decimal place.
 */
export const attendancePercent = (present, total) => {
  const t = Number(total);
  if (!t || isNaN(t) || t <= 0) return null;
  const p = Math.max(0, Number(present) || 0);
  return Number(((p / t) * 100).toFixed(1));
};

/**
 * Calculates how many consecutive future sessions a student must attend
 * without missing any to achieve >= 75% attendance.
 * Formula: max(0, 3*T - 4*P)
 */
export const requiredFutureSessions = (P, T) => {
  const p = Math.max(0, Number(P) || 0);
  const t = Math.max(0, Number(T) || 0);
  return Math.max(0, 3 * t - 4 * p);
};

/**
 * Evaluates CIE marks against institutional passing rubrics:
 * - IA1: max 20 (min 8)
 * - IA2: max 20 (min 8)
 * - IA: average of both: (IA1 + IA2) / 2
 * - Practical: max 15 (min 10)
 * - Assignment: max 30 (min 15)
 * - Oral: max 25 (min 15)
 * - total: /90 (IA avg + Practical + Assignment + Oral)
 * - status: PASS | FAIL | PENDING
 */
export const calculateCie = (marks = {}) => {
  const { ia1, ia2, practical, assignment, oral } = marks;

  const isPresent = (v) => v !== undefined && v !== null && v !== '' && !isNaN(Number(v));

  const hasIa1 = isPresent(ia1);
  const hasIa2 = isPresent(ia2);
  const hasPractical = isPresent(practical);
  const hasAssignment = isPresent(assignment);
  const hasOral = isPresent(oral);

  const numIa1 = hasIa1 ? Number(ia1) : null;
  const numIa2 = hasIa2 ? Number(ia2) : null;
  const numPractical = hasPractical ? Number(practical) : null;
  const numAssignment = hasAssignment ? Number(assignment) : null;
  const numOral = hasOral ? Number(oral) : null;

  // IA average: average of IA1 and IA2
  let iaAvg = null;
  if (hasIa1 && hasIa2) {
    iaAvg = Number(((numIa1 + numIa2) / 2).toFixed(1));
  } else if (hasIa1) {
    iaAvg = numIa1;
  } else if (hasIa2) {
    iaAvg = numIa2;
  }

  // Total out of 90: IA avg + Practical + Assignment + Oral
  let total = null;
  const components = [iaAvg, numPractical, numAssignment, numOral].filter((v) => v !== null);
  if (components.length > 0) {
    total = Number(components.reduce((acc, curr) => acc + curr, 0).toFixed(1));
  }

  // Status computation:
  // If ANY component is missing (ia1, ia2, practical, assignment, oral), status is PENDING
  let status = 'PENDING';
  if (hasIa1 && hasIa2 && hasPractical && hasAssignment && hasOral) {
    const passesIa1 = numIa1 >= 8;
    const passesIa2 = numIa2 >= 8;
    const passesPractical = numPractical >= 10;
    const passesAssignment = numAssignment >= 15;
    const passesOral = numOral >= 15;

    if (passesIa1 && passesIa2 && passesPractical && passesAssignment && passesOral) {
      status = 'PASS';
    } else {
      status = 'FAIL';
    }
  }

  return {
    ia1: numIa1,
    ia2: numIa2,
    iaAvg,
    practical: numPractical,
    assignment: numAssignment,
    oral: numOral,
    total,
    status
  };
};
