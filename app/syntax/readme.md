# Syntax

This app is responsible for loading an expire applications configuration from a directory of JSON
files.

## URIs

`${model}` model the page is on
`${id}` id of the model object. Could be from page or from form submission.

## Usage

```bash
python manage.py apploader /path/to/configuration/directory/
```

# Structure

The structure of the configuration directory should be as follows:

```
├── application.json
├── api
├── db
│   ├── model_1.json
│   ├── model_2.json
├── functions
│   ├── function_1.json
│   ├── function_2.json
├── layout
├── packages
├── workflows
```

existing_release_object = self._get_existing_release_object(object_id)

        if existing_release_object:
            if self.change_type == ReleaseChangeType.CREATE:
                raise Exception('Cannot create a release change when there is an existing object.')

            # If the existing release object is being removed, do not process this change.
            if existing_release_object.change_type == ReleaseChangeType.DELETE:
                return

            if can_merge_syntax(self.syntax_json, existing_release_object.syntax_json):
                # Delete the previous ReleaseChange as a new one will be created.
                if existing_release_object.change_type is not None:
                    existing_release_object.delete()
            else:
                raise Exception(
                    'Changes made to model object cannot be merged with existing object.'
                )
        else:
            if self.change_type != ReleaseChangeType.CREATE:
                raise Exception(
                    'Can only create a model object when there is not an existing object.'
                )

            # validate_release_change(self)

            self._generate_id()

            if 'model_id' not in self.syntax_json:
                self.syntax_json['model_id'] = None

        super().save(*args, **kwargs)