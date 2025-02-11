from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework import serializers

from members.models import Team, Member
from members.serializers import TeamSerializer, MemberSerializer
from users.serializers import UserSerializer


User = get_user_model()

class TeamSerializerTest(TestCase):
    def setUp(self):
        self.team_data = {
            'name': 'Development Team',
            'description': 'Team responsible for software development',
        }
        self.team = Team.objects.create(**self.team_data)

    def test_team_serializer_valid_data(self):
        serializer = TeamSerializer(instance=self.team)
        self.assertEqual(serializer.data['name'], self.team_data['name'])
        self.assertEqual(serializer.data['description'], self.team_data['description'])

    def test_team_serializer_invalid_data(self):
        invalid_data = {
            'name': '',
            'description': 'Invalid team',
        }
        serializer = TeamSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_team_serializer_create(self):
        new_team_data = {
            'name': 'QA Team',
            'description': 'Team responsible for quality assurance',
        }
        serializer = TeamSerializer(data=new_team_data)
        self.assertTrue(serializer.is_valid())
        team = serializer.save()
        self.assertEqual(team.name, new_team_data['name'])
        self.assertEqual(team.description, new_team_data['description'])

    def test_team_serializer_update(self):
        updated_data = {
            'name': 'Updated Team Name',
            'description': 'Updated team description',
        }
        serializer = TeamSerializer(instance=self.team, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        team = serializer.save()
        self.assertEqual(team.name, updated_data['name'])
        self.assertEqual(team.description, updated_data['description'])


class MemberSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email='test@example.com',
            password='testPassword123',
            first_name='Ahmad',
            last_name='Ameen',
        )
        self.team = Team.objects.create(name='Test Team', description='A test team')
        self.member_data = {
            'user': self.user,
            'team': self.team,
            'role': 'member',
        }
        self.member = Member.objects.create(**self.member_data)

    def test_member_serializer_valid_data(self):
        serializer = MemberSerializer(instance=self.member)
        self.assertEqual(serializer.data['role'], self.member_data['role'])
        self.assertEqual(serializer.data['user']['email'], self.user.email)
        self.assertEqual(serializer.data['team'], self.team.id)

    def test_member_serializer_invalid_data(self):
        invalid_data = {
            'role': '',
        }
        serializer = MemberSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('role', serializer.errors)

    def test_member_serializer_to_representation(self):
        serializer = MemberSerializer(instance=self.member)
        representation = serializer.to_representation(self.member)
        self.assertIn('user', representation)
        self.assertIn('team', representation)
        self.assertEqual(representation['user']['email'], self.user.email)
        self.assertEqual(representation['team'], self.team.id)

    def test_member_serializer_create(self):
        new_member_data = {
            'user': self.user.id,
            'team': self.team.id,
            'role': 'member',
        }
        serializer = MemberSerializer(data=new_member_data)
        self.assertTrue(serializer.is_valid())
        member = serializer.save()
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.team, self.team)
        self.assertEqual(member.role, new_member_data['role'])

    def test_member_serializer_update(self):
        updated_data = {
            'role': 'admin',
        }
        serializer = MemberSerializer(instance=self.member, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        member = serializer.save()
        self.assertEqual(member.role, updated_data['role'])
