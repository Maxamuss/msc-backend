from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'releases', views.ReleaseAPIView, basename='releases')


urlpatterns = [
    path('layout/', views.LayoutAPIView.as_view()),
    path(
        'developer/<str:model>/',
        views.DeveloperAPIView.as_view(),
    ),
    path(
        'developer/<str:model>/<uuid:object_id>/',
        views.DeveloperAPIView.as_view(),
    ),
] + router.urls
