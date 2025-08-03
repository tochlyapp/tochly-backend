import uuid
import json

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.db.models import Value, Q
from django.db.models.functions import Concat

from rest_framework.response import Response
from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError

from common.utils import CacheRateLimiter
from members.utils.s3 import (
    generate_presigned_url, 
    delete_old_profile_picture,
)

from members.serializers import (
    TeamSerializer, 
    MemberSerializer, 
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
    lookup_field = 'id'

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

        serializer = MemberSerializer(queryset, many=True)
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


class PresignedProfileUploadView(APIView):
    def get(self, request):
        limiter = CacheRateLimiter('profile_upload')

        if limiter.is_limited(request.user.id):
            return Response(
                {'error': 'Too many uploads. Try again later.'}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        extension = request.query_params.get('extension', 'jpg')
        content_type = request.query_params.get('type', 'image/jpeg')
        unique_id = str(uuid.uuid4())
        key = f'profile_pictures/{unique_id}.{extension}'

        presigned_url = generate_presigned_url(key, content_type=content_type)
        file_url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{key}'
        upload_token = str(uuid.uuid4())

        cache.set(
            f'profile_upload_token:{upload_token}',
            json.dumps({'key': key, 'user_id': request.user.id}),
            timeout=300
        )

        return Response({
            'upload_url': presigned_url,
            'file_url': file_url,
            'token': upload_token,
        })
    

class CompleteProfileUploadView(APIView):
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({'error': 'Missing upload token.'}, status=400)
        
        team_tid = request.query_params.get('team_tid')
        if not team_tid:
            return Response({'error': 'team_id is required'}, status=400)

        cached_data = cache.get(f'profile_upload_token:{token}')
        if not cached_data:
            return Response({'error': 'Invalid or expired token.'}, status=400)
        
        data = json.loads(cached_data)
        if data['user_id'] != request.user.id:
            return Response({'error': 'Token does not belong to you.'}, status=403)
        
        file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{data['key']}"

        try:
            member = Member.objects.get(user=request.user, team__tid=team_tid)
        except member.DoesNotExist:
            return Response({'detail': 'Member not found in the specified team.'}, status=404)
        else:
            if member.profile_picture_url:
                delete_old_profile_picture(member.profile_picture_url)
            member.profile_picture_url = file_url
            member.save()
        
        cache.delete(f'profile_upload_token:{token}')
        return Response({'success': True, 'file_url': file_url})
    