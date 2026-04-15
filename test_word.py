import re

def _xml_replace(xml: str, replacements: dict) -> str:
    items = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    def replace_para(match):
        para_xml = match.group(0)
        texts = re.findall(r'(<w:t(?:[^>]*)>)(.*?)(</w:t>)', para_xml, re.DOTALL)
        if not texts:
            return para_xml

        combined = "".join(t[1] for t in texts)

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
                result = result.replace(
                    open_tag + old_text + close_tag,
                    open_tag + close_tag,
                    1,
                )
        return result

    return re.sub(r"<w:p[ >].*?</w:p>", replace_para, xml, flags=re.DOTALL)


para = '''<w:p><w:r><w:t>You are selected for the </w:t></w:r><w:r><w:t>post of __________ based</w:t></w:r><w:r><w:t> in our office.</w:t></w:r></w:p>'''
role = "Software Engineer"
reps = {
    "post of __________ based": f"post of </w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>{role.strip()}</w:t></w:r><w:r><w:t xml:space=\"preserve\"> based"
}

out = _xml_replace(para, reps)
print(out)
