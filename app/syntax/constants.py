from enum import Enum

from .validators import validate_field, validate_icon, validate_text, validate_uri


class ComponentsTypes(Enum):
    button = 'button'
    header = 'header'
    form = 'form'


STATELESS_COMPONENTS = (
    ComponentsTypes.button,
    ComponentsTypes.header,
    ComponentsTypes.form,
)


COMPONENT_CONFIG = {
    ComponentsTypes.button: {
        'text': {
            'required': True,
            'type': 'text',
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Button Text',
            'description': 'Text displayed inside button',
            'frontend_default': 'Button Text',
        },
        'link': {
            'required': True,
            'type': 'link',
            'many': False,
            'validator': validate_uri,
            'default': None,
            'label': 'Link',
            'description': 'Link to redirect to when clicked',
            'frontend_default': 'Button Text',
        },
        'icon': {
            'required': False,
            'type': 'icon',
            'many': False,
            'validator': validate_icon,
            'default': None,
            'label': 'Icon',
            'description': 'Icon displayed on left of button text',
            'frontend_default': None,
        },
    },
    ComponentsTypes.header: {
        'title_text': {
            'required': True,
            'type': 'text',
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Header title!',
            'description': 'Main text',
            'frontend_default': None,
        },
        'subtitle_text': {
            'required': False,
            'type': 'text',
            'many': False,
            'validator': None,
            'default': None,
            'label': 'subtitle',
            'description': 'Smaller text underneath title',
            'frontend_default': 'Subtitle for header',
        },
        'tools': {
            'required': False,
            'type': ComponentsTypes.button,
            'many': True,
            'validator': None,
            'default': [],
            'label': 'Tools',
            'description': 'List of buttons to be rendered on the right of title',
            'frontend_default': [
                {
                    'component': "button",
                    'config': {
                        'text': 'Tool button',
                        'icon': 'CursorClickIcon',
                        'uri': None,
                    },
                }
            ],
        },
    },
    ComponentsTypes.form: {
        'model': {
            'required': True,
            'type': 'text',
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Form model',
            'description': 'Model that this form is for',
            'frontend_default': None,
        },
        'fields': {
            'required': True,
            'type': 'field',
            'many': True,
            'validator': validate_field,
            'default': None,
            'label': 'Fields',
            'description': 'Fields for the form',
            'frontend_default': [],
        },
        'submit_button_text': {
            'required': True,
            'type': 'text',
            'many': False,
            'validator': validate_text,
            'default': 'Submit',
            'label': 'Submit button text',
            'description': 'Text to be displayed in the submit button',
            'frontend_default': 'Submit',
        },
        'link': {
            'required': False,
            'type': 'text',
            'many': False,
            'validator': validate_text,
            'default': 'edit',
            'label': 'Link page',
            'description': 'Page that each row should link to',
            'frontend_default': 'edit',
        },
    },
}
