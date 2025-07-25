from django.test import TestCase
from django.contrib.auth import get_user_model

from members.models import Team, Member
from users.models import Profile
from members.serializers import TeamSerializer, MemberSerializer


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
            first_name='Ahmad',
            last_name='Ameen',
        )

        self.team = Team.objects.create(name='Test Team', tid='TEAM1', description='A test team')
        self.team2 = Team.objects.create(name='Test Team 2', tid='TEAM2')

        Profile.objects.create(user=self.user)

        self.member_data = {
            'user': self.user.pk,
            'team': self.team.pk,
            'display_name': 'Ahmad Ameen',
            'role': 'member',
            'status': 'remote'
        }
        self.member_data1 = {
            'user': self.user,
            'team': self.team,
            'display_name': 'Ahmad Ameen',
            'role': 'member',
            'status': 'remote'
        }
        self.member = Member.objects.create(**self.member_data1)

    def test_serializer_fields(self):
        """Test that serializer contains all model fields"""
        serializer = MemberSerializer(self.member)
        expected_fields = [
            'id', 'user', 'profile', 'team', 'role', 'display_name', 'title',
            'phone_number', 'online', 'status', 'profile_picture_url',
            'created', 'updated', 'tid', 'full_name'
        ]
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_get_full_name_method(self):
        """Test the get_full_name method"""
        serializer = MemberSerializer(self.member)
        self.assertEqual(serializer.data['full_name'], 'Ahmad Ameen')

    def test_get_tid_method(self):
        """Test the get_tid method"""
        serializer = MemberSerializer(self.member)
        self.assertEqual(serializer.data['tid'], 'TEAM1')

    def test_to_representation(self):
        """Test user serialization in representation"""
        serializer = MemberSerializer(self.member)
        self.assertIn('user', serializer.data)
        self.assertEqual(serializer.data['user']['email'], 'test@example.com')
        self.assertEqual(serializer.data['user']['first_name'], 'Ahmad')

    def test_create_valid_member(self):
        """Test creating a member with valid data"""
        data = {
            'user': self.user.pk,
            'display_name': 'Ahmad Ameen',
            'role': 'member',
            'status': 'remote'
        }
        serializer = MemberSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        member = serializer.save(user=self.user, team=self.team2)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.team, self.team2)
        self.assertEqual(member.display_name, 'Ahmad Ameen')

    def test_update_member(self):
        """Test updating a member"""
        updated_data = {
            'display_name': 'Updated Name',
            'status': 'meeting'
        }
        serializer = MemberSerializer(instance=self.member, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        member = serializer.save()
        self.assertEqual(member.display_name, 'Updated Name')
        self.assertEqual(member.status, 'meeting')

    def test_validate_role_choices(self):
        """Test role choice validation"""
        invalid_data = self.member_data.copy()
        invalid_data['role'] = 'invalid_role'
        serializer = MemberSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('role', serializer.errors)

    def test_validate_status_choices(self):
        """Test status choice validation"""
        invalid_data = self.member_data.copy()
        invalid_data['status'] = 'invalid_status'
        serializer = MemberSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_phone_number_uniqueness(self):
        """Test phone number uniqueness validation"""
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            first_name='Jane',
            last_name='Smith'
        )
        self.team2 = Team.objects.create(name='Team 3', tid='TEAM3')
        Member.objects.create(
            user=self.user2,
            team=self.team2,
            phone_number='+1234567890'
        )
        data = self.member_data.copy()
        data['phone_number'] = '+1234567890'
        serializer = MemberSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)
