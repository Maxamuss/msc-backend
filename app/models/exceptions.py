class DynamicModelError(Exception):
    """
    Base exception for use in dynamic models.
    """

    pass


class OutdatedModelError(DynamicModelError):
    """
    Raised when a model's schema is outdated on save.
    """

    pass


class NullFieldChangedError(DynamicModelError):
    """
    Raised when a field is attempted to be change from NULL to NOT NULL.
    """

    pass


class InvalidFieldNameError(DynamicModelError):
    """
    Raised when a field name is invalid.
    """

    pass


class UnsavedSchemaError(DynamicModelError):
    """
    Raised when a model schema has not been saved to the db and a dynamic model
    is attempted to be created.
    """

    pass
