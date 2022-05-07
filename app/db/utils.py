from django.apps import apps

from . import cache


def is_current_model(model):
    # if there is no cache entry, the model schema has not been updated since
    # restarting the server and the current schema is fine
    last_modified = cache.get_last_modified(model.__name__)
    return last_modified is None or last_modified < model._declared


class ModelRegistry:
    def __init__(self, app_label):
        self.app_label = app_label

    def is_registered(self, model_name):
        return model_name.lower() in apps.all_models[self.app_label]

    def get_model(self, model_name):
        try:
            return apps.get_model(self.app_label, model_name)
        except LookupError:
            return None

    def unregister_model(self, model_name):
        try:
            del apps.all_models[self.app_label][model_name.lower()]
        except KeyError as err:
            raise LookupError("'{}' not found.".format(model_name)) from err
