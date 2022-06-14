from .constants import ComponentsType


def generate_button(text, uri, icon):
    return {
        'component': ComponentsType.button.name,
        'config': {
            'text': text,
            'uri': uri,
            'icon': icon,
        },
    }


def generate_header(title, subtitle, tools):
    return {
        'component': ComponentsType.header.name,
        'config': {
            'title': title,
            'subtitle': subtitle,
            'tools': tools,
        },
    }
