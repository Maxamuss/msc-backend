# Components

All components are defined with the following format:

,
"": {
    "required": ,
    "type": "",
    "default": "",
    "description": ""
}

```json
{
    "id": "7a99e5ba-2e69-456a-80ad-7808425799e7",
    "component": "button",
    "config": {
        "title": "Add Model"
    }
}
```

 * All components have a unique UUID that is generated when the page is submitted.
 * The config must only contain the required fields. Default field values are populated in the frontend. `null` default values represent the field not being rendered within the component.

## Button

 * component: **button**
 * config:
    * *title*:
        * [required]
        * main button text
    * *icon*: 
        * [default] = `null`
        * icon name displayed on left of text
    * *uri*: 
        * [default] = `null`
        * link to redirect to when clicked

## Container

 * component: **container**
 * config:
    * *children*:  
        * [required] 
        * list of components to be rendered inside

## Header

 * component: **header**
 * config:
    * *title*: 
        * [required]
        * main bold text
    * *subtitle*: 
        * [default] = `null`
        * smaller text underneath title
    * *tools*:
        * [default] = `null`
        * List of `button` components to be rendered on the right of text

## Table 

 * component: **table**
 * config:
    * *data_uri*:
        * [required]
        * uri of the data resource being used to populate table
    * *field_uri*:
        * [required]
        * uri comprised of the component id and page type. Used to on return the necessary model attributes
    * *fields*:
        * [required]
        * list of field objects, defined like:
            * field_name [required]
            * verbose_name [required]
            * sortable [required]
            * default_sorting [required]
    * *link_uri*:
        * [default] = `null`
        * uri for the view link within each row of the table
    * *search*:
        * [default] = `null`
        * display a search bar for querying the table
        * single object of fields, defined like:
            * placeholder [default] = `Search...`
    * *actions*: `null`
    * *filters*: `null`

## Tabs

## Form

 * component: **form**
 * config:
    * *action_uri*
        * [required]
        * uri to where the data should be sent
    * *link_uri*
        * [required]
        * uri to where a redirect should be made to on successful for submit
    * *fields*
        * [required]
        * list of field objects, defined like:
            * field_name [required]
            * label [required]
            * widget [required]
            * required [required]
            * default [required]
            * help_text [required]
            * placeholder [required]
            * layout [required]
    * *submit_button_text*:
        * [default] = `Save`
        * text contained with submit button
    * *action*
        * [default] = `post`
        * http method used when submitting form. Options: `get`, `post`, `put`, `patch`, `delete`