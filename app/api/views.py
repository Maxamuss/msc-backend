import json
import re
from functools import cached_property
from typing import List, Optional, Tuple, Union

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model as DjangoModel
from django.shortcuts import get_object_or_404

from rest_framework import serializers, status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from functions.models import Function
from layout.utils import get_page_layout
from models.models import Model
from models.serializer import ModelSerializer
from packages.models import Package
from .pagination import DataPagination
from .utils import find_component


class LayoutAPIView(APIView):
    """
    API responsible for returning a page layout.

    $model:$id


    Path has to be in the format:
    /layout/{developer|user}/$resource/$resource_type/

    - First argument is the environment the user is viewing.
    - Second argument is the resource e.g. a model or page type (function, package)
    - Third argument is the specific resource layout e.g. list, edit, delete, custom_page_name

    Developer layouts are defined in files. These are cached in Redis with a 15 minute timeout.

    User layouts are defined for a Model and stored in a corresponding Page table.
    """

    def get(self, request):
        environment, resource, resource_type = self.parse_args()

        if resource == 'skeleton':
            return self.get_skeleton_layout(environment, resource_type)

        return self.get_page_layout(environment, resource, resource_type)

    def get_skeleton_layout(self, environment, resource_type):
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
            return Response(
                {'detail': 'User skeleton not implemented'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_page_layout(self, environment, resource, resource_type):
        layout = get_page_layout(environment, resource, resource_type)

        if layout is None:
            return Response(
                {'detail': 'Incorrect layout value'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(layout, status=status.HTTP_200_OK)

    def parse_args(self):
        args = self.request.GET.get('q', '').split(':')

        # Validate path has correct number of arguments.
        if len(args) != 3:
            raise ParseError('Incorrect arguments supplied')

        if args[0] not in ['developer', 'user']:
            raise ParseError('Incorrect environment argument supplied')

        return args


class DataAPIView(APIView):
    """
    API responsible for returning data for a specified model.

    Defines the following views:
        - list:   GET       /data/?q=${model} | /data/?q=${model}@${filter_model}:${filter_id}
            - Default filters:       @${field_name}:${value}
            - User applied filters:  #${field_name}:${value}
        - create: POST      /data/?q=${model}
        - detail: GET       /data/?q=${model}:${id}
        - update: PUT/PATCH /data/?q=${model}:${id}

    https://regex101.com/r/gxQjwQ/1

    `c` args can also be passed which tell the view which component made the request. This is used
    for example by the table and form components as they need to now which fields to use in
    serialization.
    """

    def method_setup(self) -> None:
        self.model_name, self.filter_model_name, self.model_id = self.parse_q_args()
        self.page, self.component_id = self.parse_c_args()
        self.model = self.get_model_class(self.model_name)

    def parse_q_args(self) -> Tuple[str, Optional[str], Optional[str]]:
        q = self.request.query_params.get('q')

        if not q:
            raise ParseError('Did not pass q parameter')

        pattern = re.compile(
            r'^(?P<model>[a-zA-Z_]{1,255})|@(?P<filter_model>[a-zA-Z_]{1,255})|:(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
        )

        groups = re.findall(pattern, q)
        matches = [None, None, None]

        for group in groups:
            for index, value in enumerate(group):
                if value:
                    matches[index] = value

        model_name, filter_model_name, model_id = matches

        # Validate correct permutation of args. Either:
        # model, filter_model, id
        # model, id
        # model

        if not model_name:
            raise ParseError('Model argument not provided')

        if not model_id and filter_model_name:
            raise ParseError('Filter model id argument not provided')

        return model_name, filter_model_name, model_id

    def parse_c_args(self) -> List[Optional[str]]:
        """
        Retrive the fields of the component passed. The component must have a `field` attribute in
        its config. Should be in the format:

        ${page}:${component_id}

        https://regex101.com/r/8ov5BM/1
        """
        NONE_RETURN_VALUES: List[Optional[str]] = [None, None]

        c = self.request.query_params.get('c')

        if not c:
            return NONE_RETURN_VALUES

        pattern = re.compile(
            r'^(?P<page>[a-zA-Z_]{1,255}):(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
        )

        groups = re.findall(pattern, c)
        matches: List[Optional[str]] = [None, None]

        for group in groups:
            for index, value in enumerate(group):
                if value:
                    matches[index] = value

        if any([x is None for x in matches]):
            return NONE_RETURN_VALUES

        return matches

    def get_model_class(self, model_name) -> DjangoModel:
        if not model_name:
            raise Exception()

        model_obj = (
            Model.objects.filter(model_name__iexact=model_name)
            .select_related('model_schema')
            .first()
        )

        if model_obj is None:
            model_obj = ContentType.objects.filter(model=model_name).first()

            if model_obj is None:
                raise ParseError('Model not found')

            model = apps.get_model(model_obj.app_label, model_name)
            self.environment = 'developer'
        else:
            model = model_obj.model_schema.as_model()
            self.environment = 'user'

        return model

    # ---------------------------------------------------------------------------------------------
    # HTTP methods
    # ---------------------------------------------------------------------------------------------

    def get(self, request, *args, **kwargs):
        self.method_setup()

        if self.model_id and not self.filter_model_name:
            return self.detail()
        return self.list()

    def post(self, request, *args, **kwargs):
        self.method_setup()

        if not self.model_id and not self.filter_model_name:
            return self.create()

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        self.method_setup()

        if self.model_id and not self.filter_model_name:
            return self.update()

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    # ---------------------------------------------------------------------------------------------
    # Views
    # ---------------------------------------------------------------------------------------------

    def list(self):
        queryset = self.get_queryset()
        paginator = DataPagination()
        page = paginator.paginate_queryset(queryset, self.request, view=self)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def detail(self):
        resource = get_object_or_404(self.get_queryset(), id=self.model_id)
        serializer = self.get_serializer(resource)
        return Response(serializer.data)

    def create(self):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self):
        partial = self.request.method.lower() == 'patch'
        resource = get_object_or_404(self.get_queryset(), id=self.model_id)
        serializer = self.get_serializer(resource, data=self.request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(resource, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            resource._prefetched_objects_cache = {}

        return Response(serializer.data)

    # ---------------------------------------------------------------------------------------------
    # Util methods
    # ---------------------------------------------------------------------------------------------

    def get_queryset(self):
        """
        Options:
            - Search on each column
            - Sorting
            - Filters
        """
        queryset = self.model.objects.all()
        queryset = self.set_queryset_fields(queryset)
        queryset = self.order_queryset(queryset)

        # Filter the queryset.
        query = {}

        if self.filter_model_name:
            if self.filter_model_name in [field.name for field in self.model._meta.get_fields()]:
                query[self.filter_model_name] = self.model_id

        return queryset.filter(**query)

    def set_queryset_fields(self, queryset):
        only_fields = self.get_fields

        if isinstance(only_fields, list):
            queryset = queryset.only(*only_fields)

        return queryset

    def order_queryset(self, queryset):
        return queryset.order_by('-created_at')

    @cached_property
    def get_fields(self) -> Union[str, List]:
        """
        If the component query parameter is passed, get the component and its defined fields.
        """
        if self.page and self.component_id:
            layout = get_page_layout(self.environment, self.model_name, self.page)

            if layout:
                component = find_component(layout.get('layout', []), self.component_id)

                if component:
                    fields = [
                        x.get('field_name') for x in component.get('config', {}).get('fields', [])
                    ]

                    if 'id' not in fields:
                        fields.append('id')

                    return fields

        return '__all__'

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.generic_serializer(self.model, self.get_fields)
        kwargs.setdefault(
            'context',
            {'request': self.request, 'format': self.format_kwarg, 'view': self},
        )
        return serializer_class(*args, **kwargs)

    def generic_serializer(self, serializer_model, serializer_fields):
        class GenericSerializer(serializers.ModelSerializer):
            class Meta:
                model = serializer_model
                fields = serializer_fields

        return GenericSerializer


# -------------------------------------------------------------------------------------------------
#
#                                      DEVELOPER API VIEWS
#
# -------------------------------------------------------------------------------------------------


class DeveloperBaseAPIView(APIView):
    """
    Base class for developer API views.
    """

    def post(self, request, path):
        return self.create(request)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class ModelAPIView(DeveloperBaseAPIView):
    """
    API responsible for managing the models of the application.
    """

    model = Model
    serializer_class = ModelSerializer

    def update(self, request, *args, **kwargs):
        pass

    def delete(self, request, *args, **kwargs):
        pass


class FunctionAPIView(DeveloperBaseAPIView):
    """
    API responsible for managing functions for an application.
    """

    model = Function


class PackageAPIView(DeveloperBaseAPIView):
    """
    API responsible for managing packages for an application.
    """

    model = Package
