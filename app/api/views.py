from typing import Optional

from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from api.pagination import DataPagination
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from accounts.models import User
from accounts.serializers import UserSerializer
from db.models import ModelSchema
from syntax.models import Release, ReleaseChange, ReleaseChangeType, ReleaseSyntax
from syntax.serializers import ReleaseSerializer
from .mixins import ReleaseMixin, ViewMixin


class LayoutAPIView(ReleaseMixin, APIView):
    """
    Returns the application information.
    """

    def get(self, *args, **kwargs):
        models = self.release.get_syntax_definitions('modelschema', release=self.release)
        model_ids = [x['id'] for x in models]

        pages = self.release.get_syntax_definitions(
            'page', release=self.release, modelschema_id__in=model_ids
        )

        for page in pages:
            model_id = page['modelschema_id']

            model = [x for x in models if x['id'] == model_id][0]

            if 'pages' in model:
                model['pages'].append(page)
            else:
                model['pages'] = [page]

        data = {'models': models}

        return Response(data)


class DataAPIView(ViewMixin, APIView):
    """
    API responsible for returning data for a specified model.
    """

    @cached_property
    def model(self):
        model_schema = ModelSchema.objects.filter(name__iexact=self.kwargs.get('model')).first()

        if model_schema:
            return model_schema.as_model()

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
        queryset = self.model.objects.all()  # type: ignore

        if params := self.query_params:
            queryset = queryset.filter(**params)

        queryset = self.order_queryset(queryset)

        return queryset

    def order_queryset(self, queryset):
        return queryset.order_by('-created_at')

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.generic_serializer()
        kwargs.setdefault(
            'context',
            {'request': self.request, 'format': self.format_kwarg, 'view': self},
        )
        return serializer_class(*args, **kwargs)

    def generic_serializer(self):
        class GenericSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.model
                fields = '__all__'

        return GenericSerializer


class DeveloperAPIView(ViewMixin, APIView):
    """
    API responsible for handling actions made in the developer site.

    This API view always takes in syntax created on the frontend and manages the version control as
    well as the validation.
    """

    def list(self):
        """
        This method returns all of the syntax definitions for a model from the current release.
        """
        data = self.release.get_syntax_definitions(
            self.model_name,
            release=self.release,
            **self.query_params,
        )
        return Response(data)

    def detail(self):
        """
        This method returns the syntax for a model from the current release.
        """
        data = self.release.get_syntax_definitions(
            self.model_name,
            object_id=self.object_id,
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


class UserViewSet(ModelViewSet):
    """
    API viewset to manage user accounts.
    # permission_classes = [IsAccountAdminOrReadOnly]

    """

    queryset = User.objects.all()
    serializer_class = UserSerializer


class ReleaseViewSet(ViewSet):
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
            serializer = self.serializer_class(release)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
