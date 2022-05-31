# Model

# Syntax

```json
{
    "type": "model",
    "config": {
        "verbose_name": "User",
        "verbose_name_plural": "Users",
        "fields": [
            {
                "field_type": "text",
                "field_name": "first_name",
                "verbose_name": "First name",
                "required": true,
                "choices": null,
                "default": null,
                "help_text": null,
                "unique": false,
            }
        ]
    }
}
```

# Fields

## Types
| Type        | Widgets                     | Attributes
| ----------- | ----------------------------|------------
| Boolean     | Toggle                      |
| Text        | Input, TextArea             |
| Date        | DateSelect                  | auto_add_now, auto_now
| Time        | TimeSelect                  | auto_add_now, auto_now
| DateTime    | DateTimeSelect              | auto_add_now, auto_now
| Float       | Number                      | 
| Email       | Email                       | 
| File        | FileInput                   | 
| Integer     | Number                      | 
| JSON        | JSONField                   | 