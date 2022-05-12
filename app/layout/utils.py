import json
from typing import Dict, List, Optional

from rest_framework.exceptions import ParseError


def get_page_layout(environment: str, resource: str, resource_type: str) -> Dict:
    if environment == 'developer':
        # Open layout file for model.
        try:
            with open(f'layout/layouts/{resource}.json') as f:
                model_layouts = json.loads(f.read())
        except FileNotFoundError:
            raise ParseError(
                'Skeleton definition file not found',
            )

        # Get specific page in layout data.
        return model_layouts[resource_type]
    return {}


def find_component(layout: List, component_id: str) -> Optional[Dict]:
    """
    Recursively iterate through the nested tree of the layout to find the component with given id.
    """

    for component in layout:
        if component.get('id') == component_id:
            return component
        elif children := component['config'].get('children'):
            return find_component(children, component_id)
    return None
