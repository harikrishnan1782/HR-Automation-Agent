"""
============================================================
  streamlit_app.py  —  UI LAYER
  DataPattern Offer Letter Agent

  Pure Streamlit interface. All business logic lives in:
    main.py           — core logic, handlers, HTML builders
    logic.py          — DOCX generation & replacement maps
    mailer.py         — Gmail API sending
    email_template.py — HTML / plain email body builders

  Run with:
    streamlit run streamlit_app.py
============================================================
"""

import time
from pathlib import Path

import streamlit as st

from main import (
    SESSION_DEFAULTS,
    build_dispatch_toast_html,
    load_default_template,
    generate_offer_letter,
    dispatch_offer_email,
    check_system_status,
)


# ════════════════════════════════════════════════════════════
#  TOAST NOTIFICATION
# ════════════════════════════════════════════════════════════
def show_dispatch_toast(candidate_name: str, recipient_email: str) -> None:
    """Renders the animated toast and auto-dismisses after ~4.6 seconds."""
    toast_html = build_dispatch_toast_html(candidate_name, recipient_email)
    _slot = st.empty()
    _slot.markdown(toast_html, unsafe_allow_html=True)
    time.sleep(4.6)
    _slot.empty()


# ════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DataPattern · Offer Letter Agent",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS from external file ─────────────────────────
_CSS_PATH = Path(__file__).parent / "styles.css"
if _CSS_PATH.exists():
    st.markdown(f"<style>{_CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
  header[data-testid="stHeader"] { display: none !important; }
  .block-container { padding-top: 1rem !important; margin-top: 0 !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  TEMPLATE & SESSION STATE
# ════════════════════════════════════════════════════════════
template_bytes = load_default_template()

for _k, _v in SESSION_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:0.3rem 0 0.7rem;">
      <div style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;
                  color:#2a5244;font-weight:600;margin-bottom:4px;">DataPattern</div>
      <div class="brand-name">Offer Letter Agent</div>
      <div class="brand-sub">v3.0 - Gmail API</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:0 0 0.6rem;'>", unsafe_allow_html=True)

    _sent  = st.session_state.emails_sent
    _ready = bool(st.session_state.generated_bytes)
    _lbl   = "Ready"   if _ready else "Waiting"
    _cls   = "ready"   if _ready else "waiting"

    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-mini">
        <div class="sv">{_sent}</div>
        <div class="sl">Emails Sent</div>
      </div>
      <div class="stat-mini {_cls}">
        <div class="sv">{_lbl}</div>
        <div class="sl">Letter</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.66rem;text-transform:uppercase;letter-spacing:0.1em;
                color:#4d7a70;font-weight:700;margin-bottom:0.35rem;">
      Workflow
    </div>
    """, unsafe_allow_html=True)

    _d1 = ""    if _ready                          else "off"
    _d2 = ""    if st.session_state.last_recipient else "off"

    st.markdown(f"""
    <div class="timeline">
      <div class="timeline-item">
        <div class="td {_d1}"></div>
        <div class="tl">Step 1</div>
        <div class="tv">Generate Letter</div>
      </div>
      <div class="timeline-item">
        <div class="td {_d2}"></div>
        <div class="tl">Step 2</div>
        <div class="tv">Dispatch Email</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.last_recipient:
        st.markdown(f"""
        <div class="last-sent">
          <div class="ls-l">Last sent to</div>
          <div class="ls-v">{st.session_state.last_recipient}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:0.85rem 0 0.6rem;'>", unsafe_allow_html=True)

    status = check_system_status(template_bytes)
    _tpl_ok  = status["template_ok"]
    _cred_ok = status["credentials_ok"]

    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:4px;">
      <span class="spill {'ok' if _tpl_ok else 'bad'}">
        {'✓' if _tpl_ok else '✗'} &nbsp;{'Template loaded' if _tpl_ok else 'Template missing'}
      </span>
      <span class="spill {'ok' if _cred_ok else 'bad'}">
        {'✓' if _cred_ok else '✗'} &nbsp;{'Google API ready' if _cred_ok else 'credentials.json missing'}
      </span>
    </div>
    """, unsafe_allow_html=True)

    if not _tpl_ok:
        st.markdown("<div style='margin-top:0.9rem;'>", unsafe_allow_html=True)
        _uploaded = st.file_uploader("Upload template (.docx)", type=["docx"])
        if _uploaded:
            template_bytes = _uploaded.read()
            st.success("Template loaded ✓")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-wrap">
  <div class="hero-title">DataPattern</div>
  <div class="hero-sub">Offer Letter Agent &nbsp;·&nbsp; Generate · Preview · Dispatch — one seamless workflow</div>
</div>
""", unsafe_allow_html=True)

if not template_bytes:
    st.error("⚠️ Template not found. Upload it using the sidebar.")
    st.stop()

tab_gen, tab_send, tab_preview = st.tabs([
    "📝  Generate Letter",
    "📬  Send Email",
    "📋  Preview",
])


# ════════════════════════════════
#  TAB 1 — GENERATE
# ════════════════════════════════
with tab_gen:
    st.markdown("""
    <div class="step-hdr">
      <div class="step-num">1</div>
      <div class="step-hdr-txt">Candidate Details</div>
    </div>
    """, unsafe_allow_html=True)

    ct, cn = st.columns([1, 3])
    with ct: title = st.selectbox("Title", ["Mr.", "Ms.", "Mrs.", "Dr."], key="title")
    with cn: name  = st.text_input("Full Name *", placeholder="e.g. Arjun Sharma", key="cand_name")

    c1, c2 = st.columns(2)
    with c1:
        role         = st.text_input("Role / Designation *", placeholder="e.g. Data Analyst", key="role")
        offer_date   = st.text_input("Offer Date",           placeholder="e.g. 06 Apr 2026",  key="offer_date")
    with c2:
        joining_date = st.text_input("Joining Date",         placeholder="e.g. 01 May 2026",  key="joining_date")

    st.markdown("<br>", unsafe_allow_html=True)
    gc, _, _ = st.columns([2, 1, 1])
    with gc:
        if st.button("⚡  Generate Offer Letter", type="primary", use_container_width=True):
            if not name.strip() or not role.strip():
                st.warning("Please fill in at least Candidate Name and Role.")
            else:
                with st.spinner("Personalising offer letter…"):
                    time.sleep(0.3)
                    result = generate_offer_letter(
                        template_bytes=template_bytes,
                        title=title,
                        name=name,
                        role=role,
                        offer_date=offer_date,
                        joining_date=joining_date,
                    )

                if result["success"]:
                    st.session_state.generated_bytes = result["bytes"]
                    st.session_state.generated_name  = result["filename"]
                    st.session_state["preview_data"] = result["preview_data"]
                    st.success(f"✅ Offer letter ready for **{result['full_name']}**!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Generation failed: {result['error']}")

    if st.session_state.generated_bytes:
        dl, _ = st.columns([2, 1])
        with dl:
            st.download_button(
                label="⬇️  Download Offer Letter (.docx)",
                data=st.session_state.generated_bytes,
                file_name=st.session_state.generated_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="dl_tab1",
            )


# ════════════════════════════════
#  TAB 2 — SEND EMAIL
# ════════════════════════════════
with tab_send:
    st.markdown("""
    <div class="step-hdr">
      <div class="step-num">2</div>
      <div class="step-hdr-txt">Dispatch via Email</div>
    </div>
    """, unsafe_allow_html=True)

    _pd    = st.session_state.get("preview_data", {})
    _cname = _pd.get("Candidate", "Candidate")
    _role  = _pd.get("Role", "the role")

    # ── Attachment Upload ────────────────────────────────────
    st.markdown('<div class="sec-div">Offer Letter Attachment</div>', unsafe_allow_html=True)

    uploaded_docx = st.file_uploader(
        "Upload the Offer Letter (.docx) *",
        type=["docx"],
        key="upload_docx",
        help="Upload the generated offer letter DOCX file to attach it to the email.",
    )

    if uploaded_docx:
        _docx_bytes = uploaded_docx.read()
        _fname      = uploaded_docx.name
        st.success(f"📎 **{_fname}** uploaded and ready to attach.")
    else:
        _docx_bytes = st.session_state.generated_bytes
        _fname      = st.session_state.generated_name or "Offer_Letter.docx"

    # ── Sender Info ──────────────────────────────────────────
    st.markdown('<div class="sec-div">Sender Details</div>', unsafe_allow_html=True)

    sender_email_input = st.text_input(
        "Sender Email *",
        placeholder="e.g. hr@datapattern.ai",
        key="sender_email",
        help="Note: If this doesn't match the Google account you logged in with, Google may overwrite it."
    )

    # ── Recipient fields ─────────────────────────────────────
    st.markdown('<div class="sec-div">Recipient</div>', unsafe_allow_html=True)

    email_input = st.text_input(
        "Recipient Email *",
        placeholder="e.g. arjun.sharma@example.com",
        key="recipient_email",
    )
    cc_input = st.text_input(
        "CC (optional — comma-separated)",
        placeholder="e.g. hr-head@datapattern.ai, ceo@datapattern.ai",
        key="cc_email",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    sc, _ = st.columns([2, 1])
    with sc:
        if st.button("🚀  Send Offer Email", type="primary", use_container_width=True):
            with st.spinner("Connecting to Gmail API…"):
                res = dispatch_offer_email(
                    docx_bytes      = _docx_bytes,
                    filename        = _fname,
                    sender_email    = sender_email_input,
                    recipient_email = email_input,
                    cc_email        = cc_input,
                    candidate_name  = _cname,
                    role            = _role,
                )

            if res["success"]:
                st.session_state.emails_sent   += 1
                st.session_state.last_recipient = email_input.strip()
                show_dispatch_toast(_cname, email_input.strip())
                st.rerun()
            else:
                st.error(f"❌ {res['message']}")

        st.markdown("<hr style='margin:1.2rem 0;'>", unsafe_allow_html=True)

        with st.expander("👁️  Preview email that will be sent"):
            st.markdown(f"""
**From:** `DataPattern HR <{sender_email_input if sender_email_input else '—'}>`
**To:** `{email_input if email_input else '—'}`
**CC:** `{cc_input if cc_input else '—'}`
**Subject:** `Offer Letter — {_role} at DataPattern`
**Attachment:** `{_fname if _docx_bytes else '—'}`

---

*Dear {_cname},*

We are pleased to offer you the position of **{_role}** at DataPattern.
Your official Offer Letter is attached.

**Next steps:**
- Review and sign your offer letter
- Complete the onboarding checklist
- Contact HR for any queries

*Warm regards,
HR Team — DataPattern*
            """)


# ════════════════════════════════
#  TAB 3 — PREVIEW
# ════════════════════════════════
with tab_preview:
    st.markdown("""
    <div class="step-hdr">
      <div class="step-num">📋</div>
      <div class="step-hdr-txt">Offer Summary</div>
    </div>
    """, unsafe_allow_html=True)

    _data = st.session_state.get("preview_data")
    if not _data:
        st.info("No letter generated yet. Fill the form in the Generate tab first.")
    else:
        _rows = "".join(
            f"<div class='pv-row'>"
            f"<span class='pv-lbl'>{k}</span>"
            f"<span class='pv-val'>{v}</span>"
            f"</div>"
            for k, v in _data.items()
        )
        st.markdown(f"<div class='pv-card'>{_rows}</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="dispatch-badge">
          <div class="dispatch-icon">✅</div>
          <div class="dispatch-title">Letter is ready to dispatch</div>
          <div class="dispatch-hint">
            Head to the <strong>Send Email</strong> tab to deliver it.
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.generated_bytes:
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️  Download Offer Letter (.docx)",
                data=st.session_state.generated_bytes,
                file_name=st.session_state.generated_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="dl_tab3",
            )