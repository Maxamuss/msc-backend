import json
from functools import cached_property
from typing import Optional, Tuple

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model as DjangoModel
from django.shortcuts import get_object_or_404

from rest_framework import serializers, status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from db.models import FieldSchema, ModelSchema
from db.serializer import FieldSchemaSerializer, ModelSchemaSerializer
from layout.constants import Environment
from layout.utils import find_component, get_page_layout
from .pagination import DataPagination


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


class DataAPIView(APIView):
    """
    API responsible for returning data for a specified model.

    Defines the following views:
        - list:   GET       /data/?model=${model}&page=${page}
        - create: POST      /data/?model=${model}&page=${page}
        - detail: GET       /data/?model=${model}:${id}&page=${page}
        - update: PUT/PATCH /data/?model=${model}:${id}&page=${page}
        - delete: DELETE    /data/?model=${model}:${id}&page=${page}

    `model` arg must be passed to tell the view which model and optionally the object is being used.

    `page` arg must also be supplied to tell the view which page is being requested from.

    `related_model` arg can optionally be passed to filter the query. This is formatted as a model
    with a object id - ${related_model}:${related_model_id}

    `component` arg can optionally be passed which tell the view which component (id) made the request.
    This is used for example by the table and form components as they need to now which fields
    to use in serialization.
    """

    overridden_serializers = {
        ModelSchema: ModelSchemaSerializer,
        FieldSchema: FieldSchemaSerializer,
    }

    def method_setup(self) -> None:
        self.model_name, self.model_id = self.parse_model_arg()
        self.model = self.get_model_class()

        self.page = self.parse_page_arg()
        self.related_model, self.related_model_id = self.parse_related_model_arg()
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

    def parse_related_model_arg(self) -> Tuple[Optional[str], Optional[str]]:
        related_model = self.request.query_params.get('related_model')

        if related_model and related_model.count(':') == 1:
            return related_model.split(':')
        return None, None

    def parse_component_arg(self) -> Optional[str]:
        return self.request.query_params.get('component')

    def get_model_class(self) -> DjangoModel:
        try:
            model_schema = ModelSchema.objects.get(name__iexact=self.model_name)
            model = model_schema.as_model()
            self.environment = 'user'
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

    @cached_property
    def get_model_fields(self):
        """
        If the component query parameter is passed, get the component and its defined fields
        otherwise get the page_object_fields from the page.
        """
        all_fields = '__all__'

        # Component will be in related model layout.
        model_name = self.related_model or self.model_name
        layout = get_page_layout(self.environment, model_name, self.page)

        if self.component_id:
            component = find_component(layout.get('layout', []), self.component_id)

            if component:
                fields_attribute = component.get('config', {}).get('fields', [])

                if fields_attribute != '__all__':
                    fields = [x.get('field_name') for x in fields_attribute]
                else:
                    fields = all_fields
            else:
                fields = all_fields
        else:
            fields = layout.get('page_object_fields', all_fields)

        if isinstance(fields, list) and 'id' not in fields:
            fields.append('id')

        return fields

    def get_serializer_context(self):
        return {'request': self.request, 'format': self.format_kwarg, 'view': self}

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.overridden_serializers.get(self.model, self.generic_serializer())
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def generic_serializer(self):
        class GenericSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.model
                fields = self.get_model_fields

        return GenericSerializer
