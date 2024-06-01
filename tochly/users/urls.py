from django.urls import path, re_path

from rest_framework import routers

from users.views import (
  CustomTokenObtainPairView,
  CustomTokenRefreshView,
  CustomTokenVerifyView,
  CustomProviderAuthView,
  LogoutView,
  ProfileViewSet,
  TeamProfilesViewSet,
  UserTeamsViewSet,
)


router = routers.SimpleRouter()
router.register(r'profiles', ProfileViewSet, basename='profiles')

urlpatterns = [
    re_path(
      r'^o/(?P<provider>\S+)/$', 
      CustomProviderAuthView.as_view(), 
      name='provider-auth',
    ),
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('user/teams/', UserTeamsViewSet.as_view()),
    path('team/profiles/', TeamProfilesViewSet.as_view()),
]

urlpatterns += router.urls
