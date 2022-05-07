from contextlib import contextmanager

from django.core.exceptions import FieldDoesNotExist
from django.db import connection


def db_table_exists(table_name):
    with _db_cursor() as c:
        table_names = connection.introspection.table_names(c)
        return table_name in table_names


def db_table_has_field(table_name, field_name):
    table = _get_table_description(table_name)
    return field_name in [field.name for field in table]


def db_field_allows_null(table_name, field_name):
    table_description = _get_table_description(table_name)
    for field in table_description:
        if field.name == field_name:
            return field.null_ok
    raise FieldDoesNotExist(f"field {field_name} does not exist on table {table_name}")


def _get_table_description(table_name):
    with _db_cursor() as c:
        return connection.introspection.get_table_description(c, table_name)


def receiver_is_connected(receiver_name, signal, sender):
    receivers = signal._live_receivers(sender)
    receiver_strings = ["{}.{}".format(r.__module__, r.__name__) for r in receivers]
    return receiver_name in receiver_strings


@contextmanager
def _db_cursor():
    cursor = connection.cursor()
    yield cursor
    cursor.close()
