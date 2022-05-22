from enum import Enum


class ComponentsType(Enum):
    button = 'button'
    header = 'header'
    form = 'form'
    table = 'table'
    tabs = 'tabs'


class AttributeType(Enum):
    text = 'text'
    uri = 'uri'
    icon = 'icon'
    form_field = 'form_field'
    table_field = 'table_field'


class HTTPAction(Enum):
    get = 'GET'
    post = 'POST'
    put = 'PUT'
    patch = 'PATCH'
    delete = 'DELETE'


STATELESS_COMPONENTS = (
    ComponentsType.button,
    ComponentsType.header,
    ComponentsType.form,
)
