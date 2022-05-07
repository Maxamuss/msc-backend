import json
from typing import Dict, Optional

from rest_framework.exceptions import ParseError


def get_page_layout(
    environment: str, resource: str, resource_type: str
) -> Optional[Dict]:
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
        layout = model_layouts.get(resource_type)

        return layout
    return None
