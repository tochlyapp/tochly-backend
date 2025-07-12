from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware

from members.models import Team, Member
from datetime import datetime, timedelta


User =  get_user_model()

class TeamModelTestCase(TestCase):
    def test_create_team_with_minimal_required_fields(self):
        team = Team.objects.create(name='Team Alpha')
        self.assertEqual(team.name, 'Team Alpha')
        self.assertEqual(len(team.tid), 9)
        self.assertIsNotNone(team.created)
        self.assertIsNotNone(team.updated)
        self.assertAlmostEqual(team.created, team.updated, delta=timedelta(microseconds=100))

    def test_name_uniqueness_enforcement(self):
        Team.objects.create(name='Marketing Team', tid='MKT123')
        with self.assertRaises(IntegrityError):
            Team.objects.create(name='Marketing Team', tid='MKT456')

    def test_tid_uniqueness_enforcement(self):
        """Test that duplicate team IDs are not allowed."""
        Team.objects.create(name='Design Team', tid='DSN789')
        with self.assertRaises(IntegrityError):
            Team.objects.create(name='UX Team', tid='DSN789')

    def test_description_field_optionality(self):
        team1 = Team.objects.create(name='Team Alpha')
        team2 = Team.objects.create(name='Team Beta', description='')
        team3 = Team.objects.create(name='Team Gamma', description='Frontend Developers')
        
        self.assertIsNone(team1.description)
        self.assertEqual(team2.description, '')
        self.assertEqual(team3.description, 'Frontend Developers')

    def test_auto_timestamps(self):
        """Verify auto_now_add and auto_now behavior for created/last_updated fields."""
        test_time = make_aware(datetime(2023, 1, 1))
        team = Team.objects.create(name='Old Team')
        team.created = test_time  # Simulate older creation time
        team.updated = test_time
        team.save()

        # Update team and verify timestamp change
        team.name = 'Updated Team Name'
        team.save()
        team.refresh_from_db()

        self.assertEqual(team.created, test_time)
        self.assertGreater(team.updated, test_time)

    def test_string_representation(self):
        """Test the __str__ method returns the team ID."""
        team = Team.objects.create(name='QA Team', tid='QA456')
        self.assertEqual(str(team), 'QA456')

    def test_default_tid_generation(self):
        """Ensure default tid is generated when not provided."""
        team1 = Team.objects.create(name='Team One')
        team2 = Team.objects.create(name='Team Two')
        self.assertNotEqual(team1.tid, team2.tid)
        self.assertTrue(team1.tid.isalnum())


class MemberModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@test.com', first_name='Ahmad', last_name='Ameen')
        self.user2 = User.objects.create_user(email='user2@test.com', first_name='User', last_name='Two')
        
        # Create test teams
        self.team1 = Team.objects.create(name='Team 1', tid='TEAM1')
        self.team2 = Team.objects.create(name='Team 2', tid='TEAM2')
        
        # Create test member with unique user-team combo
        self.member = Member.objects.create(
            user=self.user1,
            team=self.team1,
            display_name='Member 1'
        )

    def test_member_creation(self):
        """Test that member is created with all fields"""
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(self.member.user, self.user1)
        self.assertEqual(self.member.team, self.team1)
        self.assertEqual(self.member.role, 'member')
        self.assertEqual(self.member.display_name, 'Member 1')
        self.assertEqual(self.member.title, None)
        self.assertEqual(self.member.phone_number, None)
        self.assertFalse(self.member.online)
        self.assertEqual(self.member.status, '')
        self.assertEqual(self.member.profile_picture_url, None)
        self.assertIsNotNone(self.member.created)
        self.assertIsNotNone(self.member.updated)

    def test_role_choices(self):
        """Test that role choices are enforced"""
        with self.assertRaises(ValidationError):
            member = Member(
                user=self.user2,
                team=self.team2,
                role='invalid',
                display_name='Invalid Role'
            )
            member.full_clean()

    def test_status_choices(self):
        """Test that status choices are enforced"""
        user3 = User.objects.create_user(email='user3@test.com', first_name='User', last_name='User Three')
        
        # Test with valid status
        member = Member.objects.create(
            user=user3,
            team=self.team1,
            display_name='Valid Status',
            status='meeting'
        )
        self.assertEqual(member.status, 'meeting')

    def test_phone_number_uniqueness(self):
        """Test phone number uniqueness constraint"""
        with self.assertRaises(Exception):
            Member.objects.create(
                user=self.user,
                team=self.team,
                display_name='Duplicate Phone',
                phone_number='+1234567890'
            )

    def test_full_name_property(self):
        """Test the full_name property"""
        self.assertEqual(self.member.full_name, 'Ahmad Ameen')
        
        # Test with empty names
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='',
            last_name=''
        )
        member2 = Member.objects.create(
            user=user2,
            team=self.team2,
            display_name='Empty Names'
        )
        self.assertEqual(member2.full_name, ' ')

    def test_tid_property(self):
        """Test the tid property"""
        self.assertEqual(self.member.tid, 'TEAM1')

    def test_str_representation(self):
        """Test the __str__ method"""
        self.assertEqual(str(self.member), 'TEAM1')

    def test_optional_fields(self):
        """Test that optional fields can be null/blank"""
        member = Member.objects.create(
            user=self.user2,
            team=self.team2,
            display_name='Minimal Member'
        )
        self.assertIsNone(member.title)
        self.assertIsNone(member.phone_number)
        self.assertFalse(member.online)
        self.assertEqual(member.status, '')
        self.assertIsNone(member.profile_picture_url)

    def test_user_team_unique_together(self):
        """Test that user can only have one membership per team"""
        # This should raise IntegrityError because the combination already exists
        with self.assertRaises(Exception) as context:
            Member.objects.create(
                user=self.user1,
                team=self.team1,
                display_name='Duplicate Membership'
            )
        
        self.assertIn('unique', str(context.exception).lower())
