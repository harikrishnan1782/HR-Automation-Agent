"""
============================================================
  mailer.py
  Handles all email sending logic via the Official Gmail API.
  No Streamlit dependency — pure Python.
============================================================
"""

import os
import re
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email_template import build_email_html, build_email_plain

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+$"
    return bool(re.match(pattern, email.strip()))

def get_gmail_service():
    """Authenticates the user and returns the Gmail API service."""
    creds = None
    # token.json stores the user's access and refresh tokens. It is created 
    # automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("credentials.json not found in the directory.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # This will pop open a browser window for you to log in
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def send_offer_email(
    receiver_email: str,
    cc_email: str,
    candidate_name: str,
    role: str,
    docx_bytes: bytes,
    filename: str,
    sender_email: str,
) -> dict:
    
    if not is_valid_email(receiver_email):
        return {"success": False, "message": "Invalid recipient email address format."}

    if not sender_email.strip() or not is_valid_email(sender_email.strip()):
        return {"success": False, "message": "Invalid sender email address format."}

    # ── Safely format CCs ──
    cc_list = []
    if cc_email.strip():
        raw_ccs = [e.strip() for e in cc_email.replace(";", ",").split(",") if e.strip()]
        for cc in raw_ccs:
            if is_valid_email(cc):
                cc_list.append(cc)
            else:
                return {"success": False, "message": f"Invalid CC email format detected: {cc}"}

    # ── Build the Email Message ──
    msg            = MIMEMultipart("mixed")
    msg["From"]    = f"DataPattern HR <{sender_email.strip()}>"
    msg["To"]      = receiver_email.strip()
    msg["Subject"] = f"Offer Letter — {role} at DataPattern"

    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    # Body
    body = MIMEMultipart("alternative")
    body.attach(MIMEText(build_email_plain(candidate_name, role), "plain", "utf-8"))
    body.attach(MIMEText(build_email_html(candidate_name, role),  "html",  "utf-8"))
    msg.attach(body)

    # DOCX Attachment
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(docx_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(attachment)

    # Encode the message for the Gmail API
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    create_message = {'raw': raw_message}

    # ── Send the Email ──
    try:
        service = get_gmail_service()
        if not service:
            return {"success": False, "message": "Failed to authenticate with Gmail API."}

        # userId="me" tells Google to send it from whichever account you logged into
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        return {
            "success": True,
            "message": f"Email dispatched successfully via Gmail API to **{receiver_email}**"
        }
    except Exception as e:
        return {"success": False, "message": f"API Error: {e}"}