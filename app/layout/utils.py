import json
from typing import Dict, Optional

from rest_framework.exceptions import ParseError


def get_page_layout(environment: str, resource: str, resource_type: str) -> Dict:
    print(environment, resource, resource_type)
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
