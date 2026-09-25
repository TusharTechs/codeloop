"""ACLS vocabulary shared by the spikes (the backend has its own formulary YAML)."""

KEYTERMS = [
    "CodeLoop", "epinephrine", "epi", "amiodarone", "amio", "lidocaine", "adenosine",
    "atropine", "calcium chloride", "calcium gluconate", "sodium bicarbonate", "bicarb",
    "magnesium sulfate", "naloxone", "vasopressin", "dextrose", "V-fib", "VF", "V-tach",
    "pulseless VT", "PEA", "pulseless electrical activity", "asystole", "ROSC",
    "defibrillate", "synchronized cardioversion", "joules", "milligrams", "compressions",
    "rhythm check", "pulse check", "ETCO2", "capnography", "intubated", "IO access",
    "IV access", "bag mask", "code blue",
]

PROMPT = (
    "Audio from an in-hospital cardiac arrest (code blue), captured by a tablet on the crash "
    "cart. Several clinicians talk over monitor alarms and chest compressions: a team leader "
    "giving orders, a medication nurse reading doses back, a compressor, and an airway "
    "clinician. Speech contains ACLS drug names and doses such as epinephrine 1 milligram and "
    "amiodarone 300 or 150 milligrams, defibrillation energies in joules, rhythms such as VF, "
    "pulseless VT, PEA and asystole, and Hindi-English code-switching. Doses and numbers are "
    "safety-critical and are spoken exactly."
)

# Tokens that must survive transcription for each gold event, used for entity accuracy.
DRUG_ALIASES = {
    "epinephrine": {"epinephrine", "epi", "adrenaline"},
    "amiodarone": {"amiodarone", "amio"},
    "lidocaine": {"lidocaine"},
}
RHYTHM_ALIASES = {
    "VF": {"vfib", "v fib", "vf", "ventricular fibrillation", "v-fib"},
    "ASYSTOLE": {"asystole"},
    "PEA": {"pea", "pulseless electrical activity"},
}
NUMBER_FORMS = {
    1: {"1", "one", "ek"},
    150: {"150", "one fifty", "one hundred fifty", "one hundred and fifty"},
    200: {"200", "two hundred"},
    300: {"300", "three hundred", "three zero zero", "3 0 0"},
}
