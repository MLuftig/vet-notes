"""Fictional hospital records. No real patient data is used anywhere in this project."""

# The census: patients currently in the hospital, with the doctor's discharge orders.
patients = {
    "P001": {
        "name": "Rosie",
        "description": "11-year-old female spayed Boxer",
        "procedure": "TRACHEOSTOMY",
        "orders": {"medications": [], "other": []},
    },
    "P002": {
        "name": "Olive",
        "description": "9-year-old female spayed DLH cat",
        "procedure": "PNEUMONIA",
        "orders": {
            "medications": [
                {"drug": "Amoxicillin-clavulanate", "dose": "62.5 mg", "route": "by mouth",
                 "frequency": "every 12 hours", "duration": "for 14 days"},
                {"drug": "Enrofloxacin", "dose": "22.7 mg", "route": "by mouth",
                 "frequency": "every 24 hours", "duration": "for 14 days"},
                {"drug": "Prednisolone", "dose": "5 mg", "route": "by mouth",
                 "frequency": "every 24 hours", "duration": "for 7 days"},
            ],
            "other": [],
        },
    },
    "P003": {
        "name": "Duke",
        "description": "3-year-old male neutered Great Dane",
        "procedure": "TPLO",
        "orders": {
            "medications": [
                {"drug": "Gabapentin", "dose": "600 mg", "route": "by mouth",
                 "frequency": "every 8 hours", "duration": "for 14 days"},
                {"drug": "Trazodone", "dose": "300 mg", "route": "by mouth",
                 "frequency": None, "duration": None},
            ],
            "other": ["Remove IV catheter prior to discharge"],
        },
    },
}

protocols = {
    "TPLO": """
HARBORVIEW VETERINARY SURGERY CENTER (FICTIONAL) - STANDARD TPLO AFTERCARE
Applies unless the doctor specifies otherwise.
ACTIVITY: Weeks 0-2 strict confinement; leash walks for bathroom breaks only,
5-10 minutes, 3-4 times daily. Weeks 2-8 leash walks may increase about
5 minutes per week. No running, jumping, stairs, rough play, or off-leash
activity until cleared at the 8-week recheck.
INCISION: Check twice daily for redness, swelling, discharge, or odor. No
bathing or swimming until cleared. E-collar at all times when unsupervised
until suture removal, unless the doctor documents an alternative.
FOLLOW-UP: Recheck and suture removal in 10-14 days. Radiographs at 8 weeks.
CALL IMMEDIATELY IF: sudden non-weight-bearing on the operated leg; incision
opens, bleeds, or drains; pain not controlled by prescribed medications;
vomiting, diarrhea, or refusal to eat for more than 24 hours.
CONTACT: Clinic (555) 010-0100. After-hours (555) 010-0199.
""",
    "PNEUMONIA": """
HARBORVIEW VETERINARY SURGERY CENTER (FICTIONAL) - STANDARD PNEUMONIA AFTERCARE
Applies unless the doctor specifies otherwise.
ACTIVITY: Keep indoors and quiet. Limit activity until the recheck.
BREATHING: Twice daily, count breaths per minute while your pet is resting
or asleep. Call if it is more than 40 breaths per minute.
FOLLOW-UP: Recheck exam and chest radiographs in 10-14 days.
CALL IMMEDIATELY IF: labored, rapid, or open-mouth breathing; blue or pale
gums; collapse; not eating for more than 24 hours.
CONTACT: Clinic (555) 010-0100. After-hours (555) 010-0199.
""",
}

# Answer keys: the handoff summaries a credentialed technician would write
# from the rounds recording in data/rounds_transcript.txt.
answer_keys = {
    "P001": """
Who: Rosie, 11-year-old female spayed Boxer
Why presented: Presented three days ago for episodic noisy breathing. Diagnosed
with a laryngeal mass (suspect carcinoma). Temporary tracheostomy placed after
poor recovery from biopsy yesterday.
Changes while here: Episode of respiratory distress yesterday afternoon
(panting, restless, temp approximately 103.8F), improved after a bandage
compressing the trach site was loosened. Overnight stable: up, walking,
drinking, ate a small amount. Agitated with stimulation, especially owner
visits; settles with acepromazine.
Meds started: Acepromazine PRN for agitation.
Dose changes: none
Meds stopped: Fentanyl CRI briefly discontinued yesterday, then restarted.
Plan: Fentanyl CRI nearly finished; let it run out and monitor, no oral pain
meds. Owners may visit around 10:00. Goals of care discussed (permanent trach
vs. euthanasia); owners spoke with the doctor around 06:00 and elected to
proceed with euthanasia. May offer different foods.
Watch: Respiratory status.
Pending: none
Code status: DNR
""",
    "P002": """
Who: Olive, 9-year-old female spayed DLH
Why presented: Coughing, increased respiratory effort, inappetence. History of
recurrent pleural effusion. Radiographs consistent with aspiration pneumonia.
Changes while here: Weaned off oxygen around midnight; much brighter, eating
and drinking.
Meds started: Transitioned to oral amoxicillin-clavulanate, enrofloxacin,
prednisolone.
Dose changes: none
Meds stopped: Ampicillin-sulbactam, butorphanol.
Plan: Discharge today if she continues to improve. No IV access (both
cephalic catheters lost, saphenous veins poor); doctor elected not to replace
since she is taking all medications by mouth. Owners may call about further
workup for the effusion.
Watch: Respiratory status.
Pending: none
Code status: CPR
""",
    "P003": """
Who: Duke, 3-year-old male neutered Great Dane
Why presented: Post-op care following right TPLO yesterday. History of
bilateral hip dysplasia and a left TPLO earlier this year.
Changes while here: Very vocal post-op; settled and ate after pain/sedation
protocol adjusted. Became agitated with e-collar, which was removed.
Meds started: Gabapentin 600 mg, trazodone 300 mg, methadone; fentanyl
switched to buprenorphine.
Dose changes: Initial post-op protocol insufficient; changed as above.
Meds stopped: Fentanyl.
Plan: Discharge this morning. Buprenorphine due 08:00, moved to 09:00 pending
discharge time. Remove IV catheter before discharge. Trazodone frequency not
yet written; confirm from the prescription. Owners brought home-cooked food,
in a labeled container in the treatment-room fridge.
Watch: Pain and anxiety prior to discharge.
Pending: none
Code status: CPR
""",
}

# Drugs each patient's summary should mention, used to grade attribution.
expected_drugs = {
    "P001": {"acepromazine", "fentanyl"},
    "P002": {"amoxicillin-clavulanate", "enrofloxacin", "prednisolone",
             "ampicillin-sulbactam", "butorphanol"},
    "P003": {"gabapentin", "trazodone", "methadone", "fentanyl", "buprenorphine"},
}

expected_code_status = {"P001": "DNR", "P002": "CPR", "P003": "CPR"}
