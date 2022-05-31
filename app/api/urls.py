from django.urls import path

from . import views

urlpatterns = [
    path('layout/', views.LayoutAPIView.as_view()),
    path('data/', views.DeveloperAPIView.as_view()),
]
