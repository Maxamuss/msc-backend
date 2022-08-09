from uuid import UUID

from django.core.management.base import BaseCommand

from accounts.models import User
from syntax.models import Release, ReleaseChange, ReleaseChangeType, ReleaseSyntax

data = {
    'modelschema': [
        {
            'model_name': 'Author',
            'fields': [
                {'field_name': 'author_name', 'field_type': 'text', 'required': True},
            ],
        },
    ],
    'function': [
        {
            'function_name': 'Send Email',
        },
        {
            'function_name': 'Export as CSV',
        },
    ],
}


class Command(BaseCommand):
    help = 'Setup testing environment'

    def handle(self, *args, **options):
        user = User.objects.create_superuser(email='admin@email.com', password=None)  # type: ignore
        user.set_password('superuser')
        user.save()

        initial_release = Release.objects.create(
            release_version='Release 0',
        )

        for model_type, definitions in data.items():
            for definition in definitions:
                ReleaseChange.objects.create(
                    parent_release=initial_release,
                    change_type=ReleaseChangeType.CREATE,
                    model_type=model_type,
                    syntax_json=definition,
                )

        second_release = Release.objects.create(
            parent=initial_release,
            release_version='23EFB',
        )

        author_modelschema_id = (
            ReleaseSyntax.objects.filter(
                model_type='modelschema', syntax_json__model_name='Author'
            )
            .first()
            .syntax_json['id']
        )

        book_schema = {
            'model_name': 'Book',
            'fields': [
                {
                    'field_name': 'book_name',
                    'field_type': 'text',
                    'required': True,
                },
                {
                    'field_name': 'author',
                    'field_type': 'fk',
                    'required': True,
                    'modelschema_id': author_modelschema_id,
                },
            ],
        }
        ReleaseChange.objects.create(
            parent_release=second_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json=book_schema,
        )
        third_release = Release.objects.create(
            parent=second_release,
            release_version='RH765',
        )

        book_modelschema_id = (
            ReleaseSyntax.objects.filter(model_type='modelschema', syntax_json__model_name='Book')
            .first()
            .syntax_json['id']
        )
        rental_schema = {
            'model_name': 'Rental',
            'fields': [
                {
                    'field_name': 'book',
                    'field_type': 'fk',
                    'modelschema_id': book_modelschema_id,
                    'required': True,
                },
                {
                    'field_name': 'customer_name',
                    'field_type': 'text',
                    'required': True,
                },
                {'field_name': 'loaned_at', 'field_type': 'datetime', 'required': True},
            ],
        }
        ReleaseChange.objects.create(
            parent_release=third_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json=rental_schema,
        )
        forth_release = Release.objects.create(
            parent=third_release,
            release_version='MX2QP',
        )
        return

        forth_release = Release.objects.create(
            parent=second_release,
            release_version='MX2QP',
        )

        fifth_release = Release.objects.create(
            parent=forth_release,
            release_version='KL93J',
        )

        # second_release = Release.objects.get(
        #     release_version='0.1.0',
        # )

        ReleaseChange.objects.create(
            parent_release=fifth_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='page',
            syntax_json={
                'page_name': 'list',
                'modelschema_id': str(
                    ReleaseSyntax.objects.filter(
                        model_type='modelschema', syntax_json__model_name='Book'
                    )
                    .first()
                    .syntax_json['id']
                ),
                'layout': [
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
                ],
            },
        )
        # ReleaseChange.objects.create(
        #     parent_release=second_release,
        #     change_type=ReleaseChangeType.CREATE,
        #     model_type='page',
        #     syntax_json={
        #         'page_name': 'create',
        #         'modelschema_id': str(
        #             ReleaseSyntax.objects.filter(
        #                 model_type='modelschema', syntax_json__model_name='Book'
        #             )
        #             .first()
        #             .syntax_json['id']
        #         ),
        #         'layout': [
        #             {
        #                 'component': 'core@Header',
        #                 'config': {
        #                     'title': 'Create <MODEL_NAME>',
        #                 },
        #             },
        #             {
        #                 'component': 'core@Form',
        #                 'config': {
        #                     'to': '<MODEL_NAME_LOWER>/<OBJECT_ID>',
        #                 },
        #             },
        #         ],
        #     },
        # )
        # ReleaseChange.objects.create(
        #     parent_release=second_release,
        #     change_type=ReleaseChangeType.CREATE,
        #     model_type='page',
        #     syntax_json={
        #         'page_name': 'edit',
        #         'modelschema_id': str(
        #             ReleaseSyntax.objects.filter(
        #                 model_type='modelschema', syntax_json__model_name='Book'
        #             )
        #             .first()
        #             .syntax_json['id']
        #         ),
        #         'layout': [
        #             {
        #                 'component': 'core@Header',
        #                 'config': {
        #                     'title': 'Edit <MODEL_NAME>',
        #                 },
        #             },
        #             {
        #                 'component': 'core@Form',
        #                 'config': {
        #                     'method': 'PATCH',
        #                 },
        #             },
        #         ],
        #     },
        # )

        # ReleaseChange.objects.create(
        #     parent_release=second_release,
        #     change_type=ReleaseChangeType.CREATE,
        #     model_type='page',
        #     syntax_json={'page_name': 'list', 'modelschema_id': str(model_ids['Rental'])},
        # )
        # ReleaseChange.objects.create(
        #     parent_release=second_release,
        #     change_type=ReleaseChangeType.DELETE,
        #     object_id=UUID(second_release.modelschemas[0]['id'], version=4),
        #     model_type='modelschema',
        #     syntax_json={},
        # )
        # print(second_release.modelschemas)
        # ReleaseChange.objects.create(
        #     parent_release=second_release,
        #     change_type=ReleaseChangeType.UPDATE,
        #     object_id=UUID(second_release.modelschemas[0]['id'], version=4),
        #     model_type='modelschema',
        #     syntax_json={'model_name': 'Horror Book', 'fields': []},
        # )
        # ReleaseChange.objects.create(
        #     parent_release=second_release,
        #     change_type=ReleaseChangeType.CREATE,
        #     model_type='modelschema',
        #     syntax_json={'model_name': 'Rental', 'fields': []},
        # )

        # third_release = Release.objects.create(
        #     parent=second_release,
        #     release_version='0.2.0',
        #     release_notes='Second release',
        # )
