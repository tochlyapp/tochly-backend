from django.urls import reverse
from django.contrib.auth import get_user_model

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


class MemberViewSetTest(BaseAPITestCaseAuthenticated):
    def setUp(self):
        super().setUp()
        self.base_url = '/api/teams/{}/members/'
        
        # Create test data
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            first_name='John',
            last_name='Doe'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            first_name='Jane',
            last_name='Smith'
        )
        
        self.team1 = Team.objects.create(name='Team 1', tid='TEAM1')
        self.team2 = Team.objects.create(name='Team 2', tid='TEAM2')
        
        # Create members
        self.member1 = Member.objects.create(
            user=self.user1,
            team=self.team1,
            display_name='Johnny'
        )
        self.member2 = Member.objects.create(
            user=self.user2,
            team=self.team1,
            display_name='Janey'
        )

    def test_list_members(self):
        """Test listing members"""
        response = self.client.get(self.base_url.format(self.team1.tid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['display_name'], 'Johnny')

    def test_create_member(self):
        """Test creating a new member"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'user': self.user2.id,
            'team': self.team2.id,
            'display_name': 'New Member',
            'role': 'member'
        }
        response = self.client.post(
            self.base_url.format(self.team2.tid),
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Member.objects.count(), 3)

    def test_create_duplicate_member(self):
        """Test preventing duplicate members"""
        self.client.force_authenticate(user=self.user1)
        
        Member.objects.create(
            user=self.user2,
            team=self.team2,
            display_name='Existing Member'
        )
        
        # Then try to create duplicate
        data = {
            'user': self.user2.id,
            'display_name': 'Duplicate',
            'role': 'member'
        }
        response = self.client.post(
            self.base_url.format(self.team2.tid),
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already a member', str(response.data))

    def test_profiles_action(self):
        """Test the custom profiles endpoint"""
        Profile.objects.create(user=self.user1)
        Profile.objects.create(user=self.user2)

        response = self.client.get(
            f"{self.base_url.format(self.team1.tid)}profiles/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['full_name'], 'John Doe')

    def test_list_with_search(self):
        """Test searching members"""
        response = self.client.get(
            f"{self.base_url.format(self.team1.tid)}?search=john"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['display_name'], 'Johnny')

    def test_list_with_limit(self):
        """Test limiting results"""
        response = self.client.get(
            f"{self.base_url.format(self.team1.tid)}?limit=1"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


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
