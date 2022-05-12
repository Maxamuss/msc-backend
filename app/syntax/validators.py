def _validate_text_length(text):
    if not text or len(text) == 0:
        raise Exception()


def validate_text(text):
    _validate_text_length(text)


def validate_uri(text):
    _validate_text_length(text)


def validate_icon(text):
    _validate_text_length(text)


def validate_field(field):
    pass
