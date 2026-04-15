"""
============================================================
  logic.py
  Core business logic:
    - DOCX template filling via XML replacement
    - Replacement map builder for offer letter placeholders
    - Email validation (re-exported from mailer for convenience)
  No Streamlit dependency — pure Python.
============================================================
"""

import os
import re
import zipfile
import tempfile


# ── DOCX XML Replacement ──────────────────────────────────

def _xml_replace(xml: str, replacements: dict) -> str:
    """
    Replaces placeholder tokens inside Word paragraph XML.

    Word splits text runs at arbitrary points, so a single
    placeholder like {{name}} may be spread across multiple
    <w:t> tags. This function:
      1. Collects all <w:t> text in a paragraph.
      2. Joins them into one combined string.
      3. Applies all replacements on the combined string.
      4. Writes the result back into the first <w:t> and
         clears subsequent ones to avoid duplication.

    Args:
        xml          : Full document.xml string.
        replacements : {placeholder: replacement_value} dict.

    Returns:
        str : Modified XML with all placeholders filled.
    """
    # Sort longest keys first to avoid partial substring collisions
    items = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    def replace_para(match):
        para_xml = match.group(0)
        texts = re.findall(r'(<w:t(?:[^>]*)>)(.*?)(</w:t>)', para_xml, re.DOTALL)
        if not texts:
            return para_xml

        combined = "".join(t[1] for t in texts)

        # Only process paragraphs that actually contain a placeholder
        if not any(old in combined for old, _ in items):
            return para_xml

        replaced = combined
        for old, new in items:
            replaced = replaced.replace(old, new)

        result, first = para_xml, True
        for open_tag, old_text, close_tag in texts:
            if first:
                result = result.replace(
                    open_tag + old_text + close_tag,
                    open_tag + replaced + close_tag,
                    1,
                )
                first = False
            else:
                # Clear subsequent runs to avoid duplication
                result = result.replace(
                    open_tag + old_text + close_tag,
                    open_tag + close_tag,
                    1,
                )
        return result

    return re.sub(r"<w:p[ >].*?</w:p>", replace_para, xml, flags=re.DOTALL)


def fill_offer_letter(template_bytes: bytes, replacements: dict) -> bytes:
    """
    Fills an offer letter DOCX template by replacing placeholders
    inside the Word XML, then returns the modified DOCX as bytes.

    Operates entirely in memory via a temp directory — no permanent
    files are written to disk.

    Args:
        template_bytes : Raw bytes of the template .docx file.
        replacements   : {placeholder_string: value} mapping.

    Returns:
        bytes : Filled .docx file as raw bytes, ready for download
                or email attachment.

    Raises:
        Exception : Propagates any ZIP / XML error to the caller.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        path_in  = os.path.join(tmpdir, "template.docx")
        path_out = os.path.join(tmpdir, "filled.docx")

        with open(path_in, "wb") as f:
            f.write(template_bytes)

        with zipfile.ZipFile(path_in, "r") as zin, \
             zipfile.ZipFile(path_out, "w", zipfile.ZIP_DEFLATED) as zout:

            for item in zin.infolist():
                data = zin.read(item.filename)

                if item.filename == "word/document.xml":
                    xml  = data.decode("utf-8")
                    xml  = _xml_replace(xml, replacements)
                    data = xml.encode("utf-8")

                zout.writestr(item, data)

        with open(path_out, "rb") as f:
            return f.read()


# ── Replacement Map Builder ───────────────────────────────

def build_replacements(
    title: str,
    name: str,
    role: str,
    location: str,
    phone: str,
    address: str,
    offer_date: str,
    joining_date: str,
    hr_name: str,
    hr_dept: str,
) -> tuple[str, dict]:
    """
    Constructs the full name and the placeholder → value mapping
    used to fill the offer letter template.

    Both {{placeholder}} style (for dynamic templates) and
    underscore-blank style (for existing scanned/typed templates)
    are covered.

    Args:
        title        : Salutation — "Mr.", "Ms.", "Mrs.", or "Dr."
        name         : Candidate's given name(s).
        role         : Job title / designation.
        location     : Office location or branch.
        phone        : Contact phone number.
        address      : Residential address.
        offer_date   : Date of the offer letter.
        joining_date : Expected date of joining.
        hr_name      : HR signatory full name.
        hr_dept      : HR department label.

    Returns:
        (full_name, replacements_dict)
    """
    full_name = f"{title} {name.strip()}"

    replacements = {
        # ── {{placeholder}} style ──────────────────────────
        "Dear {{name}},":                       f"Dear {name.strip()},",
        "{{name}}":                             full_name,
        "{{role}}":                             f"</w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>{role.strip()}</w:t></w:r><w:r><w:t xml:space=\"preserve\">",
        "{{location}}":                         location.strip(),
        "{{phone}}":                            phone.strip(),
        "{{address}}":                          address.strip(),
        "{{date}}":                             offer_date.strip(),
        "{{joining_date}}":                     joining_date.strip(),
        "{{hr_name}}":                          hr_name.strip(),
        "{{hr_department}}":                    hr_dept.strip(),

        # ── Underscore-blank style ─────────────────────────
        # Longest patterns first to avoid partial matches
        "_____________ (residential address)":  address.strip(),
        "Phone No: ________________________":   f"Phone No: {phone.strip()}",
        "____________________________":         hr_name.strip(),   # 28 underscores
        "___________________________":          hr_name.strip(),   # 27 underscores
        "Mr. _______":                          full_name,
        "Dear ________,":                       f"Dear {name.strip()},",
        "post of __________ based":             f"post of </w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>{role.strip()}</w:t></w:r><w:r><w:t xml:space=\"preserve\"> based",
        "based at ________.":                   f"based at {location.strip()}.",
        " _____________.":                      f" {joining_date.strip()}.",
        "Name: _______________":                f"Name: {name.strip()}",
        "Date: ______________________":         f"Date: {offer_date.strip()}",
    }

    return full_name, replacements
