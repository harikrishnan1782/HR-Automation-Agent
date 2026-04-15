"""
============================================================
  main.py  —  CORE APPLICATION LOGIC
  DataPattern Offer Letter Agent

  Contains all non-UI business logic:
    - Toast notification HTML builder
    - Template loading
    - Session state initialization
    - Offer letter generation handler
    - Email dispatch handler

  Dependencies:
    logic.py          — DOCX generation & replacement maps
    mailer.py         — Gmail API sending
    email_template.py — HTML / plain email body builders

  Entry point:
    streamlit run streamlit_app.py
============================================================
"""

import os
import logging
import time
from pathlib import Path

os.environ["STREAMLIT_LOGGER_LEVEL"] = "error"
logging.getLogger("streamlit").setLevel(logging.ERROR)

# ── Internal modules ──────────────────────────────────────
from logic  import fill_offer_letter, build_replacements
from mailer import send_offer_email, is_valid_email


# ── Constants ─────────────────────────────────────────────
TEMPLATE_NAME    = "DataPattern Offer Letter_sample.docx"
DEFAULT_TEMPLATE = Path(__file__).parent / TEMPLATE_NAME

SESSION_DEFAULTS = {
    "generated_bytes": None,
    "generated_name":  "",
    "emails_sent":     0,
    "last_recipient":  "",
    "preview_data":    {},
}


# ════════════════════════════════════════════════════════════
#  TOAST HTML BUILDER
# ════════════════════════════════════════════════════════════
def build_dispatch_toast_html(candidate_name: str, recipient_email: str) -> str:
    """
    Returns the HTML string for a branded, animated toast notification
    confirming the email was dispatched. Auto-dismisses after 4 seconds
    via CSS animation.
    """
    return f"""
    <style>
      @keyframes dp-slide-in {{
        from {{ transform: translateX(120%); opacity: 0; }}
        to   {{ transform: translateX(0);   opacity: 1; }}
      }}
      @keyframes dp-fade-out {{
        0%   {{ opacity: 1; }}
        80%  {{ opacity: 1; }}
        100% {{ opacity: 0; transform: translateX(120%); }}
      }}
      .dp-toast-wrap {{
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 9999;
        animation: dp-slide-in 0.45s cubic-bezier(0.22,1,0.36,1) forwards,
                   dp-fade-out 4s ease-in-out 0.5s forwards;
        pointer-events: none;
      }}
      .dp-toast {{
        display: flex;
        align-items: flex-start;
        gap: 14px;
        background: #ffffff;
        border-left: 5px solid #2a7a5e;
        border-radius: 10px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.14), 0 2px 8px rgba(42,122,94,0.10);
        padding: 16px 22px 16px 18px;
        min-width: 320px;
        max-width: 400px;
      }}
      .dp-toast-icon {{
        flex-shrink: 0;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2a7a5e, #3aaf82);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        color: #fff;
        box-shadow: 0 2px 8px rgba(42,122,94,0.25);
      }}
      .dp-toast-body {{
        display: flex;
        flex-direction: column;
        gap: 3px;
      }}
      .dp-toast-title {{
        font-size: 0.88rem;
        font-weight: 700;
        color: #1a3a2e;
        letter-spacing: 0.01em;
        margin: 0;
      }}
      .dp-toast-sub {{
        font-size: 0.78rem;
        color: #4a6860;
        margin: 0;
        line-height: 1.5;
      }}
      .dp-toast-meta {{
        font-size: 0.72rem;
        color: #8aab9e;
        margin: 4px 0 0;
        letter-spacing: 0.02em;
      }}
    </style>

    <div class="dp-toast-wrap">
      <div class="dp-toast">
        <div class="dp-toast-icon">✓</div>
        <div class="dp-toast-body">
          <p class="dp-toast-title">Offer Letter Dispatched</p>
          <p class="dp-toast-sub">
            Sent to <strong>{candidate_name}</strong>
          </p>
          <p class="dp-toast-meta">📧 {recipient_email} &nbsp;·&nbsp; via Gmail API</p>
        </div>
      </div>
    </div>
    """


