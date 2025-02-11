from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.tests.base import BaseAPITestCaseAuthenticated
from users.models import Profile
from members.models import Team, Member


User = get_user_model()

class TeamViewSetTests(BaseAPITestCaseAuthenticated):
    def setUp(self):
        super().setUp()
        self.team1 = Team.objects.create(tid='T12345678', name='Team Alpha')
        self.team2 = Team.objects.create(tid='T23456789', name='Team Beta')
        self.team3 = Team.objects.create(tid='T34567890', name='Team Gamma')

    def test_list_all_teams(self):
        response = self.client.get(reverse('teams-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_teams_by_name(self):
        response = self.client.get(reverse('teams-list'), {'name': 'alpha'})  # Case-insensitive search
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Team Alpha')

    def test_retrieve_team_by_tid(self):
        url = reverse('teams-detail', args=[self.team1.tid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Team Alpha')

    def test_create_team(self):
        data = {'name': 'Team Delta'}
        response = self.client.post(reverse('teams-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.count(), 4)

    def test_update_team(self):
        tid = self.team1.tid
        url = reverse('teams-detail', args=[tid])
        data = {'tid': tid, 'name': 'Team Alpha Updated'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Team.objects.get(tid=tid).name, 'Team Alpha Updated')

    def test_partial_update_team(self):
        tid = self.team1.tid
        url = reverse('teams-detail', args=[tid])
        data = {'name': 'Team Alpha Partial Update'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Team.objects.get(tid=tid).name, 'Team Alpha Partial Update')

    def test_delete_team(self):
        tid = self.team1.tid
        url = reverse('teams-detail', args=[tid])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Team.objects.count(), 2)
        self.assertFalse(Team.objects.filter(tid=tid).exists())


class MemberViewSetTestCase(BaseAPITestCaseAuthenticated):
    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(name='Test Team')
        self.other_user = User.objects.create_user(
            email='newuser@example.com',
            password='password123',
            first_name='Ahmad',
            last_name='Ameen'
        )

        self.profile1 = Profile.objects.create(user=self.user, display_name="User 1 name")
        self.profile2 = Profile.objects.create(user=self.other_user, display_name="User 2 name")

        self.member = Member.objects.create(user=self.user, team=self.team)

        self.url = reverse('team-members-list', kwargs={'team_tid': self.team.tid})

    def test_list_members(self):
        """Test retrieving members' profiles."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['display_name'], "User 1 name")

    def test_create_member_success(self):
        data = {'user': self.other_user.id}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Member.objects.filter(user=self.user, team=self.team).exists())

    def test_create_member_already_exists(self):
        """Test trying to add an existing user to the same team."""
        data = {'user': self.user.id}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already a member', str(response.data))

    def test_create_member_user_does_not_exist(self):
        """
        Test adding a member when the user does not exist.
        """
        data = {'user': 99}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_member_team_does_not_exist(self):
        """
        Test adding a member to a non-existent team.
        """
        invalid_url = reverse('team-members-list', kwargs={'team_tid': 'T56789012'})  # Non-existent team ID

        data = {'user': self.other_user.id}
        response = self.client.post(invalid_url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserTeamsListViewTest(BaseAPITestCaseAuthenticated):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email='newuser@example.com',
            password='password123',
            first_name='Ahmad',
            last_name='Ameen'
        )

        self.team1 = Team.objects.create(name='Team A')
        self.team2 = Team.objects.create(name='Team B')
        self.team3 = Team.objects.create(name='Team C')

        Member.objects.create(user=self.user, team=self.team1)
        Member.objects.create(user=self.user, team=self.team2)

        Member.objects.create(user=self.other_user, team=self.team3)

        self.url = '/api/users/teams/'

    def test_user_teams_list(self):
        """Test that the API returns only the teams of the authenticated user"""
        response = self.client.get(self.url)

        returned_team_names = {team['name'] for team in response.json()}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(returned_team_names, {'Team A', 'Team B'})

    def test_unauthenticated_request(self):
        self.unauthenticate()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
