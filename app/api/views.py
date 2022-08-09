import random
import string

from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from api.pagination import DataPagination
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from accounts.models import User
from accounts.serializers import GroupSerializer, UserSerializer
from db.models import ModelSchema
from syntax.models import Release, ReleaseChange, ReleaseChangeType
from syntax.serializers import ReleaseChangeSerializer, ReleaseSerializer
from .mixins import ReleaseMixin, ViewMixin


class LayoutAPIView(ReleaseMixin, APIView):
    """
    Returns the application information.
    """

    def get(self, *args, **kwargs):
        models = self.release.get_syntax_definitions(
            'modelschema', release=self.release, include_changes=False
        )
        model_ids = [x['id'] for x in models]

        pages = self.release.get_syntax_definitions(
            'page', release=self.release, modelschema_id__in=model_ids, include_changes=False
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
        resource = get_object_or_404(self.get_queryset(), id=self.object_id)
        serializer = self.get_serializer(resource)
        return Response(serializer.data)

    def create(self):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self):
        partial = self.request.method.lower() == 'patch'
        resource = get_object_or_404(self.get_queryset(), id=self.object_id)
        serializer = self.get_serializer(resource, data=self.request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(resource, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            resource._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self):
        resource = get_object_or_404(self.get_queryset(), id=self.object_id)

        if self.request.method.lower() == 'get':
            serializer = self.get_serializer(resource)
            return Response(serializer.data)
        else:
            resource.delete()
            return Response({})

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
        object_id = self._create_release(ReleaseChangeType.CREATE)
        data = self.release.get_syntax_definitions(
            self.model_name,
            object_id=object_id,
            release=self.release,
        )
        return Response(self._get_response_data(data), status=status.HTTP_201_CREATED)

    def update(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        self._create_release(ReleaseChangeType.UPDATE)
        data = self.release.get_syntax_definitions(
            self.model_name,
            object_id=self.object_id,
            release=self.release,
        )
        return Response(self._get_response_data(data), status=status.HTTP_200_OK)

    def destroy(self):
        """
        This method takes a syntax definition, validates it and adds it as a ReleaseChange.
        """
        self._create_release(ReleaseChangeType.DELETE)
        return Response(self._get_response_data(None), status=status.HTTP_200_OK)


class UserViewSet(ReleaseMixin, ModelViewSet):
    """
    API viewset to manage user accounts.
    # permission_classes = [IsAccountAdminOrReadOnly]
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        user = get_object_or_404(User.objects.all(), pk=pk)
        groups = user.groups.order_by('name')

        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-to-group')
    def add_group(self, request, pk=None):
        user = get_object_or_404(User.objects.all(), pk=pk)
        group = get_object_or_404(Group.objects.all(), pk=request.data.get('group_id'))
        group.user_set.add(user)  # type: ignore

        return Response({})

    @action(detail=True, methods=['post'], url_path='remove-from-group')
    def remove_group(self, request, pk=None):
        user = get_object_or_404(User.objects.all(), pk=pk)
        group = get_object_or_404(Group.objects.all(), pk=request.data.get('group_id'))
        group.user_set.remove(user)  # type: ignore

        return Response({})

    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        user = get_object_or_404(User.objects.all(), pk=pk)
        user_groups = set(user.groups.all().values_list('id', flat=True))

        permissions = self.release.get_syntax_definitions('permission')
        permissions = [
            permission
            for permission in permissions
            if str(user.id) in permission['users']
            or len(set(permission['groups']).union(user_groups)) > 0
        ]
        return Response(permissions)

    @action(detail=True, methods=['post'], url_path='add-permission')
    def add_permission(self, request, pk=None):
        user = get_object_or_404(User.objects.all(), pk=pk)

        permission = self.release.get_syntax_definitions(
            'permission', object_id=request.data.get('permission_id')
        )

        if str(user.id) not in permission.syntax_json['users']:
            permission.syntax_json['users'].append(str(user.id))

        return Response({})

    @action(detail=True, methods=['post'], url_path='remove-permission')
    def remove_permission(self, request, pk=None):
        user = get_object_or_404(User.objects.all(), pk=pk)

        permission = self.release.get_syntax_definitions(
            'permission', object_id=request.data.get('permission_id')
        )

        if str(user.id) not in permission.syntax_json['users']:
            permission.syntax_json['users'].append(str(user.id))

        return Response({})


class GroupViewSet(ReleaseMixin, ModelViewSet):
    """
    API viewset to manage groups.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        group = get_object_or_404(Group.objects.all(), pk=pk)
        users = group.user_set.order_by('email')  # type: ignore

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-user')
    def add_user(self, request, pk=None):
        group = get_object_or_404(Group.objects.all(), pk=pk)
        user = get_object_or_404(User.objects.all(), pk=request.data.get('user_id'))
        group.user_set.add(user)  # type: ignore

        return Response({})

    @action(detail=True, methods=['post'], url_path='remove-user')
    def remove_user(self, request, pk=None):
        group = get_object_or_404(Group.objects.all(), pk=pk)
        user = get_object_or_404(User.objects.all(), pk=request.data.get('user_id'))
        group.user_set.remove(user)  # type: ignore

        return Response({})

    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        group = get_object_or_404(Group.objects.all(), pk=pk)

        permissions = self.release.get_syntax_definitions('permission')
        permissions = [
            permission for permission in permissions if group.id in permission['groups']
        ]

        return Response(permissions)

    @action(detail=True, methods=['post'], url_path='add-permission')
    def add_permission(self, request, pk=None):
        group = get_object_or_404(Group.objects.all(), pk=pk)

        permission = self.release.get_syntax_definitions(
            'permission', object_id=request.data.get('permission_id')
        )

        if permission and group.id not in permission['groups']:
            permission['groups'].append(group.id)

            self._create_release(
                ReleaseChangeType.UPDATE,
                model_type='permission',
                syntax_json=permission,
                object_id=permission['id'],
            )

        return Response({})

    @action(detail=True, methods=['post'], url_path='remove-permission')
    def remove_permission(self, request, pk=None):
        group = get_object_or_404(Group.objects.all(), pk=pk)

        permission = self.release.get_syntax_definitions(
            'permission', object_id=request.data.get('permission_id')
        )

        if permission and group.id in permission['groups']:
            permission['groups'].pop(group.id)

            self._create_release(
                ReleaseChangeType.UPDATE,
                model_type='permission',
                syntax_json=permission,
                object_id=permission['id'],
            )

        return Response({})


class ReleaseViewSet(ReleaseMixin, ViewSet):
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

    @action(detail=False, methods=['get'], url_path='current')
    def current_release(self, request):
        release_change_count = self.release.release_changes.count()
        serializer = ReleaseSerializer(self.release)

        return Response({'release': serializer.data, 'release_change_count': release_change_count})

    @action(detail=False, methods=['get'])
    def changes(self, request):
        release_changes = self.release.release_changes.all()

        serializer = ReleaseChangeSerializer(release_changes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def publish(self, request):
        if not self.release.release_changes.all().exists():
            return Response(
                {'error': 'There have been no changes made to the current release.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        release = Release.objects.create(
            parent=self.release,
            release_version=''.join(
                random.choice(string.ascii_uppercase + string.digits) for _ in range(5)
            ),
            release_notes='',
            released_by=User.objects.all()[0],
        )
        serializer = self.serializer_class(release)
        return Response(serializer.data)
