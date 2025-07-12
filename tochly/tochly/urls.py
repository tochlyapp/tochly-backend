from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include(('djoser.urls', 'djoser'), namespace='djoser')),
    path('api/', include('users.urls')),
    path('api/', include('members.urls')),
    path('api/invitations/', include('invitations.urls')),
]
