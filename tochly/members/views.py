from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Value, Q
from django.db.models.functions import Concat

from rest_framework.response import Response
from rest_framework import viewsets, generics
from rest_framework.serializers import ValidationError
from rest_framework.decorators import action

from users.serializers import ProfileSerializer 

from members.serializers import (
    TeamSerializer, 
    MemberSerializer, 
    MemberWithProfileSerializer
)
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

        queryset = queryset.order_by('-created')
        return queryset

class MemberViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer

    def get_queryset(self):
        tid = self.kwargs['team_tid']
        team = get_object_or_404(Team, tid=tid)
        user_id = self.request.query_params.get('user_id')
        queryset = Member.objects.filter(team=team).select_related('user__profile')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """Returns the list of user profiles instead of Member instances."""
        include = request.query_params.get('include', 'member').strip().lower()
        search_query = request.query_params.get('search', '').strip().lower()
        limit = request.query_params.get('limit')

        queryset = self.get_queryset()
        if search_query:
            queryset = queryset.annotate(
                search_full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            ).filter(
                Q(search_full_name__icontains=search_query) |
                Q(display_name__icontains=search_query)
            )

        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]

        if include == 'both':
            serializer = MemberWithProfileSerializer(queryset, many=True)
            return Response(serializer.data)

        serializer = MemberSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='profiles')
    def profiles(self, request, *args, **kwargs):
        """
        Custom route: /teams/<team_tid>/members/profiles/
        Returns list of member(s) profile(s).
        """
        search_query = request.query_params.get('search', '').strip().lower()
        limit = request.query_params.get('limit')

        members = self.get_queryset()
        if search_query:
            members = members.annotate(
                search_full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            ).filter(
                Q(search_full_name__icontains=search_query) |
                Q(display_name__icontains=search_query)
            )

        profiles = [member.user.profile for member in members]

        if limit and limit.isdigit():
            profiles = profiles[:int(limit)]

        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Handles member creation, ensuring user and team exist."""
        user_pk = self.request.data.get('user')

        team = get_object_or_404(Team, tid=self.kwargs['team_tid'])
        user = get_object_or_404(User, id=user_pk)

        if Member.objects.filter(user=user, team=team).exists():
            raise ValidationError(f'User with email {user.email} is already a member.')

        serializer.save(user=user, team=team)


class UserTeamsListView(generics.ListAPIView):
    serializer_class = TeamSerializer

    def get_queryset(self):
        return Team.objects.filter(members__user=self.request.user).distinct().order_by('-created')
