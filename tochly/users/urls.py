from django.urls import path, re_path

from users.views import (
  CustomTokenObtainPairView,
  CustomTokenRefreshView,
  CustomTokenVerifyView,
  CustomProviderAuthView,
  LogoutView,
)


urlpatterns = [
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('logout/', LogoutView.as_view()),
    re_path(
      r'^o/(?P<provider>\S+)/$', 
      CustomProviderAuthView.as_view(), 
      name='provider-auth',
    )
]
