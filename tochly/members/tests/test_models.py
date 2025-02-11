from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware

from members.models import Team, Member
from datetime import datetime, timedelta


User =  get_user_model()

class TeamModelTestCase(TestCase):
    def test_create_team_with_minimal_required_fields(self):
        team = Team.objects.create(name='Development Team')
        self.assertEqual(team.name, 'Development Team')
        self.assertEqual(len(team.tid), 9)
        self.assertIsNotNone(team.created)
        self.assertIsNotNone(team.last_updated)
        self.assertAlmostEqual(team.created, team.last_updated, delta=timedelta(microseconds=100))

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
        team.last_updated = test_time
        team.save()

        # Update team and verify timestamp change
        team.name = 'Updated Team Name'
        team.save()
        team.refresh_from_db()

        self.assertEqual(team.created, test_time)
        self.assertGreater(team.last_updated, test_time)

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


class MemberModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ahmadmameen7@gmail.com',
            password='password123',
            first_name='Ahmad',
            last_name='Ameen'
        )
        self.team = Team.objects.create(name='Test Team')

    def test_create_member(self):
        member = Member.objects.create(user=self.user, team=self.team, role='admin', is_active=True)

        self.assertEqual(member.user, self.user)
        self.assertEqual(member.team, self.team)
        self.assertEqual(member.role, 'admin')
        self.assertTrue(member.is_active)
        self.assertIsNotNone(member.created)
        self.assertIsNotNone(member.last_updated)

    def test_default_permission(self):
        member = Member.objects.create(user=self.user, team=self.team)
        self.assertEqual(member.role, 'member')

    def test_default_is_active(self):
        member = Member.objects.create(user=self.user, team=self.team)
        self.assertFalse(member.is_active)

    def test_created_and_last_updated(self):
        member = Member.objects.create(user=self.user, team=self.team)
        self.assertAlmostEqual(member.created, member.last_updated, delta=timedelta(microseconds=100))
