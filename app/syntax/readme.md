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