"""
Defines the layout of the page in order of render (starting from the top). Each key is the
component to be used with the parameters to be passed to it.
"""
MODEL_DEFAULT_PAGES = {
    'list': [
        {
            "component": "header",
            "config": {
                "title": "Test",
                "subtitle": "",
                "tools": [
                    {
                        "text": "Add Model",
                        "icon": "ViewGridAddIcon",
                        "resource": "model",
                        "resource_type": "create",
                    }
                ],
            },
        }
    ],
    'edit': {
        "component": "header",
        "config": {
            "title": "Test",
            "subtitle": "",
            "tools": [
                {
                    "text": "Add Model",
                    "icon": "ViewGridAddIcon",
                    "resource": "model",
                    "resource_type": "create",
                }
            ],
        },
    },
    'create': {
        "component": "header",
        "config": {
            "title": "Test",
            "subtitle": "",
            "tools": [
                {
                    "text": "Add Model",
                    "icon": "ViewGridAddIcon",
                    "resource": "model",
                    "resource_type": "create",
                }
            ],
        },
    },
    'delete': {
        "component": "header",
        "config": {
            "title": "Test",
            "subtitle": "",
            "tools": [
                {
                    "text": "Add Model",
                    "icon": "ViewGridAddIcon",
                    "resource": "model",
                    "resource_type": "create",
                }
            ],
        },
    },
}
