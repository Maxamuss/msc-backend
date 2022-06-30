from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'developer/releases', views.ReleaseAPIView, basename='releases')


urlpatterns = router.urls + [
    path(
        'application/layout/<str:model>/',
        views.LayoutAPIView.as_view(),
    ),
    path(
        'application/layout/<str:model>/<str:page>/',
        views.LayoutAPIView.as_view(),
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
    path(
        'developer/<str:model>/<uuid:object_id>/<uuid:modelschema_id>/',
        views.DeveloperAPIView.as_view(),
    ),
    path(
        'developer/<str:model>/>/<uuid:modelschema_id>/',
        views.DeveloperAPIView.as_view(),
    ),
]
