"""Look and feel: one paw-print header, legible type, and patient summary cards."""
import html

import streamlit as st

SAGE = "#2F6B5E"
SAGE_DEEP = "#24554A"
INK = "#1C2B27"
MIST = "#EEF4F1"
AMBER_TEXT = "#7A5410"
AMBER_BG = "#FBF3E4"


def paw(size=22, color="currentColor", opacity=1.0, rotate=0):
    """A simple paw print: one main pad and four toes."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true" '
        f'style="width:{size}px;height:{size}px;flex:none;opacity:{opacity};transform:rotate({rotate}deg)">'
        f'<g fill="{color}">'
        '<ellipse cx="12" cy="16" rx="5.2" ry="4.4"/>'
        '<ellipse cx="5.2" cy="10.2" rx="2.1" ry="2.7"/>'
        '<ellipse cx="9.3" cy="6.4" rx="2.1" ry="2.8"/>'
        '<ellipse cx="14.7" cy="6.4" rx="2.1" ry="2.8"/>'
        '<ellipse cx="18.8" cy="10.2" rx="2.1" ry="2.7"/>'
        "</g></svg>"
    )


def paw_trail():
    """Paw prints walking up and across the header, alternating left and right feet."""
    steps = []
    for i in range(7):
        x = 4 + i * 13            # percent across the trail area
        y = 62 - i * 7 + (10 if i % 2 else 0)
        opacity = 0.16 + i * 0.08
        steps.append(
            f'<span style="position:absolute;left:{x}%;top:{y}%">'
            f'{paw(34, "#FFFFFF", round(opacity, 2), 70 + (12 if i % 2 else -12))}</span>'
        )
    return "".join(steps)


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&display=swap');

html, body, p, li, label, input, textarea, button, td, th,
h1, h2, h3, h4, [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{
  font-family: 'Atkinson Hyperlegible', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
textarea {{ font-size: 0.95rem !important; line-height: 1.5 !important; }}

.vn-header {{
  position: relative; overflow: hidden;
  background: {SAGE}; color: #FFFFFF;
  border-radius: 14px; padding: 1.6rem 1.8rem 1.5rem;
  margin: 0.2rem 0 1.4rem;
}}
.vn-header h1 {{
  color: #FFFFFF; font-size: 2rem; font-weight: 700; line-height: 1.15;
  margin: 0 0 0.45rem; padding: 0; max-width: 60%;
}}
.vn-header p {{ color: #E4EFEB; margin: 0; max-width: 58%; font-size: 1.02rem; line-height: 1.5; }}
.vn-header .vn-note {{ margin-top: 0.7rem; font-size: 0.88rem; color: #CFE2DB; }}
.vn-trail {{ position: absolute; right: 0; top: 0; width: 40%; height: 100%; pointer-events: none; }}
@media (max-width: 720px) {{
  .vn-header h1, .vn-header p {{ max-width: 100%; }}
  .vn-trail {{ display: none; }}
}}

.vn-card {{
  border: 1px solid #D5E3DD; border-left: 4px solid {SAGE};
  border-radius: 10px; padding: 1rem 1.2rem 0.9rem; margin-bottom: 1rem; background: #FFFFFF;
}}
.vn-card-head {{ display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.7rem; color: {SAGE}; }}
.vn-card-head strong {{ color: {INK}; font-size: 1.15rem; }}
.vn-card-head span {{ color: #4E615B; }}
.vn-fields {{ display: grid; grid-template-columns: minmax(9rem, max-content) 1fr; gap: 0.35rem 1rem; }}
.vn-label {{ color: #4E615B; font-size: 0.92rem; }}
.vn-value {{ color: {INK}; line-height: 1.45; }}
.vn-flag {{
  background: {AMBER_BG}; color: {AMBER_TEXT}; border-radius: 8px;
  padding: 0.5rem 0.75rem; margin-top: 0.55rem; line-height: 1.45;
}}
.vn-flag q {{ font-style: italic; }}
.vn-footer {{ display: flex; align-items: center; gap: 0.45rem; color: #6A7C76; font-size: 0.85rem; margin-top: 2rem; }}
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)


def header(title, subtitle, note):
    st.markdown(
        f'<div class="vn-header"><h1>{html.escape(title)}</h1>'
        f"<p>{html.escape(subtitle)}</p>"
        f'<p class="vn-note">{html.escape(note)}</p>'
        f'<div class="vn-trail">{paw_trail()}</div></div>',
        unsafe_allow_html=True,
    )


FLAG_NAMES = {
    "uncertain": "Uncertain",
    "possible_mistranscription": "Possible transcription error",
    "conflict": "Conflict",
}


def summary_card(name, description, summary, fields):
    rows = "".join(
        f'<div class="vn-label">{html.escape(label)}</div>'
        f'<div class="vn-value">{html.escape(str(summary.get(key, "Not stated")))}</div>'
        for key, label in fields
    )
    flags = "".join(
        f'<div class="vn-flag"><strong>{html.escape(FLAG_NAMES.get(f.get("type"), "Flag"))}:</strong> '
        f'{html.escape(f.get("detail", ""))}<br>Said: <q>{html.escape(f.get("quote", ""))}</q></div>'
        for f in summary.get("flags", [])
    )
    st.markdown(
        f'<div class="vn-card"><div class="vn-card-head">{paw(22, SAGE)}'
        f"<strong>{html.escape(name)}</strong><span>{html.escape(description)}</span></div>"
        f'<div class="vn-fields">{rows}</div>{flags}</div>',
        unsafe_allow_html=True,
    )


def footer(text):
    st.markdown(f'<div class="vn-footer">{paw(16, "#8FA59E")}<span>{html.escape(text)}</span></div>',
                unsafe_allow_html=True)
