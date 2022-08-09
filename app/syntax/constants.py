LIST_PAGE_LAYOUT = [
    {
        'component': 'core@Header',
        'config': {
            'title': '<MODEL_NAME_PLURAL>',
            'tools': [
                {
                    'text': 'Create <MODEL_NAME>',
                    'to': '<MODEL_NAME_LOWER>/create',
                }
            ],
        },
    },
    {
        'component': 'core@Table',
        'config': {
            'actions': [
                {
                    'text': 'View',
                    'to': '<MODEL_NAME_LOWER>/<OBJECT_ID>',
                }
            ],
        },
    },
]
CREATE_PAGE_LAYOUT = [
    {
        'component': 'core@Header',
        'config': {
            'title': 'Create <MODEL_NAME>',
        },
    },
    {
        'component': 'core@Form',
        'config': {
            'to': '<MODEL_NAME_LOWER>/<OBJECT_ID>',
        },
    },
]
EDIT_PAGE_LAYOUT = [
    {
        'component': 'core@Header',
        'config': {
            'title': 'Edit <MODEL_NAME>',
            'tools': [
                {
                    'text': 'Delete <MODEL_NAME>',
                    'to': '<MODEL_NAME_LOWER>/<OBJECT_ID>/delete',
                }
            ],
        },
    },
    {
        'component': 'core@Form',
        'config': {
            'method': 'PATCH',
        },
    },
]
DELETE_PAGE_LAYOUT = [
    {
        'component': 'core@Header',
        'config': {
            'title': 'Delete <MODEL_NAME>',
            'tools': [
                {
                    'text': 'Go Back',
                    'to': '<MODEL_NAME_LOWER>/<OBJECT_ID>',
                }
            ],
        },
    },
    {
        'component': 'core@Form',
        'config': {
            'method': 'DELETE',
            'to': '<MODEL_NAME_LOWER>',
            'submit_button_text': 'Confirm Delete',
        },
    },
]
