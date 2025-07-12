import jwt
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.http import Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pydantic import ValidationError

from members.models import Team, Member
from invitations.tasks import send_member_invite_email
from invitations.validators import SendInviteRequestValidator, AcceptInviteValidator

User = get_user_model()

class SendMemberInviteView(APIView):
    def post(self, request):
        try:
            validated_data = SendInviteRequestValidator.model_validate(request.data)
            expire = datetime.now(timezone.utc) + timedelta(hours=24)
            invitation_data = {
                'tid': validated_data.tid,
                'invitee_email': validated_data.invitee_email,
                'invited_by': validated_data.invited_by,
                'role': validated_data.role,
                'url': validated_data.url,
                'expires_at': expire.isoformat(),
            }
            token = jwt.encode(invitation_data, settings.SECRET_KEY, algorithm='HS256')

            team = get_object_or_404(Team, tid=validated_data.tid)
            invite_link = f'{validated_data.url}?token={token}'
            send_member_invite_email.delay(validated_data.invitee_email, team.name, invite_link)
            return Response(
                {'detail': 'Invitation email is being sent.'}, 
                status=status.HTTP_202_ACCEPTED
            )
        except ValidationError as e:
            return Response(
                {"detail": e.errors()},
                status=status.HTTP_400_BAD_REQUEST
            )
        
   
class AcceptMemberInviteView(APIView):
    def post(self, request):
        try:
            invite_token = request.data.get('token')
            if not invite_token:
                return Response(
                    {'detail': 'Missing invitation token'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = jwt.decode(invite_token, settings.SECRET_KEY, algorithms=['HS256'])
            validated_data = AcceptInviteValidator.model_validate(token)
            exp_datetime = datetime.fromisoformat(validated_data.expires_at)
            current_datetime = timezone.now()

            if current_datetime >= exp_datetime:
                return Response(
                    {'detail': 'Invitation token has expired!'}, 
                    status=status.HTTP_406_NOT_ACCEPTABLE
                )

            team = get_object_or_404(Team, tid=validated_data.tid)
            user = get_object_or_404(User, email=validated_data.invitee_email)
            Member.objects.create(
                team=team, 
                user=user, 
                role=validated_data.role, 
                display_name=f'{user.first_name} {user.last_name}'
            )
            return Response(
                {
                    'detail': 'Team membership created!',
                    'data': {
                        'user_id': user.id,
                        'tid': validated_data.tid,
                    },
                }, 
                status=status.HTTP_200_OK
            )
        except Http404 as e:
            return Response(
            {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
            {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
