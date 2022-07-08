from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'developer/releases', views.ReleaseViewSet, basename='releases')
router.register(r'developer/user', views.UserViewSet, basename='users')


urlpatterns = router.urls + [
    path(
        'application/layout/',
        views.LayoutAPIView.as_view(),
    ),
    path(
        'application/data/<str:model>/',
        views.DataAPIView.as_view(),
    ),
    path(
        'application/data/<str:model>/<uuid:object_id>/',
        views.DataAPIView.as_view(),
    ),
    # Developer Views
    path(
        'developer/<str:model>/',
        views.DeveloperAPIView.as_view(),
    ),
    path(
        'developer/<str:model>/<uuid:object_id>/',
        views.DeveloperAPIView.as_view(),
    ),
]
