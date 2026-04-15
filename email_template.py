"""
============================================================
  email_template.py
  Builds a clean plain-text email body for offer dispatch.
  No branding, no HTML — just a professional plain email.
============================================================
"""


def build_email_html(candidate_name: str, role: str) -> str:
    """
    Minimal clean HTML email — no colours, no dark theme,
    just a professional white-background message that looks
    native in any inbox.

    Args:
        candidate_name : Full name of the candidate.
        role           : Job title / designation.

    Returns:
        str : Clean HTML email string.
    """
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offer Letter — DataPattern</title>
</head>
<body style="margin:0;padding:0;background:#ffffff;
             font-family:Arial,Helvetica,sans-serif;
             font-size:14px;color:#1a1a1a;line-height:1.7;">

  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#ffffff;padding:40px 24px;">
    <tr><td align="left" style="max-width:600px;">

      <p>Dear {candidate_name},</p>

      <p>
        We are pleased to offer you the position of <strong>{role}</strong>
        at <strong>DataPattern</strong>.
        Please find your official Offer Letter attached to this email.
        Kindly review it carefully and revert with your acceptance at the earliest.
      </p>

      <p>Should you have any questions regarding the offer or the onboarding process,
      feel free to reach out to the HR team.</p>

      <p>We look forward to welcoming you to the DataPattern family.</p>

      <p style="margin-top:32px;">
        Warm regards,<br>
        <strong>HR Team</strong><br>
        DataPattern
      </p>

    </td></tr>
  </table>

</body>
</html>"""


def build_email_plain(candidate_name: str, role: str) -> str:
    """
    Plain-text version of the offer email.

    Args:
        candidate_name : Full candidate name.
        role           : Offered job title.

    Returns:
        str : Plain-text email body.
    """
    return (
        f"Dear {candidate_name},\n\n"
        f"We are pleased to offer you the position of {role} at DataPattern.\n"
        f"Please find your official Offer Letter attached to this email.\n"
        f"Kindly review it carefully and revert with your acceptance at the earliest.\n\n"
        f"Should you have any questions regarding the offer or the onboarding process,\n"
        f"feel free to reach out to the HR team.\n\n"
        f"We look forward to welcoming you to the DataPattern family.\n\n"
        f"Warm regards,\n"
        f"HR Team\n"
        f"DataPattern"
    )