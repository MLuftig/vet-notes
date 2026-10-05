"""Grade the transcript extraction against the technician-written answer keys."""
import re

from records import expected_code_status, expected_drugs, patients

# Canonical drug name -> patterns that count as a mention of it.
DRUG_PATTERNS = {
    "acepromazine": [r"\bacepromazine\b", r"\bace\b"],
    "amoxicillin-clavulanate": [r"amoxicillin", r"clavulanate", r"clavamox"],
    "enrofloxacin": [r"enrofloxacin", r"\benro\b"],
    "prednisolone": [r"prednisolone", r"\bpred\b"],
    "ampicillin-sulbactam": [r"ampicillin", r"sulbactam", r"unasyn"],
    "butorphanol": [r"butorphanol"],
    "gabapentin": [r"gabapentin", r"\bgaba\b", r"\bgabba\b"],
    "trazodone": [r"trazodone", r"\btraz\b"],
    "methadone": [r"methadone"],
    "fentanyl": [r"fentanyl"],
    "buprenorphine": [r"buprenorphine", r"\bbupe\b"],
    "maropitant": [r"maropitant", r"cerenia"],
}

CONTENT_FIELDS = ["signalment", "why_presented", "changes", "meds_started", "dose_changes",
                  "meds_stopped", "plan", "watch", "pending", "code_status"]


def content_text(summary):
    """The summary's fields only, excluding flags, lowercased."""
    return " ".join(str(summary.get(f, "")) for f in CONTENT_FIELDS).lower()


def drugs_mentioned(text):
    return {drug for drug, pats in DRUG_PATTERNS.items() if any(re.search(p, text) for p in pats)}


def flag_text(summary, flag_type=None):
    flags = summary.get("flags", [])
    if flag_type:
        flags = [f for f in flags if f.get("type") == flag_type]
    return " ".join(f"{f.get('detail', '')} {f.get('quote', '')}" for f in flags).lower()


def result(test, patient_id, passed, detail, critical=False):
    name = patients[patient_id]["name"] if patient_id in patients else "All"
    return {"Patient": name, "Test": test, "Result": "Pass" if passed else "FAIL",
            "Critical": "Yes" if critical else "", "Detail": detail}


def grade(extraction):
    s = extraction["patients"]
    results = []

    # Every census patient must have a summary.
    for pid in patients:
        if pid not in s:
            results.append(result("Summary produced", pid, False, "No summary was produced.", True))
    if any(r["Result"] == "FAIL" for r in results):
        return results

    text = {pid: content_text(s[pid]) for pid in patients}

    # 1. Drug attribution: every drug on the right patient, none on the wrong one.
    for pid, expected in expected_drugs.items():
        found = drugs_mentioned(text[pid])
        missing, extra = expected - found, found - expected
        results.append(result(
            "Medications attributed correctly", pid, not missing and not extra,
            "All expected drugs found, none extra." if not missing and not extra else
            f"Missing: {sorted(missing) or 'none'}. On the wrong patient: {sorted(extra) or 'none'}.",
            critical=bool(extra)))

    # 2. Code status.
    for pid, expected in expected_code_status.items():
        got = str(s[pid].get("code_status", "")).upper()
        results.append(result("Code status", pid, expected in got, f"Expected {expected}, got '{got}'."))

    # 3. Hedge later confirmed: Olive's enrofloxacin is certain, not flagged.
    enro_flagged = "enro" in flag_text(s["P002"], "uncertain")
    results.append(result(
        "Confirmed hedge recorded as certain", "P002",
        "enrofloxacin" in drugs_mentioned(text["P002"]) and not enro_flagged,
        "Enrofloxacin listed and not flagged as uncertain." if not enro_flagged
        else "Enrofloxacin still flagged as uncertain after the doctor confirmed it."))

    # 4. Hedge never confirmed: Duke's trazodone frequency must not be invented.
    invented = re.search(r"twice|bid|every 12|q12|two times", text["P003"])
    flagged = "traz" in flag_text(s["P003"]) or ("frequency" in text["P003"] and "traz" in text["P003"])
    results.append(result(
        "Unconfirmed frequency not invented", "P003", bool(flagged) and not invented,
        "Trazodone frequency left open and flagged." if flagged and not invented else
        ("Recorded the guessed frequency as fact." if invented else "Missing frequency was not flagged."),
        critical=bool(invented)))

    # 5. Possible mistranscription flagged, not silently corrected.
    boop_flagged = "boop" in flag_text(s["P003"], "possible_mistranscription")
    results.append(result(
        "Mistranscription flagged", "P003", boop_flagged,
        "'boop' flagged for confirmation." if boop_flagged else "'boop' was not flagged as a possible mistranscription."))

    # 6. Late jump-back: Olive's IV access lands on Olive only.
    iv_ok = "iv access" in text["P002"] and "iv access" not in text["P001"] and "iv access" not in text["P003"]
    results.append(result(
        "Late detail attributed to the right patient", "P002", iv_ok,
        "No-IV-access note is on Olive only." if iv_ok else "No-IV-access note missing from Olive or on another patient.",
        critical=not iv_ok))

    # 7. Late jump-back: Rosie's owner visit time.
    visit_ok = re.search(r"\b10\b|10:00|\bten\b", text["P001"]) and not re.search(r"\b10:00\b|around ten", text["P002"])
    results.append(result(
        "Interjection attributed to the right patient", "P001", bool(visit_ok),
        "Owner visit time is on Rosie." if visit_ok else "Owner visit time missing from Rosie or on Olive."))

    # 8. The euthanasia decision, given at the very end.
    euth_ok = "euthanasia" in text["P001"] and re.search(r"elect|decid|go ahead|proceed", text["P001"])
    results.append(result(
        "End-of-rounds decision captured", "P001", bool(euth_ok),
        "Euthanasia decision recorded." if euth_ok else "The owners' euthanasia decision was missed."))

    # 9. Ambiguous "her breathing", resolved as both.
    for pid in ["P001", "P002"]:
        ok = re.search(r"breath|respirat", str(s[pid].get("watch", "")).lower())
        results.append(result("Ambiguous 'her' resolved", pid, bool(ok),
                              "Breathing is in the watch list." if ok else "Breathing missing from the watch list."))

    # 10. Duke's nursing details stay on Duke.
    food_ok = "home-cooked" in text["P003"] and "home-cooked" not in text["P001"] + text["P002"]
    results.append(result("Nursing detail on the right patient", "P003", food_ok,
                          "Home-cooked food note is on Duke only." if food_ok else "Food note missing or misplaced."))

    return results
