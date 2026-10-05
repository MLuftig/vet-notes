"""Discharge drafting assistant: rounds recording -> handoff summaries -> discharge drafts."""
import os
from pathlib import Path

import anthropic
import pandas as pd
import streamlit as st

from agent import draft_discharge
from extract import FIELDS, extract_summaries, summary_to_text
from grade import grade
from records import answer_keys, patients

st.set_page_config(page_title="Discharge drafting assistant", page_icon="🩺", layout="wide")

TRANSCRIPT = (Path(__file__).parent / "data" / "rounds_transcript.txt").read_text()


def secret(name):
    try:
        return st.secrets.get(name) or os.environ.get(name)
    except Exception:  # no secrets file when running locally
        return os.environ.get(name)


def password_ok():
    password = secret("APP_PASSWORD")
    if not password or st.session_state.get("authed"):
        return True
    entered = st.text_input("Enter the demo password to continue", type="password")
    if entered == password:
        st.session_state.authed = True
        st.rerun()
    elif entered:
        st.error("That password is incorrect.")
    return False


st.title("Discharge drafting assistant")
st.write(
    "Turns a recorded rounds conversation into handoff summaries, then drafts owner "
    "discharge instructions for the doctor to review. Every patient, order, and protocol "
    "here is fictional."
)

if not password_ok():
    st.stop()

api_key = secret("ANTHROPIC_API_KEY")
if not api_key:
    st.error("No API key found. Add ANTHROPIC_API_KEY to the app's secrets to run it.")
    st.stop()
client = anthropic.Anthropic(api_key=api_key)

state = st.session_state
state.setdefault("extraction", None)
state.setdefault("drafts", {})

tab_rec, tab_sum, tab_dc, tab_acc = st.tabs(
    ["1. Rounds recording", "2. Handoff summaries", "3. Discharge drafts", "4. Accuracy check"]
)

# ---------- 1. Rounds recording ----------
with tab_rec:
    st.write(
        "A speech-to-text transcript of morning rounds. There are no speaker labels, the "
        "conversation jumps between patients, and some words are mistranscribed."
    )
    transcript = st.text_area("Transcript", TRANSCRIPT, height=420)
    if st.button("Extract handoff summaries", type="primary"):
        with st.spinner("Sorting statements by patient and filling in summaries..."):
            try:
                state.extraction = extract_summaries(client, transcript)
                state.drafts = {}
                st.success("Summaries extracted. Open the next tab to review them.")
            except Exception as e:
                st.error(f"Extraction stopped: {e}")

# ---------- 2. Handoff summaries ----------
with tab_sum:
    if not state.extraction:
        st.info("Extract summaries from the rounds recording first.")
    else:
        for pid, patient in patients.items():
            summary = state.extraction["patients"].get(pid)
            with st.expander(f"{patient['name']}: {patient['description']}", expanded=True):
                if not summary:
                    st.error("No summary was produced for this patient.")
                    continue
                for key, label in FIELDS:
                    st.markdown(f"**{label}:** {summary.get(key, 'Not stated')}")
                for flag in summary.get("flags", []):
                    st.warning(f"{flag.get('type', 'flag').replace('_', ' ').capitalize()}: "
                               f"{flag.get('detail', '')}  \nSaid: \u201c{flag.get('quote', '')}\u201d")
        unattributed = state.extraction.get("unattributed", [])
        if unattributed:
            st.subheader("Statements not matched to a patient")
            for item in unattributed:
                st.info(f"\u201c{item.get('quote', '')}\u201d  \n{item.get('reason', '')}")

# ---------- 3. Discharge drafts ----------
with tab_dc:
    source = st.radio(
        "Write the draft from",
        ["The summary extracted from the recording", "The technician-written summary"],
        horizontal=True,
    )
    choice = st.selectbox("Patient", list(patients), format_func=lambda p: patients[p]["name"])
    if st.button("Draft discharge instructions", type="primary"):
        if source.startswith("The summary extracted") and not state.extraction:
            st.error("Extract summaries from the rounds recording first, or switch to the technician-written summary.")
        else:
            if source.startswith("The summary extracted"):
                summary = state.extraction["patients"].get(choice)
                summary_text = summary_to_text(summary) if summary else ""
            else:
                summary_text = answer_keys[choice]
            if not summary_text:
                st.error("There is no summary for this patient to draft from.")
            else:
                with st.spinner("Fetching orders and protocol, drafting, and checking medications..."):
                    try:
                        state.drafts[choice] = draft_discharge(client, choice, summary_text)
                    except Exception as e:
                        st.error(f"Drafting stopped: {e}")

    if choice in state.drafts:
        result, passed, log = state.drafts[choice]
        with st.expander("Agent steps", expanded=False):
            st.code("\n".join(log), language=None)
        if passed:
            st.success("Medication check passed. This is a draft for the doctor to review and approve.")
            st.markdown(result)
        else:
            st.error(result)

# ---------- 4. Accuracy check ----------
with tab_acc:
    st.write(
        "Grades the extracted summaries against summaries written by a credentialed veterinary "
        "technician from the same recording. A critical error is a fact on the wrong patient or "
        "an unconfirmed detail recorded as fact."
    )
    if not state.extraction:
        st.info("Extract summaries from the rounds recording first.")
    elif st.button("Grade the summaries", type="primary"):
        results = grade(state.extraction)
        passed = sum(r["Result"] == "Pass" for r in results)
        critical = sum(r["Critical"] == "Yes" and r["Result"] == "FAIL" for r in results)
        c1, c2 = st.columns(2)
        c1.metric("Tests passed", f"{passed} of {len(results)}")
        c2.metric("Critical errors", critical)
        st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)
