from typing import Optional

from django.utils.functional import cached_property

from rest_framework import status
from rest_framework.response import Response

from syntax.models import Release, ReleaseChange
from syntax.serializers import ReleaseSerializer


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

    def _get_response_data(self, data):
        release_change_count = self.release.release_changes.count()

        response_data = {
            'release': ReleaseSerializer(self.release).data,
            'release_change_count': release_change_count,
            'data': data,
        }

        return response_data

    def _create_release(self, change_type, model_type=None, syntax_json=None, object_id=None):
        release_change = ReleaseChange(
            parent_release=self.release,
            change_type=change_type,
            model_type=model_type or self.model_name,
            syntax_json=syntax_json or self.request.data,
        )
        release_change.save(object_id=object_id or self.object_id)

        return release_change.syntax_json['id']


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
