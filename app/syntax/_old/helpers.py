import re

FIELD_REGEX = re.compile(r'\{\{(.*?)\}\}')


def extract_fields(text):
    """
    Extract the fields from the text. Fields are in the format: {{ field_name }}, where the field
    name to be extracted is surrounded by double curly brackets.
    """
    fields = []

    if isinstance(text, str):
        for matched_field in re.findall(FIELD_REGEX, text):
            fields.append(matched_field.strip())

    return fields
