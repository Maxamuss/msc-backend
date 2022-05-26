'''
Defines the layout of the page in order of render (starting from the top). Each key is the
component to be used with the parameters to be passed to it.
'''
MODEL_DEFAULT_PAGES = {
    'list': [
        {
            'component': 'header',
            'config': {
                'title': '${model}',
                'tools': [
                    {
                        'text': 'Add Model',
                        'uri': '${model}:create',
                        'icon': 'PlusCircleIcon',
                    }
                ],
            },
        },
        {
            'component': 'table',
            'config': {
                'model': '${model}',
            },
        },
    ],
    'edit': [
        {
            'component': 'header',
            'config': {
                'title': 'Edit ${model}: ${id}',
                'subtitle': '',
                'tools': [
                    {
                        'text': 'Delete',
                        'uri': '${model}:delete:${id}',
                        'icon': 'TrashIcon',
                    }
                ],
            },
        },
        {
            'component': 'form',
            'config': {
                'model': '${model}',
                'submit_button_text': 'Save Object',
            },
        },
    ],
    'create': [
        {
            'component': 'header',
            'config': {
                'title': 'Create ${model}',
            },
        },
        {
            'component': 'form',
            'config': {
                'model': '${model}',
                'uri': '${model}:edit:${id}',
                'submit_button_text': 'Create',
            },
        },
    ],
    'delete': [
        {
            'component': 'header',
            'config': {
                'title': 'Delete ${model}: ${id}',
                'subtitle': 'Are you sure you want to delete this object?',
            },
        }
    ],
}
