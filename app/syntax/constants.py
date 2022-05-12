from enum import Enum

from .validators import validate_icon, validate_text, validate_uri


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
        'uri': {
            'required': True,
            'type': 'uri',
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
}
