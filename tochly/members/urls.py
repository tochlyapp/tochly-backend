from django.urls import path, include
from rest_framework_nested import routers

from members.views import TeamViewSet, MemberViewSet


router = routers.SimpleRouter()
router.register(r'teams', viewset=TeamViewSet, basename='teams')

teams_router = routers.NestedSimpleRouter(router, r'teams', lookup='team')
teams_router.register(r'members', viewset=MemberViewSet, basename='team-members')

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'', include(teams_router.urls)),
]
