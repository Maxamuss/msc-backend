import json
from typing import Optional, Tuple
from uuid import UUID

from django.db.models import Model as DjangoModel
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from db.models import FieldSchema, ModelSchema
from layout.constants import Environment
from layout.models import Page
from layout.utils import get_page_layout
from packages.models import Package
from syntax.models import Release, ReleaseChange
from syntax.serializers import ReleaseSerializer
from workflows.models import Function, Workflow


class LayoutAPIView(APIView):
    """
    API responsible for returning a page layout.

    /layout/?environment=${environment}&model=${model}&page=${page}
        - environment the user is in (developer or user).

    Developer layouts are defined in files. These are cached in Redis with a 15 minute timeout.

    User layouts are defined for a Model and stored in a corresponding Page table.
    """

    def get(self, *args, **kwargs):
        environment, resource, resource_type = self.parse_args()

        if resource == 'skeleton':
            return self.get_skeleton_layout(environment, resource, resource_type)

        return self.get_page_layout(environment, resource, resource_type)

    def get_skeleton_layout(self, environment, resource, resource_type):
        if environment == 'developer':
            try:
                with open(f'layout/layouts/skeleton.json') as f:
                    layout = json.loads(f.read())
            except FileNotFoundError:
                return Response({'detail': 'File not found.'}, status=status.HTTP_400_BAD_REQUEST)

            if resource_type != 'all':
                layout = layout.get(resource_type)

                if layout is None:
                    return Response(
                        {'detail': 'Incorrect layout value'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return Response(layout, status=status.HTTP_200_OK)
        else:
            layout = {
                'colors': {
                    'primary': '#7e22ce',
                    'secondary': '#7e22ce',
                },
                'sidebar': [
                    {
                        "section_name": "",
                        "links": [
                            {"name": "Books", "icon": "CollectionIcon", "uri": "book:list"},
                        ],
                    },
                ],
            }
            return Response(layout)

    def get_page_layout(self, environment, resource, resource_type):
        layout = get_page_layout(environment, resource, resource_type, populate_all=True)
        return Response(layout, status=status.HTTP_200_OK)

    def parse_args(self) -> Tuple[str, str, str]:
        environment = self.request.GET.get('environment')
        resource = self.request.GET.get('resource')
        resource_type = self.request.GET.get('resource_type')

        # Validate path has correct number of arguments.
        if not environment:
            raise ParseError('environment parameter not supplied')

        if environment not in Environment._member_names_:
            raise ParseError('Incorrect environment parameter supplied')

        if not resource:
            raise ParseError('resource parameter not supplied')

        if not resource_type:
            raise ParseError('resource_type parameter not supplied')

        return environment, resource, resource_type


class DeveloperAPIView(APIView):
    """
    API responsible for handling actions made in the developer site.

    This API view always takes in syntax created on the frontend and manages the version control as
    well as the validation.
    """

    model_name_mapping = {
        ModelSchema._meta.model_name: ModelSchema,
        FieldSchema._meta.model_name: FieldSchema,
        Page._meta.model_name: Page,
        Package._meta.model_name: Package,
        Workflow._meta.model_name: Workflow,
        Function._meta.model_name: Function,
    }

    @property
    def model_name(self) -> str:
        return self.kwargs.get('model')

    @property
    def object_id(self) -> Optional[UUID]:
        return self.kwargs.get('object_id')

    @property
    def release(self) -> Release:
        release_version = self.request.query_params.get('release_version')

        if release_version:
            release = Release.objects.filter(current_release=True).first()

            if not release:
                raise Exception('Release version not found.')
        else:
            release = Release.objects.order_by('-released_at').first()

        return release

    @property
    def model(self) -> DjangoModel:
        model = self.model_name_mapping.get(self.model_name)

        if not model:
            raise Exception('Incorrect model passed.')

        return model

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
        data = self.release.get_all_syntax_definitions(self.model_name)
        return Response(data)

    def detail(self):
        """
        This method returns the syntax for a model from the current release.
        """
        data = self.release.get_syntax_definition(self.model_name, self.object_id)
        return Response(data)

    def create(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        return self.create_release(ReleaseChange.ChangeType.CREATE)

    def update(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        return self.create_release(ReleaseChange.ChangeType.UPDATE)

    def destroy(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        return self.create_release(ReleaseChange.ChangeType.DELETE)

    # ---------------------------------------------------------------------------------------------
    # Util methods
    # ---------------------------------------------------------------------------------------------

    def get_object(self):
        return get_object_or_404(self.get_base_queryset(), id=self.model_id)

    def get_base_queryset(self):
        return self.model.objects.all()

    def get_queryset(self):
        queryset = self.get_base_queryset()
        queryset = self.queryset_related_filter(queryset)
        queryset = self.queryset_only_fields(queryset)
        queryset = self.queryset_ordering(queryset)
        return queryset

    def queryset_related_filter(self, queryset):
        """
        Filter the queryset if the related model parameter is passed.
        """
        model_schema_mapping = {'modelschema': 'model_schema'}

        if self.related_model and self.related_model_id:
            filter_name = model_schema_mapping.get(self.related_model, self.related_model)
            queryset = queryset.filter(**{filter_name: self.related_model_id})
        return queryset

    def queryset_only_fields(self, queryset):
        if not self.model == FieldSchema:
            if isinstance(self.get_model_fields, list):
                return queryset.only(*self.get_model_fields)
        return queryset

    def queryset_ordering(self, queryset):
        return queryset.order_by('-created_at')

    def create_release(self, change_type):
        try:
            ReleaseChange.objects.create(
                release=self.release,
                change_type=change_type,
                model_type=self.model_name,
                object_id=self.object_id,
                syntax_json=self.request.DATA,
            )
        except Exception:
            pass

        return Response({}, status=status.HTTP_200_OK)


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
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response({})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
