from enum import Enum

from .validators import validate_form_field, validate_icon, validate_text, validate_uri


class ComponentsTypes(Enum):
    button = 'button'
    header = 'header'
    form = 'form'
    table = 'table'
    tabs = 'tabs'


class AttributeTypes(Enum):
    text = 'text'
    uri = 'uri'
    icon = 'icon'
    form_field = 'form_field'


STATELESS_COMPONENTS = (
    ComponentsTypes.button,
    ComponentsTypes.header,
    ComponentsTypes.form,
)


class ManyOptions(Enum):
    none = 'none'
    components = 'components'
    attributes = 'attributes'


COMPONENT_CONFIG = {
    AttributeTypes.form_field: {
        'field_name': {
            'required': True,
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': None,
            'label': 'Field name',
            'description': 'Name of model field',
            'frontend_default': None,
        },
        'label': {
            'required': False,
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': None,
            'label': 'Field label',
            'description': 'Label for of form field',
            'frontend_default': None,
        },
        'widget': {
            'required': False,
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': None,
            'label': 'Field label',
            'description': 'Label for of form field',
            'frontend_default': None,
        },
        'widget': {
            'required': False,
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': None,
            'label': 'Field label',
            'description': 'Label for of form field',
            'frontend_default': None,
        },
    },
    ComponentsTypes.button: {
        'text': {
            'required': True,
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': None,
            'label': 'Button Text',
            'description': 'Text displayed inside button',
            'frontend_default': 'Button Text',
        },
        'link_uri': {
            'required': True,
            'type': AttributeTypes.uri,
            'many': ManyOptions.none,
            'validator': validate_uri,
            'default': None,
            'label': 'Link',
            'description': 'Link to redirect to when clicked',
            'frontend_default': 'Button Text',
        },
        'icon': {
            'required': False,
            'type': AttributeTypes.icon,
            'many': ManyOptions.none,
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
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': None,
            'label': 'Header title!',
            'description': 'Main text',
            'frontend_default': None,
        },
        'subtitle_text': {
            'required': False,
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': None,
            'default': None,
            'label': 'subtitle',
            'description': 'Smaller text underneath title',
            'frontend_default': 'Subtitle for header',
        },
        'tools': {
            'required': False,
            'type': ComponentsTypes.button,
            'many': ManyOptions.components,
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
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': None,
            'label': 'Form model',
            'description': 'Model that this form is for',
            'frontend_default': None,
        },
        'fields': {
            'required': True,
            'type': AttributeTypes.form_field,
            'many': ManyOptions.attributes,
            'validator': validate_form_field,
            'default': None,
            'label': 'Fields',
            'description': 'Fields for the form',
            'frontend_default': [],
        },
        'submit_button_text': {
            'required': True,
            'type': AttributeTypes.text,
            'many': ManyOptions.none,
            'validator': validate_text,
            'default': 'Submit',
            'label': 'Submit button text',
            'description': 'Text to be displayed in the submit button',
            'frontend_default': 'Submit',
        },
        'link_uri': {
            'required': False,
            'type': AttributeTypes.uri,
            'many': ManyOptions.none,
            'validator': validate_uri,
            'default': '${model}:edit:${model_id}',
            'label': 'Redirect page',
            'description': 'Page that will be redirected to on submitting the form',
            'frontend_default': '${model}:edit:${model_id}',
        },
    },
    ComponentsTypes.table: {
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
            'validator': validate_form_field,
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
