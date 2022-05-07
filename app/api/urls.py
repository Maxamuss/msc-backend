from django.urls import path

from . import views

urlpatterns = [
    path('layout/', views.LayoutAPIView.as_view()),
    path('data/', views.DataAPIView.as_view()),
    path('developer/model/<path:path>/', views.ModelSchemaAPIView.as_view()),
]
