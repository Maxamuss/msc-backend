from uuid import uuid4

from .components import COMPONENT_CONFIG
from .constants import STATELESS_COMPONENTS, ComponentsType
from .helpers import extract_fields


class SyntaxParser:
    """
    This class is responsible for parsing the configuration syntax for a ModelSchema, FieldSchema,
    Page, layout, and ensuring it is valid and populated with the correct values.
    """

    def __init__(self):
        self.component_ids = []
        self.stateless_fields = []

    def _reset_class(self):
        self.component_ids = []
        self.stateless_fields = []

    def validate_component(self, component):
        """
        For the given component, validate that is contains the required attributes and add the
        optional attributes with the default values.
        """
        if not component['component'].startswith('core@'):
            component_type = ComponentsType[component['component']]
            component_config = component['config']

            for attribute, config in COMPONENT_CONFIG[component_type].items():
                # Attribute starting with an underscore are metadata about the component.
                if attribute.startswith('_'):
                    continue

                component_value = component_config.get(attribute)

                if config['required'] or component_value:
                    # The config key is required or an optional config key has a value.

                    if not component_value:
                        raise Exception(f'{attribute}: required attribute not provided')

                    # Make the component value a list (in the case it is a single value).
                    if not isinstance(component_value, list):
                        component_value = [component_value]

                    for child in component_value:
                        if config['type'] in ComponentsType:
                            # Attribute type is a component.
                            self.validate_component(child)
                        else:
                            # Attribute type is a string or dictionary.
                            config['validator'](child)
                else:
                    # An optional config key has not been given.
                    component_config[attribute] = config['default']

        # Ensure component has a unique id. UUIDs are used for this. If a component already has an
        # id, this should be used, unless a previous component already has that id. However, the
        # probability of this collision is extremly small, the case is handled.
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
        2) give each component a unique id within the page
        3) determine if the page requires loading of a model object, and if so, the fields
           required
        """
        self._reset_class()

        layout = page.get('layout')

        if layout is None:
            raise Exception('Layout is not defined for page.')

        stateless_fields = []

        for component in layout:
            self.validate_component(component)

            # Find if any stateless components have data fields.
            if not component['component'].startswith('core@'):
                if ComponentsType[component['component']] in STATELESS_COMPONENTS:
                    for attribute, value in component['config'].items():
                        if isinstance(value, list):
                            if attribute == 'fields':
                                # Attribute is a list of model fields.
                                for field in value:
                                    stateless_fields.append(field['field_name'].strip())
                            else:
                                # Attribute is a list of children components.
                                for child_component in value:
                                    for child_value in child_component['config'].values():
                                        stateless_fields += extract_fields(child_value)
                        else:
                            stateless_fields += extract_fields(value)

        page['page_object_fields'] = list(set(stateless_fields))

        return page

    def parse_model(self, model):
        pass

    def parse_function(self, function):
        pass

    def parse_workflow(self, workflow):
        pass
