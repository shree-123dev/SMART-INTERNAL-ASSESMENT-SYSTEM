# Centralized Academic Configuration for SIAMS
# Standard Assessment Scales, Minimum Passing Criteria & Examination Parameters

# ---------------- ATTENDANCE CONFIGURATION ----------------
MIN_ATTENDANCE_PERCENTAGE = 75.0   # Mandatory 75% attendance threshold for examination eligibility

# ---------------- INTERNAL ASSESSMENT (IA) ----------------
MAX_IA1_MARKS = 20.0               # Maximum marks for IA-1
MIN_PASS_IA1 = 8.0                 # Minimum passing marks for IA-1 (8 out of 20)

MAX_IA2_MARKS = 20.0               # Maximum marks for IA-2
MIN_PASS_IA2 = 8.0                 # Minimum passing marks for IA-2 (8 out of 20)

MIN_PASS_COMBINED_IA = 16.0        # Combined IA minimum passing marks (16 across IA1 + IA2)

# ---------------- PRACTICAL / LAB EXPERIMENTS ----------------
MAX_PRACTICAL_MARKS = 15.0         # Maximum marks for Practical / Lab Experiments
MIN_PASS_PRACTICAL = 10.0          # Minimum passing marks for Practical (10 out of 15)

# ---------------- ASSIGNMENTS ----------------
MAX_ASSIGNMENT_MARKS = 30.0        # Maximum marks for Assignments
MIN_PASS_ASSIGNMENT = 15.0         # Minimum passing marks for Assignments (15 out of 30)

# ---------------- ORAL / PRACTICAL VIVA EXAMINATION ----------------
MAX_ORAL_MARKS = 25.0              # Maximum marks for Final Oral / Viva Examination
MIN_PASS_ORAL = 15.0               # Minimum passing marks for Oral / Viva (15 out of 25)

# ---------------- TOTAL ASSESSMENT AGGREGATION ----------------
MAX_IA_AVERAGE = 20.0              # IA component scaled to 20
MAX_PRACTICAL_AVERAGE = 15.0       # Practical experiments component scaled to 15
MAX_ASSIGNMENT_AVERAGE = 30.0      # Assignments component scaled to 30
MAX_ORAL_WEIGHT = 25.0             # Oral examination component scaled to 25

TOTAL_CIE_MAX = 90.0               # Total maximum scale: 20 (IA) + 15 (Practical) + 30 (Assignment) + 25 (Oral) = 90
