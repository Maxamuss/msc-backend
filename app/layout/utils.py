import json
from typing import Dict, List, Optional

from rest_framework.exceptions import ParseError

from db.models import ModelSchema
from layout.models import Page
from syntax._old.utils import replace_syntax


def populate_all_fields(model_schema, layout):
    all_fields = [
        {'field_name': x.db_column, 'verbose_name': x.name} for x in model_schema.fields.all()
    ]
    all_fields_json = json.dumps(all_fields)

    return replace_syntax(layout, '"__all__"', all_fields_json)


def get_page_layout(
    environment: str, resource: str, resource_type: str, populate_all: bool = False
) -> Dict:
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
        layout = page.layout

        if populate_all:
            # Component may have the __all__ value for the fields attribute. If this is the case,
            # populate will all of the fields of the model.
            return populate_all_fields(model_schema, layout)

        return layout


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
