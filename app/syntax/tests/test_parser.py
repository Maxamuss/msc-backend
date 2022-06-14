import json

from django.test import TestCase

from .._old.parser import SyntaxParser


class SyntaxParserTest(TestCase):
    def _load_fixture(self, path):
        with open(f'syntax/tests/fixtures/{path}', 'r') as f:
            return json.loads(f.read())

    # Test that the component configuration are being correctly identified as valid or not.
    def test_validate_component_no_existing_id(self):
        fixture = self._load_fixture('components/button.json')
        component = fixture['valid'][1]  # no id
        component_id = component.get('id', 'no-id')
        SyntaxParser().validate_component(component)

        self.assertIsNotNone(component.get('id'))
        self.assertNotEqual(component_id, component['id'])

    def test_validate_component_existing_id(self):
        fixture = self._load_fixture('components/button.json')
        component = fixture['valid'][0]  # has id
        component_id = component['id']
        SyntaxParser().validate_component(component)

        self.assertEqual(component_id, component['id'])

    def test_validate_component_button(self):
        fixture = self._load_fixture('components/button.json')

        for component in fixture['valid']:
            SyntaxParser().validate_component(component)

        for component in fixture['invalid']:
            with self.assertRaises(Exception):
                SyntaxParser().validate_component(component)

    def test_validate_component_header(self):
        fixture = self._load_fixture('components/header.json')

        for component in fixture['valid']:
            SyntaxParser().validate_component(component)

        for component in fixture['invalid']:
            with self.assertRaises(Exception):
                SyntaxParser().validate_component(component)

    def test_validate_component_form(self):
        fixture = self._load_fixture('components/form.json')

        for component in fixture['valid']:
            SyntaxParser().validate_component(component)

        for component in fixture['invalid']:
            with self.assertRaises(Exception):
                SyntaxParser().validate_component(component)

    # Test that the component id and page_object_fields attributes of the page are correctly
    # populated for all core components.

    def test_parse_layout_button(self):
        """
        Component: button
        Type: stateless
        children: no
        """
        fixture = self._load_fixture('components/button.json')

        # Test when no parsable fields.
        layout = {'layout': [fixture['valid'][0]]}
        parsed_layout = SyntaxParser().parse_layout(layout)

        self.assertEqual(parsed_layout['page_object_fields'], [])
        self.assertIsNotNone(parsed_layout['layout'][0]['id'])

        # Test when parsable fields.
        layout = {'layout': [fixture['valid'][1]]}
        parsed_layout = SyntaxParser().parse_layout(layout)

        self.assertListEqual(parsed_layout['page_object_fields'], ['text1', 'text2'])
        self.assertIsNotNone(parsed_layout['layout'][0]['id'])

    def test_parse_layout_header(self):
        """
        Component: header
        Type: Stateless
        children: yes -> 'tools'
        """
        fixture = self._load_fixture('components/header.json')

        # Test when no parsable fields or tools.
        layout = {'layout': [fixture['valid'][0]]}
        parsed_layout = SyntaxParser().parse_layout(layout)

        self.assertEqual(parsed_layout['page_object_fields'], [])
        self.assertIsNotNone(parsed_layout['layout'][0]['id'])

        # Test when parsable fields but no tools.
        layout = {'layout': [fixture['valid'][1]]}
        parsed_layout = SyntaxParser().parse_layout(layout)

        self.assertListEqual(parsed_layout['page_object_fields'], ['text1', 'text2'])
        self.assertIsNotNone(parsed_layout['layout'][0]['id'])

        # Test when parsable fields and tools with parsable fields.
        layout = {'layout': [fixture['valid'][2]]}
        parsed_layout = SyntaxParser().parse_layout(layout)

        self.assertListEqual(
            parsed_layout['page_object_fields'], ['text1', 'text2', 'button1', 'button2']
        )
        self.assertIsNotNone(parsed_layout['layout'][0]['id'])
        self.assertIsNotNone(parsed_layout['layout'][0]['config']['tools'][0]['id'])
        self.assertIsNotNone(parsed_layout['layout'][0]['config']['tools'][1]['id'])

    # def test_parse_layout_form(self):
    #     """
    #     Component: form
    #     Type: stateless
    #     children: no
    #     """
    #     component = self._load_fixture('components/form.json')

    #     # Test collecting of form fields.
    #     layout = {'layout': [component]}
    #     parsed_layout = SyntaxParser().parse_layout(layout)

    #     self.assertEqual(parsed_layout['page_object_fields'], ['test_1', 'test_2'])
    #     self.assertIsNotNone(parsed_layout['layout'][0]['id'])
