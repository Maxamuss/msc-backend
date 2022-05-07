from typing import Dict, List, Optional


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
