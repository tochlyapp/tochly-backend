from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.serializers import ValidationError

from members.serializers import TeamSerializer, MemberSerializer
from members.models import Team, Member


User = get_user_model()

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name:
            return Team.objects.filter(name=name)

        return Team.objects.all()

    def retrieve(self, request, pk):
        team = get_object_or_404(Team, tid=pk)
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer

    def get_queryset(self):
        return Member.objects.filter(team_id=self.kwargs['team_pk'])

    def perform_create(self, serializer):
        team_id = self.kwargs['team_pk']
        email = self.request.data.get('user')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("User does not exist", 400)
        try:
            team = Team.objects.get(pk=team_id)
        except Team.DoesNotExist:
            raise ValidationError(
                f"No team with team_id {team_id} exist", 400
            )
        try:
            Member.objects.get(user=user, team=team)
        except Member.DoesNotExist:
            serializer.save(user=user, team=team)
        else:
            raise ValidationError(
                f"User with email {email} is already a member"
            )
