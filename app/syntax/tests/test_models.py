import uuid

from django.test import TestCase

from ..models import Release, ReleaseChange, ReleaseChangeType, ReleaseSyntax


def create_initial_release():
    return Release.objects.create(
        release_version='0.0.0',
        release_notes='Application Initial Release',
    )


class ReleaseTest(TestCase):
    def test_initial_release_creation(self):
        self.assertEqual(0, Release.objects.count())
        self.assertEqual(0, ReleaseChange.objects.count())
        self.assertEqual(0, ReleaseSyntax.objects.count())

        create_initial_release()

        self.assertEqual(1, Release.objects.count())
        self.assertEqual(0, ReleaseChange.objects.count())
        self.assertEqual(0, ReleaseSyntax.objects.count())

    def test_release_create(self):
        """
        Test creating a release when there is only ReleaseChanges.
        """
        self.assertEqual(0, Release.objects.count())
        self.assertEqual(0, ReleaseChange.objects.count())
        self.assertEqual(0, ReleaseSyntax.objects.count())

        release = create_initial_release()

        # ReleaseChange(
        #     parent_release=release,
        #     change_type=ReleaseChangeType.CREATE,
        # )

        # self.assertEqual(1, Release.objects.count())
        # self.assertEqual(0, ReleaseChange.objects.count())
        # self.assertEqual(0, ReleaseSyntax.objects.count())


class ReleaseChangeTest(TestCase):
    def setUp(self):
        self.initial_release = create_initial_release()

    def test_generate_id(self):
        # Case 1: no ReleaseChange or ReleaseSyntax.
        new_release_change = ReleaseChange(
            parent_release=self.initial_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json={},
        )
        new_release_change._generate_id()

        self.assertTrue('id' in new_release_change.syntax_json)
        self.assertIsNotNone(new_release_change.syntax_json['id'])

        # Case 2: no ReleaseChange but exists ReleaseSyntax.
        existing_release_syntax = ReleaseSyntax.objects.create(
            release=self.initial_release,
            model_type='modelschema',
            syntax_json={'id': str(uuid.uuid4())},
        )

        new_release_change = ReleaseChange(
            parent_release=self.initial_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json={},
        )
        new_release_change._generate_id()

        self.assertTrue('id' in new_release_change.syntax_json)
        self.assertIsNotNone(new_release_change.syntax_json['id'])
        self.assertNotEqual(
            new_release_change.syntax_json['id'],
            existing_release_syntax.syntax_json['id'],
        )

        existing_release_syntax.delete()

        # Case 3: exists ReleaseChange but not ReleaseSyntax.
        existing_release_change = ReleaseChange.objects.create(
            parent_release=self.initial_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json={'id': str(uuid.uuid4())},
        )

        new_release_change = ReleaseChange(
            parent_release=self.initial_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json={},
        )
        new_release_change._generate_id()

        self.assertTrue('id' in new_release_change.syntax_json)
        self.assertIsNotNone(new_release_change.syntax_json['id'])
        self.assertNotEqual(
            new_release_change.syntax_json['id'],
            existing_release_change.syntax_json['id'],
        )

        # Case 4: exists ReleaseChange and ReleaseSyntax.
        existing_release_change = ReleaseChange.objects.create(
            parent_release=self.initial_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json={'id': str(uuid.uuid4())},
        )
        existing_release_syntax = ReleaseSyntax.objects.create(
            release=self.initial_release,
            model_type='modelschema',
            syntax_json={'id': str(uuid.uuid4())},
        )

        new_release_change = ReleaseChange(
            parent_release=self.initial_release,
            change_type=ReleaseChangeType.CREATE,
            model_type='modelschema',
            syntax_json={},
        )
        new_release_change._generate_id()

        self.assertTrue('id' in new_release_change.syntax_json)
        self.assertIsNotNone(new_release_change.syntax_json['id'])
        self.assertNotEqual(
            new_release_change.syntax_json['id'],
            existing_release_change.syntax_json['id'],
        )
        self.assertNotEqual(
            new_release_change.syntax_json['id'],
            existing_release_syntax.syntax_json['id'],
        )

    def test_model_id_in_syntax_json(self):
        release_change = ReleaseChange(parent_release=self.initial_release, syntax_json={})

        self.assertFalse('model_id' in release_change.syntax_json)

        release_change.save()

        self.assertTrue('model_id' in release_change.syntax_json)
