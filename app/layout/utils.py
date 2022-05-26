import json
from typing import Dict, List, Optional

from rest_framework.exceptions import ParseError

from db.models import ModelSchema
from layout.models import Page


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
        return model_layouts.get(resource_type, {})
    else:
        model_schema = ModelSchema.objects.get(name__iexact=resource)
        page = Page.objects.get(model_schema=model_schema, page_name=resource_type)
        return page.layout


def find_component(layout: List, component_id: str) -> Optional[Dict]:
    """
    Recursively iterate through the nested tree of the layout to find the component with given id.
    """

    for component in layout:
        if component.get('id') == component_id:
            return component
        elif children := component['config'].get('components'):
            return find_component(children, component_id)
    return None
