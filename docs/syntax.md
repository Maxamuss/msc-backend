# Syntax

Model 
```json
{
    "type": "model",
    "config": {
        "model_name": "User",
        "field": ["First Name", "Last Name", "Email"]
    } 
}
```

Table Component
```json
{
    "type": "component",
    "config": {
        "model": "User",
        "fields": ["First Name", "Last Name", "Email"]
    }
}
```

Model 
```json
{
    "type": "model",
    "config": {
        "model_name": "User",
        "field": [
            {
                "id": "1",
                "First Name"
            },
            {
                "id": "2",
                "Last Name"
            }
            {
                "id": "3",
                "Email"
            }
        ]
    } 
}
```

Table Component
```json
{
    "type": "component",
    "config": {
        "model": "User",
        "fields": ["1", "2", "3"]
    }
}
```