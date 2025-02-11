from django.urls import path, re_path

from rest_framework import routers

from users.views import (
  CustomTokenObtainPairView,
  CustomTokenRefreshView,
  CustomTokenVerifyView,
  CustomProviderAuthView,
  LogoutView,
  ProfileViewSet,
)


router = routers.SimpleRouter()
router.register(r'profiles', ProfileViewSet, basename='profiles')

urlpatterns = [
    re_path(
      r'^o/(?P<provider>\S+)/$', 
      CustomProviderAuthView.as_view(), 
      name='provider-auth',
    ),
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('jwt/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('jwt/verify/', CustomTokenVerifyView.as_view(), name='token-verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

urlpatterns += router.urls
