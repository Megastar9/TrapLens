"""TrapLens: a Streamlit scam education dashboard."""
import hashlib
import html
import os

import streamlit as st
from highlighting import highlighting_html
from analyzer import AnalysisError, MAX_TEXT, analyze_message, prepare_image

st.set_page_config(page_title="TrapLens · Think Before You Click", page_icon="◈", layout="wide")
st.markdown("""<style>
.block-container {max-width:1180px;padding-top:2.4rem;padding-bottom:2rem}
header[data-testid="stHeader"] {background:transparent}
.stApp {background:radial-gradient(ellipse at 85% 0%,#16302c 0%,#0b1017 47%)}
h1,h2,h3 {letter-spacing:-.04em} h1 {font-size:clamp(2.8rem,6vw,4.6rem)!important;line-height:1.07!important}
p {line-height:1.65} .eyebrow {color:#93f5c5;font-size:.74rem;font-weight:700;letter-spacing:.17em;text-transform:uppercase}
.nav {display:flex;justify-content:space-between;align-items:center;margin-bottom:3rem;color:#a1afbf;font-size:.8rem}
.brand {font-size:1.35rem;font-weight:800;color:#edf3f8;letter-spacing:-.04em}
.brand span {color:#93f5c5}.pill {border:1px solid #315346;border-radius:30px;padding:6px 13px;color:#acf4d0;background:#14271f}
.intro {font-size:1.06rem;color:#a6b5c6;max-width:610px;margin-bottom:2rem}
.card {border:1px solid #293748;border-radius:16px;padding:24px;background:#111b26;margin-bottom:16px}
.quiet {color:#a6b5c6;font-size:.87rem}.quote {border-left:3px solid #93f5c5;padding:12px 16px;background:#192b2c;border-radius:0 8px 8px 0;white-space:pre-wrap;overflow-wrap:anywhere;color:#d4f7e7;margin:15px 0}
.card h3 {margin:0;font-size:1.13rem}.card p {margin-bottom:0;overflow-wrap:anywhere}
.score {font-size:2.2rem;font-weight:750;letter-spacing:-.045em}.step {color:#93f5c5;font-weight:700;font-size:.8rem}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px}
.stButton>button {border-radius:10px;min-height:44px} .stButton>button[kind="primary"] {font-weight:750;color:#092319}
footer {visibility:hidden}
@media(max-width:640px){.block-container{padding-top:1.5rem}.nav{margin-bottom:1.5rem}.pill{font-size:.65rem}.card{padding:18px}}
</style>""", unsafe_allow_html=True)

EXAMPLES = {
    "📦  Delivery alert": "Delivery failed: your package is on hold. Pay the $1.99 redelivery fee within 2 hours at https://parcel-redelivery.example or your parcel will be returned. Enter your card details to confirm.",
    "🏦  Account warning": "BANK SECURITY: Your account will be frozen in 30 minutes. Reply with your password and the 6-digit verification code we just sent. Do not call the bank; our phone lines are compromised.",
    "☕  Everyday message": "Hey! Are we still meeting at the campus cafe at 3? Let me know if you need to reschedule.",
}


def choose_example(message):
    st.session_state.message = message
    st.session_state.upload_version = st.session_state.get("upload_version", 0) + 1
    st.session_state.pop("result", None)


def clear():
    st.session_state.message = ""
    st.session_state.upload_version = st.session_state.get("upload_version", 0) + 1
    st.session_state.pop("result", None)


def safe(value):
    return html.escape(str(value))


