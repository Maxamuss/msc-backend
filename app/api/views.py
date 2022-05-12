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
from rest_framework.views import APIView

from db.models import ModelSchema
from db.serializer import ModelSchemaSerializer
from layout.utils import get_page_layout
from .pagination import DataPagination
from .utils import find_component


class LayoutAPIView(APIView):
    """
    API responsible for returning a page layout.

    $model:$id


    Path has to be in the format:
    /layout/?1=${developer|user}:$resource:$resource_type

    - First argument is the environment the user is in (developer or user).
    - Second argument is the resource e.g. a model or page type (function, package)
    - Third argument is the specific resource layout e.g. list, edit, delete, custom_page_name

    Developer layouts are defined in files. These are cached in Redis with a 15 minute timeout.

    User layouts are defined for a Model and stored in a corresponding Page table.
    """

    def parse_args(self):
        args = self.request.GET.get('q', '').split(':')

        # Validate path has correct number of arguments.
        if len(args) != 3:
            raise ParseError('Incorrect arguments supplied')

        if args[0] not in ['developer', 'user']:
            raise ParseError('Incorrect environment argument supplied')

        return args

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


class DataAPIView(APIView):
    """
    API responsible for returning data for a specified model.

    Defines the following views:
        - list:   GET       /data/?m=${model}&p=${page}
        - create: POST      /data/?m=${model}&p=${page}
        - detail: GET       /data/?m=${model}:${id}&p=${page}
        - update: PUT/PATCH /data/?m=${model}:${id}&p=${page}
        - delete: DELETE    /data/?m=${model}:${id}&p=${page}

    `model` arg must be passed to tell the view which model and optionally the object is being used.

    `page` arg must also be supplied to tell the view which page is being requested from.

    `component` arg can optionally be passed which tell the view which component (id) made the request.
    This is used for example by the table and form components as they need to now which fields
    to use in serialization.
    """

    overridden_serializers = {
        ModelSchema: ModelSchemaSerializer,
    }

    def method_setup(self) -> None:
        self.model_name, self.model_id = self.parse_model_arg()
        self.model = self.get_model_class()

        self.page = self.parse_page_arg()
        self.component_id = self.parse_component_arg()

    def parse_model_arg(self) -> Tuple[str, Optional[str]]:
        model = self.request.query_params['model']

        colon_count = model.count(':')

        if colon_count == 0:
            return model, None
        elif colon_count == 1:
            return model.split(':')
        else:
            raise ParseError('model parameter format incorrect')

    def parse_page_arg(self) -> str:
        return self.request.query_params['page']

    def parse_component_arg(self) -> Optional[str]:
        return self.request.query_params.get('component')

    def get_model_class(self) -> DjangoModel:
        try:
            model_schema = ModelSchema.objects.get(name__iexact=self.model_name)
            model = model_schema.as_model()
            self.environment = 'developer'
        except ModelSchema.DoesNotExist:
            model_obj = get_object_or_404(ContentType.objects.all(), model=self.model_name)
            model = apps.get_model(model_obj.app_label, self.model_name)
            self.environment = 'developer'

        return model

    # ---------------------------------------------------------------------------------------------
    # HTTP methods
    # ---------------------------------------------------------------------------------------------

    def get(self, *args, **kwargs):
        self.method_setup()

        if self.model_id:
            return self.detail()
        return self.list()

    def post(self, *args, **kwargs):
        self.method_setup()

        return self.create()

    def put(self, *args, **kwargs):
        self.method_setup()

        if self.model_id:
            return self.update()

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def patch(self, *args, **kwargs):
        return self.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.method_setup()

        if self.model_id:
            return self.destroy()

        return Response(status=status.HTTP_400_BAD_REQUEST)

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
        resource = self.get_object()
        serializer = self.get_serializer(resource)
        return Response(serializer.data)

    def create(self):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self):
        partial = self.request.method.lower() == 'patch'
        resource = self.get_object()
        serializer = self.get_serializer(resource, data=self.request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(resource, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            resource._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self):
        resource = self.get_object()
        resource.delete()
        return Response()

    # ---------------------------------------------------------------------------------------------
    # Util methods
    # ---------------------------------------------------------------------------------------------

    def get_object(self):
        return get_object_or_404(self.get_base_queryset(), id=self.model_id)

    def get_base_queryset(self):
        return self.model.objects.all()

    def get_queryset(self):
        queryset = self.get_base_queryset()
        queryset = self.queryset_only_fields(queryset)
        queryset = self.queryset_ordering(queryset)
        return queryset

    def queryset_only_fields(self, queryset):
        if isinstance(self.get_model_fields, list):
            return queryset.only(*self.get_model_fields)
        return queryset

    def queryset_ordering(self, queryset):
        return queryset.order_by('-created_at')

    @cached_property
    def get_model_fields(self):
        """
        If the component query parameter is passed, get the component and its defined fields
        otherwise get the page_object_fields from the page.
        """
        all_fields = '__all__'
        layout = get_page_layout(self.environment, self.model_name, self.page)

        if self.component_id:
            component = find_component(layout['layout'], self.component_id)

            if component:
                fields = [
                    x.get('field_name') for x in component.get('config', {}).get('fields', [])
                ]
            else:
                fields = all_fields
        else:
            fields = layout.get('page_object_fields', all_fields)

        if isinstance(fields, list) and 'id' not in fields:
            fields.append('id')

        return fields

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.overridden_serializers.get(self.model, self.generic_serializer())
        kwargs.setdefault(
            'context',
            {'request': self.request, 'format': self.format_kwarg, 'view': self},
        )
        return serializer_class(*args, **kwargs)

    def generic_serializer(self):
        class GenericSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.model
                fields = self.get_model_fields

        return GenericSerializer
