from .constants import HTTPAction


def _validate_text_length(text):
    if not text or len(text) == 0:
        raise Exception()


def validate_text(text):
    _validate_text_length(text)


def validate_uri(text):
    _validate_text_length(text)


def validate_icon(text):
    _validate_text_length(text)


def validate_action(action):
    if action not in HTTPAction._member_names_:
        raise Exception()


def validate_form_field(field):
    keys = {
        'field_name',
        'verbose_name',
        'sortable',
        'default_sorting',
    }


def validate_table_field(field):
    pass
