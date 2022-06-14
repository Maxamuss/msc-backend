import json
import os


def replace_syntax(syntax, old, new):
    syntax_json = json.dumps(syntax)
    syntax_json = syntax_json.replace(old, new)
    return json.loads(syntax_json)


def _read_file(file_path):
    with open(file_path, 'r') as f:
        return json.loads(f.read())


def load_model(model_config):
    from db.models import FieldSchema, ModelSchema
    from db.serializer import FieldSchemaSerializer, ModelSchemaSerializer

    model_data = {
        'name': model_config['model_name'],
    }

    model = ModelSchema.objects.filter(name=model_data['name']).first()
    if model:
        model.delete()

    model_schema_serializer = ModelSchemaSerializer(data=model_data)
    model_schema_serializer.is_valid(raise_exception=True)
    model_schema = model_schema_serializer.save()

    print(f'Created Model: {model_schema.as_model()._meta.model_name}', end='\n')

    for field_config in model_config['fields']:
        field_data = {
            'model_schema': model_schema.id,
            'name': field_config['field_name'],
            'field_type': field_config['field_type'],
            'kwargs': {
                'required': field_config['required'],
                'help_text': field_config['help_text'],
                'unique': field_config['unique'],
                'choices': field_config['choices'],
                'default': field_config['default'],
            },
        }

        field = FieldSchema.objects.filter(name=field_data['name']).first()
        if field:
            field.delete()

        field_schema_serializer = FieldSchemaSerializer(field, data=field_data)
        field_schema_serializer.is_valid(raise_exception=True)
        field_schema = field_schema_serializer.save()

        print(f'\tField: {field_schema.db_column}')


def load_from_directory(directory_path):
    """
    This method loads, parses, validates and creates an application with the configuration in the
    given directory. This should only be used to load application configurations when in the
    complete base state.

    The directory is parsed in the following order:
    1) models
    2) layouts
    3) functions
    4) workflows
    """
    sub_dirs = [
        ('models', load_model),
    ]

    for sub_dir_name, load_method in sub_dirs:
        try:
            sub_dir_path = os.path.join(directory_path, sub_dir_name)
            sub_dir_files = os.listdir(sub_dir_path)

            for config_file_name in sub_dir_files:
                config_file_path = os.path.join(sub_dir_path, config_file_name)
                config_file = _read_file(config_file_path)
                load_method(config_file)
        except FileNotFoundError:
            print('Skipping models directory: not found')
