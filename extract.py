"""Step 1: turn a recorded rounds conversation into per-patient handoff summaries."""
import json

from records import patients

MODEL = "claude-sonnet-5"

FIELDS = [
    ("signalment", "Who"),
    ("why_presented", "Why presented"),
    ("changes", "Changes while here"),
    ("meds_started", "Meds started"),
    ("dose_changes", "Dose changes"),
    ("meds_stopped", "Meds stopped"),
    ("plan", "Plan"),
    ("watch", "Watch"),
    ("pending", "Pending"),
    ("code_status", "Code status"),
]


def census_text():
    return "\n".join(f"- {pid}: {p['name']}, {p['description']}" for pid, p in patients.items())


EXTRACTION_PROMPT = """You turn a recorded veterinary rounds conversation into
handoff summaries, one per patient. The recording came from speech-to-text:
there are no speaker labels, speakers change at line breaks, and words may be
mistranscribed.

Patients on today's census:
{census}

Attribution rules:
- The conversation jumps between patients ("oh wait, back to the cat").
  Attribute every statement to the patient it is about, using names, species,
  breed, pronouns, and context. A statement belongs to the patient it is
  about, not the patient being discussed when it was said.
- If a statement is about a patient not on the census, or you cannot tell
  which patient it is about, put it in "unattributed". Never guess.

Content rules:
- Record only what was said. Never add details that were not said.
- Use generic drug names (Clavamox = amoxicillin-clavulanate, enro =
  enrofloxacin, pred = prednisolone, Unasyn = ampicillin-sulbactam,
  bupe = buprenorphine, gaba = gabapentin, traz = trazodone,
  ace = acepromazine). Keep doses exactly as stated.
- Hedged statements ("I think", "I wanna say", "don't quote me",
  "something like that"): record them as stated and add an "uncertain" flag
  quoting the words. If a later statement confirms or settles it, use the
  confirmed version and do not flag it.
- If statements conflict, a statement from someone who writes the orders
  (for example "I didn't write a frequency yet") outranks a guess. Flag any
  conflict that remains.
- A word that is not a real drug name or shorthand but sounds like one is a
  possible speech-to-text error. Write the likely term with the original in
  quotes, for example: buprenorphine (transcribed as "boop"), and add a
  "possible_mistranscription" flag. Never correct one silently.
- If something was not said, write "Not stated".

Respond with JSON only, no other text, in exactly this shape:
{{
  "patients": [
    {{
      "patient_id": "P001",
      "signalment": "...",
      "why_presented": "...",
      "changes": "...",
      "meds_started": "...",
      "dose_changes": "...",
      "meds_stopped": "...",
      "plan": "...",
      "watch": "...",
      "pending": "...",
      "code_status": "...",
      "flags": [
        {{"type": "uncertain | possible_mistranscription | conflict",
          "detail": "...", "quote": "exact words from the transcript"}}
      ]
    }}
  ],
  "unattributed": [
    {{"quote": "exact words", "reason": "..."}}
  ]
}}
"""


def parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in the response.")
    return json.loads(text[start:end + 1])


def extract_summaries(client, transcript, max_attempts=2):
    """Returns {"patients": {patient_id: summary_dict}, "unattributed": [...]}."""
    prompt = EXTRACTION_PROMPT.format(census=census_text())
    last_error = None
    for _ in range(max_attempts):
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=prompt,
            messages=[{"role": "user", "content": f"Rounds transcript:\n\n{transcript}"}],
        )
        if response.stop_reason == "max_tokens":
            last_error = "The response was cut off before it finished."
            continue
        text = "".join(b.text for b in response.content if b.type == "text")
        try:
            data = parse_json(text)
        except (ValueError, json.JSONDecodeError) as e:
            last_error = f"The response was not valid JSON ({e})."
            continue
        by_id = {}
        for p in data.get("patients", []):
            pid = p.get("patient_id")
            if pid in patients:
                p.setdefault("flags", [])
                by_id[pid] = p
        return {"patients": by_id, "unattributed": data.get("unattributed", [])}
    raise RuntimeError(f"Extraction failed: {last_error}")


def summary_to_text(summary):
    """Render a structured summary in the handoff template, flags included."""
    lines = [f"{label}: {summary.get(key, 'Not stated')}" for key, label in FIELDS]
    flags = summary.get("flags", [])
    if flags:
        lines.append("Transcription flags (from the rounds recording):")
        for f in flags:
            lines.append(f"- {f.get('type', 'flag')}: {f.get('detail', '')} (said: \"{f.get('quote', '')}\")")
    return "\n".join(lines)
