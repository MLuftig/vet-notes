"""Step 2: draft owner discharge instructions, with a code check on every medication."""
from records import patients, protocols

MODEL = "claude-sonnet-5"
PLACEHOLDER = "[STAFF TO COMPLETE FROM PRESCRIPTION: frequency]"


# ---------- Tools Claude can call ----------

def format_medication(med):
    line = f"{med['drug']} {med['dose']} {med['route']}"
    line += f" {med['frequency']}" if med["frequency"] else f" {PLACEHOLDER}"
    if med["duration"]:
        line += f" {med['duration']}"
    return line


def get_discharge_orders(patient_id):
    patient = patients.get(patient_id)
    if patient is None:
        return f"No discharge orders on file for {patient_id}."
    orders = patient["orders"]
    med_lines = [f"- {format_medication(m)}" for m in orders["medications"]] or ["- (none)"]
    other_lines = [f"- {o}" for o in orders["other"]] or ["- (none)"]
    text = "MEDICATION LINES (copy each exactly):\n" + "\n".join(med_lines)
    text += "\nOTHER ORDERS:\n" + "\n".join(other_lines)
    return text


def get_clinic_protocol(procedure):
    for key, text in protocols.items():
        if key in procedure.upper():
            return text
    return f"No protocol on file for {procedure}."


def run_tool(name, tool_input):
    if name == "get_discharge_orders":
        return get_discharge_orders(tool_input["patient_id"])
    if name == "get_clinic_protocol":
        return get_clinic_protocol(tool_input["procedure"])
    return f"Unknown tool: {name}"


TOOLS = [
    {
        "name": "get_discharge_orders",
        "description": "Get the doctor's discharge orders for a patient: the exact medication lines and other orders approved by the doctor.",
        "input_schema": {"type": "object", "properties": {"patient_id": {"type": "string"}}, "required": ["patient_id"]},
    },
    {
        "name": "get_clinic_protocol",
        "description": "Get the clinic's standard aftercare protocol for a procedure, such as TPLO.",
        "input_schema": {"type": "object", "properties": {"procedure": {"type": "string"}}, "required": ["procedure"]},
    },
]

SYSTEM_PROMPT = """You draft discharge instructions for a veterinary hospital.
You do not prescribe or make clinical decisions. You report what is in the
record, in plain language for the owner. Your output is a DRAFT for the
doctor to review and approve.

Before drafting, always call get_discharge_orders for the patient and
get_clinic_protocol for the procedure. The doctor's orders come ONLY from
get_discharge_orders. If a tool finds nothing on file, flag it; never guess.

Sources, in order of authority:
1. The doctor's discharge orders.
2. The clinic protocol (standard aftercare only).
3. Anything else in the case summary (for example, staff workarounds).

Medication rules:
- Copy each medication line from get_discharge_orders into the owner
  instructions EXACTLY as written, one per line, with no bold or other
  formatting inside the line. Do not reword, reorder, or add to them.
- Mention no other drugs anywhere in the owner instructions.
- Add no medication advice that is not in the orders (for example, do not
  say "complete the full course").
- Flag every [STAFF TO COMPLETE FROM PRESCRIPTION] line in the staff review.

Protocol rules:
- If the record is silent on aftercare, use the clinic protocol.
- Include EVERY point from each protocol section. You may simplify the
  wording, but never drop or soften a point's meaning.
- If staff actions conflict with the protocol and no doctor order covers
  it, follow the protocol for the owner and flag the conflict.

Never in the owner instructions:
- Anything not in the doctor's orders or the clinic protocol, including
  suggested alternatives such as recovery suits.
- Internal staff notes, opinions about the owners, or closing pleasantries
  based on them.
- References to other paperwork or sections that do not exist.
- Bold text or other emphasis formatting.

Staff review rules:
- Make the first item a one-line summary of the take-home medications
  from the orders, for example: "Take-home medications: gabapentin,
  trazodone." This is a statement, not a question.
- Pain medication check: if the case summary shows pain medication was
  used in the hospital AND the discharge orders contain NO pain medication
  of any kind, flag it. Gabapentin, NSAIDs, and opioids all count as pain
  medication. If ANY pain medication is in the discharge orders, do not
  mention the in-hospital pain drugs at all.
- Carry every transcription flag from the case summary into the staff
  review, so staff can confirm it against the record.

If the patient is going to euthanasia, write no owner instructions and skip
the take-home medication summary and pain check. Instead, write a short staff
note of the decision and flag any missing details, such as time and
location. Under OWNER INSTRUCTIONS, write only: "None: patient going to
euthanasia."

Output exactly two sections:
STAFF REVIEW: a numbered list of every flag, conflict, and protocol default.
OWNER INSTRUCTIONS: clear, plain-language instructions for the owner.
"""


# ---------- The code check ----------

WATCH_LIST = [
    "gabapentin", "trazodone", "carprofen", "rimadyl", "meloxicam",
    "grapiprant", "galliprant", "buprenorphine", "methadone", "fentanyl",
    "hydromorphone", "tramadol", "acepromazine", "amoxicillin", "clavamox",
    "enrofloxacin", "prednisolone", "maropitant", "cerenia", "cephalexin",
    "ampicillin", "sulbactam", "unasyn", "butorphanol",
]


def normalize(text):
    for symbol in ["*", "_", "`"]:
        text = text.replace(symbol, "")
    return " ".join(text.lower().split())


def check_medications(draft, orders):
    meds = orders["medications"]
    if "OWNER INSTRUCTIONS" not in draft:
        if meds:
            return ["No OWNER INSTRUCTIONS section, but medications were ordered."]
        return []
    owner = normalize(draft.split("OWNER INSTRUCTIONS", 1)[1])
    ordered_names = [m["drug"].lower() for m in meds]
    problems = []
    for med in meds:
        if normalize(format_medication(med)) not in owner:
            problems.append(f"Missing or altered medication line: '{format_medication(med)}'")
    for name in WATCH_LIST:
        if name in owner and not any(name in drug for drug in ordered_names):
            problems.append(f"Unordered drug in owner instructions: {name}")
    return problems


# ---------- The agent loop ----------

def draft_discharge(client, patient_id, summary_text, max_steps=8, max_fixes=1):
    """Returns (result_text, passed, log_lines)."""
    orders = patients[patient_id]["orders"]
    log = []
    messages = [{
        "role": "user",
        "content": f"Patient ID: {patient_id}\nCase summary:\n{summary_text}\nDraft discharge instructions.",
    }]
    fixes = 0

    for _ in range(max_steps):
        response = client.messages.create(
            model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    log.append(f"Claude called {block.name} with {block.input}")
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": run_tool(block.name, block.input)})
            messages.append({"role": "user", "content": results})

        elif response.stop_reason == "end_turn":
            draft = "".join(b.text for b in response.content if b.type == "text")
            problems = check_medications(draft, orders)
            if not problems:
                log.append("Medication check: PASSED")
                return draft, True, log
            log.append("Medication check: FAILED")
            log.extend(f"  - {p}" for p in problems)
            if fixes < max_fixes:
                fixes += 1
                log.append("Sending back to Claude to fix...")
                messages.append({"role": "user", "content": "The medication check failed:\n"
                                 + "\n".join(problems) + "\nRewrite the full draft and fix these problems."})
            else:
                return ("BLOCKED: medication check failed after a retry. Not safe to use.\n\n"
                        + "\n".join(problems)), False, log
        else:
            return f"BLOCKED: draft stopped early ({response.stop_reason}). Not safe to use.", False, log

    return "BLOCKED: too many steps without finishing. Not safe to use.", False, log
