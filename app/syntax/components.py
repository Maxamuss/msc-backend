from .constants import AttributeType, ComponentsType
from .generator import generate_button, generate_header
from .validators import (
    validate_action,
    validate_form_field,
    validate_icon,
    validate_table_field,
    validate_text,
    validate_uri,
)

# The configuration of attributes for fields in each component is defined here. This dictionary is
# converted to JSON and given to the frontend to allow for synchronised frontend validation.
# Definitions:
# ${model}: name of the model
# ${obj_id}: id of the instance targetting within the component
COMPONENT_CONFIG = {
    ComponentsType.button: {
        '_description': 'Button component that can navigate to a page or trigger a function',
        'text': {
            'required': True,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Button Text',
            'description': 'Text displayed inside button',
            'frontend_default': 'Button Text',
        },
        'uri': {
            'required': True,
            'type': AttributeType.uri,
            'many': False,
            'validator': validate_uri,
            'default': None,
            'label': 'On-click action',
            'description': 'Action to be performed when clicked',
            'frontend_default': None,
        },
        'icon': {
            'required': False,
            'type': AttributeType.icon,
            'many': False,
            'validator': validate_icon,
            'default': None,
            'label': 'Icon',
            'description': 'Icon displayed on left of button text',
            'frontend_default': None,
        },
    },
    ComponentsType.header: {
        '_description': 'Header component that for displaying text and buttons',
        'title': {
            'required': True,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Title text',
            'description': 'Main text in header',
            'frontend_default': 'Header title',
        },
        'subtitle': {
            'required': False,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Subtitle text',
            'description': 'Smaller text underneath title',
            'frontend_default': 'Subtitle for header',
        },
        'tools': {
            'required': False,
            'type': ComponentsType.button,
            'many': True,
            'validator': None,
            'default': [],
            'label': 'Tools',
            'description': 'List of buttons to be rendered on the right of title',
            'frontend_default': [
                generate_button('Header button', None, 'CursorClickIcon'),
            ],
        },
    },
    ComponentsType.form: {
        'model': {
            'required': True,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Form model',
            'description': 'Model that this form is for',
            'frontend_default': None,
        },
        'fields': {
            'required': False,
            'type': AttributeType.form_field,
            'many': True,
            'validator': validate_form_field,
            'default': '__all__',
            'label': 'Fields',
            'description': 'Fields for the form',
            'frontend_default': '__all__',
        },
        'action': {
            'required': False,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_action,
            'default': None,
            'label': 'Form model',
            'description': 'Action of form',
            'frontend_default': None,
        },
        'uri': {
            'required': False,
            'type': AttributeType.uri,
            'many': False,
            'validator': validate_uri,
            'default': None,
            'label': 'Form redirect',
            'description': 'Redirect upon successful form submission. Stays on same page by default',
            'frontend_default': None,
        },
        'submit_button_text': {
            'required': False,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': 'Submit',
            'label': 'Submit button text',
            'description': 'Text to be displayed in the submit button',
            'frontend_default': 'Submit',
        },
    },
    ComponentsType.table: {
        'model': {
            'required': True,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Table model',
            'description': 'Model that this form is for',
            'frontend_default': None,
        },
        'fields': {
            'required': False,
            'type': AttributeType.table_field,
            'many': True,
            'validator': validate_table_field,
            'default': '__all__',
            'label': 'Header fields',
            'description': 'Header fields displayed in the table',
            'frontend_default': '__all__',
        },
        'search_fields': {
            'required': False,
            'type': AttributeType.table_field,
            'many': False,
            'validator': validate_table_field,
            'default': [],
            'label': 'Search fields',
            'description': 'Searchable fields in the table',
            'frontend_default': [],
        },
        'related_model': {
            'required': False,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Related model filter',
            'description': 'Related model to filter results on',
            'frontend_default': None,
        },
        'actions': {
            'required': False,
            'type': ComponentsType.button,
            'many': True,
            'validator': None,
            'default': [
                generate_button('View', '${model}:edit:${id}', None),
            ],
            'label': 'Row actions',
            'description': 'List of action buttons for each table row',
            'frontend_default': [
                generate_button('View', '${model}:edit:${id}', None),
            ],
        },
    },
    ComponentsType.tabs: {
        'tabs': {
            'required': True,
            'type': AttributeType.text,
            'many': True,
            'validator': validate_text,
            'default': None,
            'label': 'Tabs',
            'description': 'Names of the tabs',
            'frontend_default': ['Tab1', 'Tab2', 'Tab3'],
        },
        'panels': {
            'required': True,
            'type': ComponentsType._component,
            'many': True,
            'validator': None,
            'default': None,
            'label': 'Tab panels',
            'description': 'Panel content for each tab',
            'frontend_default': [
                generate_header('Tab1 Panel', None, []),
                generate_header('Tab2 Panel', None, []),
                generate_header('Tab3 Panel', None, []),
            ],
        },
    },
    ComponentsType.inline: {
        'model': {
            'required': True,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Table model',
            'description': 'Model that this form is for',
            'frontend_default': None,
        },
        'fields': {
            'required': True,
            'type': AttributeType.table_field,
            'many': True,
            'validator': validate_table_field,
            'default': '__all__',
            'label': 'Header fields',
            'description': 'Header fields displayed in the inline',
            'frontend_default': '__all__',
        },
        'related_model': {
            'required': False,
            'type': AttributeType.text,
            'many': False,
            'validator': validate_text,
            'default': None,
            'label': 'Related model filter',
            'description': 'Related model to filter results on',
            'frontend_default': None,
        },
        'actions': {
            'required': False,
            'type': ComponentsType.button,
            'many': True,
            'validator': None,
            'default': [
                generate_button('Edit', None, None),
                generate_button('View', '${model}:edit:${id}', None),
            ],
            'label': 'Row actions',
            'description': 'List of action buttons for each inline row',
            'frontend_default': [
                generate_button('Edit', None, None),
                generate_button('View', '${model}:edit:${id}', None),
            ],
        },
        'modal': {
            'required': False,
            'type': ComponentsType._component,
            'many': False,
            'validator': None,
            'default': None,
            'label': 'Modal',
            'description': 'Modal displayed to edit or create a new model object',
            'frontend_default': None,
        },
    },
    ComponentsType.column: {
        'children': {
            'required': True,
            'type': ComponentsType._component,
            'many': True,
            'validator': None,
            'default': [],
            'label': 'Column',
            'description': 'Contain a vertical column of components',
            'frontend_default': [],
        },
    },
}
