from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import status, viewsets

from members.serializers import TeamSerializer, MemberSerializer
from members.models import Team, Member


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    queryset = Team.objects.all()

    def retrieve(self, request, pk):
        team = get_object_or_404(Team, tid=pk)
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer

    def get_queryset(self):
        return Member.objects.filter(team=self.kwargs['team_pk'])