st.markdown('<div class="nav"><div class="brand"><span>◈</span> TrapLens</div><div class="pill">Powered by Google Gemma 4</div></div>', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">A second look. A smarter next step.</div>', unsafe_allow_html=True)
st.title("Think Before You Click.")
st.markdown('<p class="intro">Scams play on instinct. Give yourself a moment.<br>Uncover the warning signs in messages, emails, and DMs—with evidence you can understand.</p>', unsafe_allow_html=True)

left, right = st.columns([1.55, 1], gap="large")
with left:
    with st.container(border=True):
        st.markdown('<span class="eyebrow">01 / Inspect a message</span>', unsafe_allow_html=True)
        st.subheader("Something feel off?")
        text = st.text_area("Paste the message", key="message", height=190, max_chars=MAX_TEXT,
                            placeholder="Paste a suspicious text, email, or DM here…")
        uploaded = st.file_uploader("Or add a screenshot", type=["png", "jpg", "jpeg", "webp"],
                                    key=f"upload_{st.session_state.get('upload_version', 0)}",
                                    help="PNG, JPEG, or WebP · up to 8 MB. Crop out private information first.")
        image_bytes = uploaded.getvalue() if uploaded else None
        image_error = None
        if uploaded:
            try:
                preview, _ = prepare_image(image_bytes)
                st.image(preview, caption="Your screenshot · sent only when you analyze", width=280)
            except AnalysisError as exc:
                image_error = str(exc)
                st.error(image_error)
        st.caption("Your submission is sent to Google for analysis. Remove passwords, codes, and personal details first. TrapLens does not save submissions to a database.")
        go, reset = st.columns([3, 1])
        analyze = go.button("Analyze Message  →", type="primary", use_container_width=True)
        reset.button("Clear", on_click=clear, use_container_width=True)
        if not os.environ.get("GEMINI_API_KEY", "").strip():
            st.info("One-time setup: set GEMINI_API_KEY in your terminal before launching. Instructions are in README.md.")
    st.caption("TRY AN EXAMPLE · These are sample inputs, not precomputed results.")
    for label, message in EXAMPLES.items():
        st.button(label, on_click=choose_example, args=(message,), use_container_width=True)
with right:
    st.markdown('''<div class="card"><span class="eyebrow">More than a verdict</span><h3 style="margin-top:12px">Understand the playbook.</h3><p class="quiet">Learn what a message is asking you to do—and how it might be trying to pressure you.</p><hr style="border-color:#293748"><p><span class="step">01 &nbsp; SPOT</span><br>Urgency, impersonation, and unusual requests.</p><p><span class="step">02 &nbsp; UNDERSTAND</span><br>Exact phrases. Clear explanations.</p><p><span class="step">03 &nbsp; ACT</span><br>Practical steps to stay in control.</p></div><div class="card"><h3>Pause. Verify independently.</h3><p class="quiet">An AI assessment is a starting point. TrapLens does not open links or verify the sender. A low-risk result is never a guarantee of safety.</p></div>''', unsafe_allow_html=True)

fingerprint = hashlib.sha256(text.encode() + b"\0" + (image_bytes or b"")).hexdigest()
if analyze:
    st.session_state.pop("result", None)
    try:
        if image_error:
            raise AnalysisError(image_error)
        with st.spinner("Gemma is examining the message and tracing the evidence…"):
            result = analyze_message(text, image_bytes)
        st.session_state.result = (fingerprint, result)
    except AnalysisError as exc:
        st.error(str(exc))

stored = st.session_state.get("result")
if stored and stored[0] != fingerprint:
    st.info("Your input changed. Analyze again to get an assessment of the current message.")
elif stored:
    result = stored[1]
    st.divider()
    st.markdown('<span class="eyebrow">02 / Your analysis</span>', unsafe_allow_html=True)
    st.header("A closer look")
    colors = {"Low": "#93f5c5", "Medium": "#f5cb78", "High": "#ff9797", "Uncertain": "#b8adff"}
    a, b = st.columns([1, 2])
    with a:
        st.markdown(f'<div class="card"><span class="quiet">CONTENT RISK</span><div class="score" style="color:{colors[result.risk_level]}">{safe(result.risk_level)}</div><p class="quiet">{len(result.red_flags)} evidence-backed warning signs<br>No websites or identities verified.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="card"><h3>What Gemma noticed</h3><p>{safe(result.summary)}</p></div>', unsafe_allow_html=True)
    evidence, actions = st.columns([1.5, 1], gap="large")
    with evidence:
        st.subheader("Evidence Mode")
        st.caption("Select a highlighted phrase to explore its warning signs.")
        if text.strip():
            st.iframe(highlighting_html(text, result.red_flags, "text"), height="content", alt="Interactive message evidence")
        if result.image_transcription:
            st.caption("Screenshot highlights use Gemma's transcription. Compare it with your image.")
            st.iframe(highlighting_html(result.image_transcription, result.red_flags, "image"), height="content", alt="Interactive screenshot transcription evidence")
        if not result.red_flags:
            st.info("No specific warning signs were identified. This does not establish that the message is authentic.")
        for i, flag in enumerate(result.red_flags, 1):
            label = "Exact match in pasted text" if flag.source == "text" else "AI-transcribed screenshot · check against your image"
            st.markdown(f'<div class="card"><span class="eyebrow">SIGN {i:02d}</span><h3>{safe(flag.title)}</h3><div class="quote">“{safe(flag.quote)}”</div><div class="quiet">{label}</div><p>{safe(flag.explanation)}</p></div>', unsafe_allow_html=True)
    with actions:
        st.subheader("Your next steps")
        for i, action in enumerate(result.recommended_actions, 1):
            st.markdown(f'<div class="card"><span class="step">{i:02d}</span><p>{safe(action)}</p></div>', unsafe_allow_html=True)
    with st.expander("Limits of this assessment", expanded=result.risk_level == "Uncertain"):
        st.text(result.limitations)
        st.caption("AI can make mistakes. Text quotes are checked against your input; screenshot quotes are checked against Gemma's transcription, not independently verified OCR.")
    if result.image_transcription:
        with st.expander("Read the screenshot transcription"):
            st.caption("AI-generated transcription. Compare it with your screenshot before relying on it.")
            st.text(result.image_transcription)
    st.download_button("Download analysis · JSON", result.model_dump_json(indent=2), "traplens-analysis.json", "application/json")
st.divider()
st.caption("◈ TrapLens  ·  Think Before You Click.    |    Built for awareness. Designed to explain.")
