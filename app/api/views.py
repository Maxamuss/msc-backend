from typing import Optional

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from syntax.models import Release, ReleaseChange, ReleaseChangeType, ReleaseSyntax
from syntax.serializers import ReleaseSerializer


class LayoutAPIView(APIView):
    """
    API responsible for returning a page layout. All layouts are defined within a ReleaseSyntax
    model.
    """

    @property
    def model_name(self) -> str:
        return self.kwargs.get('model')

    @property
    def page_name(self) -> Optional[str]:
        return self.kwargs.get('page')

    def get(self, *args, **kwargs):
        if self.model_name == '__application__':
            layout_data = self._get_application_config()
        else:
            layout_data = self._get_page_layout()

        return Response(layout_data)

    def _get_application_config(self):
        return {'models': []}

    def _get_page_layout(self):
        """
        For the given model_name and page_name, return the layout syntax json.
        """
        release = Release.get_current_release()

        modelschema_id = ReleaseSyntax.get_modelschema_id_from_name(release, self.model_name)
        print(modelschema_id)

        if modelschema_id:
            page = ReleaseSyntax.get_page(release, modelschema_id, self.page_name)

            if page:
                return page.syntax_json['layout']

        return {}


class DeveloperAPIView(APIView):
    """
    API responsible for handling actions made in the developer site.

    This API view always takes in syntax created on the frontend and manages the version control as
    well as the validation.
    """

    @property
    def model_name(self) -> str:
        return self.kwargs.get('model')

    @property
    def object_id(self) -> Optional[str]:
        obj_id = self.kwargs.get('object_id')

        if not obj_id or obj_id == 'null':
            return

        return str(obj_id)

    @property
    def modelschema_id(self) -> Optional[str]:
        """
        Parent id is the uuid primary key of the modelschema that this model is related to.
        """
        ms_id = self.kwargs.get('modelschema_id')

        if not ms_id:
            return

        return str(ms_id)

    @property
    def release(self) -> Release:
        release_version = self.request.query_params.get('release_version')

        if release_version:
            release = Release.objects.filter(release_version=release_version).first()

            if not release:
                raise Exception('Release version not found.')
        else:
            release = Release.get_current_release()

        return release

    # ---------------------------------------------------------------------------------------------
    # HTTP methods
    # ---------------------------------------------------------------------------------------------

    def get(self, *args, **kwargs):
        if self.object_id:
            return self.detail()
        return self.list()

    def post(self, *args, **kwargs):
        return self.create()

    def put(self, *args, **kwargs):
        if self.object_id:
            return self.update()

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def patch(self, *args, **kwargs):
        return self.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.object_id:
            return self.destroy()

        return Response(status=status.HTTP_400_BAD_REQUEST)

    # ---------------------------------------------------------------------------------------------
    # Views
    # ---------------------------------------------------------------------------------------------

    def list(self):
        """
        This method returns all of the syntax definitions for a model from the current release.
        """
        data = self.release.get_syntax_definitions(
            self.model_name,
            modelschema_id=self.modelschema_id,
            release=self.release,
        )
        return Response(data)

    def detail(self):
        """
        This method returns the syntax for a model from the current release.
        """
        data = self.release.get_syntax_definitions(
            self.model_name,
            object_id=self.object_id,
            modelschema_id=self.modelschema_id,
            release=self.release,
        )
        return Response(data)

    def create(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        object_id = self.create_release(ReleaseChangeType.CREATE)
        schema = self.release.get_syntax_definitions(
            self.model_name,
            object_id=object_id,
            release=self.release,
        )
        return Response(schema, status=status.HTTP_200_OK)

    def update(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        self.create_release(ReleaseChangeType.UPDATE)
        schema = self.release.get_syntax_definitions(
            self.model_name,
            object_id=self.object_id,
            release=self.release,
        )
        return Response(schema, status=status.HTTP_200_OK)

    def destroy(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        self.create_release(ReleaseChangeType.DELETE)
        return Response({}, status=status.HTTP_200_OK)

    # ---------------------------------------------------------------------------------------------
    # Util methods
    # ---------------------------------------------------------------------------------------------

    def create_release(self, change_type):
        release_change = ReleaseChange(
            parent_release=self.release,
            change_type=change_type,
            model_type=self.model_name,
            syntax_json=self.request.data,
        )
        release_change.save(object_id=self.object_id)

        return release_change.syntax_json['id']


class ReleaseAPIView(ViewSet):
    """
    API view to manage the releases for the application.

    list: get release tree.
    retrieve: get release model instance.
    publish: publish the current ReleaseChanges as a new Release.
    destroy: delete a release and all child releases.
    """

    serializer_class = ReleaseSerializer

    def list(self, request):
        queryset = Release.objects.all().only(
            'id',
            'release_version',
            'release_notes',
            'released_at',
            'released_by',
            'current_release',
            'parent',
        )
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Release.objects.all()
        release = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer_class(release)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def publish(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            release = serializer.save()
            data = self.serializer_class(data=release).initial_data
            return Response(data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