# ════════════════════════════════════════════════════════════
#  TEMPLATE LOADER
# ════════════════════════════════════════════════════════════
def load_default_template() -> bytes | None:
    """Loads the default offer letter template bytes, or None if not found."""
    if DEFAULT_TEMPLATE.exists():
        return DEFAULT_TEMPLATE.read_bytes()
    return None


# ════════════════════════════════════════════════════════════
#  OFFER LETTER GENERATION
# ════════════════════════════════════════════════════════════
def generate_offer_letter(
    template_bytes: bytes,
    title: str,
    name: str,
    role: str,
    offer_date: str,
    joining_date: str,
    location: str = "",
    phone: str = "",
    address: str = "",
    hr_name: str = "HR Team",
    hr_dept: str = "Human Resources",
) -> dict:
    """
    Builds the replacement map and fills the offer letter template.

    Returns a dict with:
        success (bool)
        bytes   (bytes | None)   — filled DOCX bytes on success
        filename (str)           — suggested download filename
        full_name (str)          — formatted candidate name
        preview_data (dict)      — summary fields for the Preview tab
        error (str | None)       — error message on failure
    """
    full_name, reps = build_replacements(
        title, name, role, location,
        phone, address, offer_date,
        joining_date, hr_name, hr_dept,
    )
    try:
        result_bytes = fill_offer_letter(template_bytes, reps)
        safe_name    = name.strip().replace(" ", "_")
        fname        = f"Offer_Letter_{safe_name}.docx"
        preview      = {
            "Candidate":    full_name,
            "Role":         role.strip(),
            "Offer Date":   offer_date.strip()   or "—",
            "Joining Date": joining_date.strip() or "—",
        }
        return {
            "success":      True,
            "bytes":        result_bytes,
            "filename":     fname,
            "full_name":    full_name,
            "preview_data": preview,
            "error":        None,
        }
    except Exception as e:
        return {
            "success":      False,
            "bytes":        None,
            "filename":     "",
            "full_name":    full_name,
            "preview_data": {},
            "error":        str(e),
        }


# ════════════════════════════════════════════════════════════
#  EMAIL DISPATCH
# ════════════════════════════════════════════════════════════
def dispatch_offer_email(
    docx_bytes: bytes,
    filename: str,
    sender_email: str,
    recipient_email: str,
    cc_email: str,
    candidate_name: str,
    role: str,
) -> dict:
    """
    Validates inputs and sends the offer letter via Gmail API.

    Returns the result dict from send_offer_email:
        { "success": bool, "message": str }
    """
    # Pre-flight validation
    if not docx_bytes:
        return {"success": False, "message": "No offer letter attachment provided."}
    if not sender_email.strip():
        return {"success": False, "message": "Sender email is required."}
    if not recipient_email.strip():
        return {"success": False, "message": "Recipient email is required."}
    if not os.path.exists("credentials.json"):
        return {"success": False, "message": "credentials.json is missing! Place the downloaded Google file in the project folder."}
    if not is_valid_email(sender_email.strip()):
        return {"success": False, "message": "Invalid sender email format."}
    if not is_valid_email(recipient_email.strip()):
        return {"success": False, "message": "Invalid recipient email format."}

    return send_offer_email(
        receiver_email = recipient_email.strip(),
        cc_email       = cc_email.strip(),
        candidate_name = candidate_name,
        role           = role,
        docx_bytes     = docx_bytes,
        filename       = filename,
        sender_email   = sender_email.strip(),
    )


# ════════════════════════════════════════════════════════════
#  SYSTEM STATUS CHECKS
# ════════════════════════════════════════════════════════════
def check_system_status(template_bytes: bytes | None) -> dict:
    """Returns a dict of readiness flags for the sidebar status panel."""
    return {
        "template_ok":     template_bytes is not None,
        "credentials_ok":  os.path.exists("credentials.json"),
    }