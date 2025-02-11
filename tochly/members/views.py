from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.response import Response
from rest_framework import status, viewsets, generics
from rest_framework.serializers import ValidationError

from users.serializers import ProfileSerializer 

from members.serializers import TeamSerializer, MemberSerializer
from members.models import Team, Member


User = get_user_model()

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    queryset = Team.objects.all()
    lookup_field = 'tid'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

class MemberViewSet(viewsets.ModelViewSet):
    """Handles member creation and retrieval."""
    serializer_class = MemberSerializer

    def get_queryset(self):
        tid = self.kwargs['team_tid']
        team = get_object_or_404(Team, tid=tid)
        return Member.objects.filter(team=team)

    def list(self, request, *args, **kwargs):
        """Returns the list of user profiles instead of Member instances."""
        members = self.get_queryset()
        profiles = [member.user.profile for member in members]
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Handles member creation, ensuring user and team exist."""
        user_pk = self.request.data.get('user')

        team = get_object_or_404(Team, tid=self.kwargs['team_tid'])
        user = get_object_or_404(User, id=user_pk)

        if Member.objects.filter(user=user, team=team).exists():
            raise ValidationError(f"User with email {user.email} is already a member.")

        serializer.save(user=user, team=team)


class UserTeamsListView(generics.ListAPIView):
    serializer_class = TeamSerializer

    def get_queryset(self):
        return Team.objects.filter(members__user=self.request.user).distinct()
