from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('internal-api/', include('api.urls')),
    path('internal-api/auth/', include('accounts.urls')),
]
