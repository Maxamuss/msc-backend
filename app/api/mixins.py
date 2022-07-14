from typing import Optional

from django.utils.functional import cached_property

from rest_framework import status
from rest_framework.response import Response

from syntax.models import Release


class QueryMixin:
    @property
    def model_name(self) -> str:
        return self.kwargs.get('model')  # type: ignore

    @property
    def object_id(self) -> Optional[str]:
        obj_id = self.kwargs.get('object_id')  # type: ignore

        if not obj_id:
            return

        return str(obj_id)

    @property
    def query_params(self):
        """
        Return a dict of query params passed.
        """
        params = dict(self.request.query_params)  # type: ignore

        for key, param in params.items():
            params[key] = list(param)[0]

        return params


class ReleaseMixin:
    @cached_property
    def release(self) -> Release:
        """
        Return the Release object to be used in the request.
        """
        release_version = self.request.query_params.get('release_version')  # type: ignore

        if release_version:
            release = Release.objects.filter(release_version=release_version).first()

            if not release:
                raise Exception('Release version not found.')
        else:
            release = Release.get_current_release()

        return release


class HTTPMixin:
    def get(self, request, *args, **kwargs):
        if self.object_id:  # type: ignore
            return self.detail()  # type: ignore
        return self.list()  # type: ignore

    def post(self, request, *args, **kwargs):
        if not self.object_id:  # type: ignore
            return self.create()  # type: ignore

        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        if self.object_id:  # type: ignore
            return self.update()  # type: ignore

        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy()  # type: ignore


class ViewMixin(QueryMixin, ReleaseMixin, HTTPMixin):
    pass
