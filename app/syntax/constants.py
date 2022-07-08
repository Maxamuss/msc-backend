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
            'fields': [
                {'field_name': 'id', 'header_name': 'ID'},
                {'field_name': 'book_name', 'header_name': 'Book Name'},
            ],
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
        },
    },
    {
        'component': 'core@Form',
        'config': {
            'method': 'PATCH',
        },
    },
]
DELETE_PAGE_LAYOUT = []
