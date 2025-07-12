import jwt
from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status

from core.tests.base import BaseAPITestCaseAuthenticated
from members.models import Team, Member

User = get_user_model()

class SendMemberInviteViewTests(BaseAPITestCaseAuthenticated):
    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(name='Test Team', tid='T12345678')
        self.user = User.objects.create_user(
            email='inviter@example.com',
            first_name='Ahmad',
            last_name='Ameen',
            password='testpass'
        )
        self.member = Member.objects.create(
            user=self.user,
            team=self.team,
            display_name='Ahmad',
            role='admin'
        )
        self.valid_payload = {
            'tid': 'T12345678',
            'invitee_email': 'newuser@example.com',
            'invited_by': self.user.id,
            'role': 'member',
            'url': 'https://example.com/accept-invite'
        }
        self.url = '/api/invitations/send-invite/'

    @patch('invitations.tasks.send_member_invite_email.delay')
    def test_send_invite_success(self, mock_send_email):
        response = self.client.post(self.url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['detail'], 'Invitation email is being sent.')
        
        # Verify email task was called
        self.assertTrue(mock_send_email.called)
        args, _ = mock_send_email.call_args
        self.assertEqual(args[0], 'newuser@example.com')
        self.assertEqual(args[1], 'Test Team')
        self.assertIn('?token=', args[2])  # Check token is in URL

    def test_send_invite_invalid_data(self):
        invalid_payload = {
            'tid': '',  # Invalid - empty
            'invitee_email': 'not-an-email',
            'invited_by': 'not-an-email',
            'role': 'invalid-role',
            'url': 'not-a-url'
        }
        response = self.client.post(self.url, invalid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_inviting_member_must_be_an_admin(self):
        user2 = User.objects.create_user(
            email='member@example.com',
            first_name='Ahmad',
            last_name='Ameen',
            password='testpass'
        )
        self.member2 = Member.objects.create(
            user=user2,
            team=self.team,
            display_name='Member User',
            role='member'
        )
        valid_payload = {
            'tid': 'T12345678',
            'invitee_email': 'newuser@example.com',
            'invited_by': user2.id,
            'role': 'member',
            'url': 'https://example.com/accept-invite'
        }

        response = self.client.post(self.url, valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_send_invite_nonexistent_team(self):
        payload = {**self.valid_payload, 'tid': 'nonexistent-team'}
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AcceptMemberInviteViewTests(BaseAPITestCaseAuthenticated):
    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(name='Test Team', tid='T12345678')
        self.user = User.objects.create_user(
            email='inviter@example.com',
            first_name='Ahmad',
            last_name='Ameen',
            password='testpass'
        )
        self.user2 = User.objects.create_user(
            email='newuser@example.com',
            first_name='New',
            last_name='User',
            password='testpass'
        )
        self.member = Member.objects.create(
            user=self.user,
            team=self.team,
            display_name='Ahmad',
            role='admin'
        )
        
        # Create a valid token
        self.expire = datetime.now(timezone.utc) + timedelta(hours=24)
        self.valid_token_data = {
            'tid': 'T12345678',
            'invitee_email': 'newuser@example.com',
            'invited_by': self.user.id,
            'role': 'member',
            'url': 'https://example.com/accept-invite',
            'expires_at': self.expire.isoformat(),
        }
        self.valid_token = jwt.encode(self.valid_token_data, settings.SECRET_KEY, algorithm='HS256')
        self.url = '/api/invitations/accept-invite/'

    def test_accept_invite_success(self):
        payload = {'token': self.valid_token}
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Team membership created!')
        
        # Verify member was created
        member = Member.objects.get(user=self.user2, team=self.team)
        self.assertEqual(member.role, 'member')
        self.assertEqual(member.display_name, 'New User')

    def test_accept_invite_missing_token(self):
        payload = {}  # No token
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Missing invitation token')

    def test_accept_invite_expired_token(self):
        # Create expired token
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token_data = {
            **self.valid_token_data,
            'expires_at': expired_time.isoformat()
        }
        expired_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')
        
        payload = {'token': expired_token}
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data['detail'], 'Invitation token has expired!')

    def test_accept_invite_nonexistent_team(self):
        token_data = {
            **self.valid_token_data,
            'tid': 'nonexistent-team'
        }
        invalid_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')
        
        payload = {'token': invalid_token}
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_invite_nonexistent_user(self):
        token_data = {
            **self.valid_token_data,
            'invitee_email': 'nonexistent@example.com'
        }
        invalid_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')
        
        payload = {'token': invalid_token}
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_invite_invalid_token(self):
        payload = {'token': 'invalid-token'}
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
