import re
from uuid import uuid4

from .constants import COMPONENT_CONFIG, STATELESS_COMPONENTS, ComponentsTypes


class SyntaxParser:
    """
    This class is responsible for parsing the configuration syntax for a ModelSchema, FieldSchema,
    Page, layout, and ensuring it is valid and populated with the correct values.
    """

    def __init__(self):
        self.component_ids = []
        self.stateless_fields = []

    def validate_component(self, component):
        component_type = ComponentsTypes[component['component']]
        component_config = component['config']
        component_config_settings = COMPONENT_CONFIG[component_type]

        for attribute, config in component_config_settings.items():
            attribute_value = component_config.get(attribute)

            if config['required'] or attribute_value:
                # The config key is required or an optional config key has a value.
                if config['many']:
                    # If the value has multiple values, recursively call this method on all elements.
                    for child_component in attribute_value:
                        self.validate_component(child_component)
                else:
                    # Otherwise, make sure the string value is valid.
                    if config['validator'] is not None:
                        config['validator'](attribute_value)
            else:
                # An optional config key has not been given.
                component_config[attribute] = config['default']

        # Make sure component has a unique id.
        component_id = component.get('id', uuid4())
        while component_id in self.component_ids:
            component_id = uuid4()

        self.component_ids.append(component_id)
        component['id'] = str(component_id)

    def parse_layout(self, page):
        """
        Parse a single page's layout configuration, returning a modified version. This method will
        return an error if the configuration is not in a valid format.

        This method does several things:
        1) all components have a valid configuration
        2) gives each component a unique id within the page
        3) determines if the page requires loading of a model object, and if so, the field required
        """
        layout = page.get('layout')

        if layout is None:
            raise Exception('Layout is not defined for page.')

        page['page_object_fields'] = []

        for component in layout:
            self.validate_component(component)

            # Find if any stateless components have data fields.
            field_match = re.compile(r'\{\{(.*?)\}\}')

            def find_matched_fields(attribute, value):
                if 'text' in attribute:
                    for matched_field in re.findall(field_match, value):
                        if matched_field not in self.stateless_fields:
                            self.stateless_fields.append(matched_field.strip())

            if ComponentsTypes[component['component']] in STATELESS_COMPONENTS:
                for attribute, value in component['config'].items():
                    if isinstance(value, list):
                        if attribute == 'fields':
                            for field in value:
                                self.stateless_fields.append(field['field_name'])
                        else:
                            for child_component in value:
                                for attribute_, value_ in child_component['config'].items():
                                    find_matched_fields(attribute_, value_)
                    else:
                        find_matched_fields(attribute, value)

        page['page_object_fields'] = self.stateless_fields

        return page
