from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.tests.base import BaseAPITestCaseAuthenticated
from users.models import Profile


User = get_user_model()

class TestCustomTokenObtainPairView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='ahmadmameen7@gmail.com', 
            password='testPassword123',
            first_name='Ahmad',
            last_name='Ameen',
        )

    def test_successful_login_sets_cookies(self):
        response = self.client.post(
            '/api/jwt/create/', 
            {'email': 'ahmadmameen7@gmail.com', 'password': 'testPassword123'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check access cookie
        access_cookie = response.cookies.get('access')
        self.assertIsNotNone(access_cookie)
        self.assertEqual(access_cookie.value, response.data['access'])
        self.assertEqual(access_cookie['max-age'], settings.AUTH_COOKIE_ACCESS_MAX_AGE)
        self.assertTrue(access_cookie['httponly'])
        self.assertEqual(access_cookie['samesite'], settings.AUTH_COOKIE_SAMESITE)
        
    def test_failed_login_does_not_set_cookies(self):
        response = self.client.post(
            reverse('token-obtain-pair'),
            {'email': 'ahmadmameen7@gmail.com', 'password': 'wrongPassword123'}
        )
        
        self.assertNotEqual(response.status_code, 200)
        self.assertNotIn('access', response.cookies)
        self.assertNotIn('refresh', response.cookies)


class TestCustomTokenRefreshView(APITestCase):
    def setUp(self):
        # Create a user and obtain a valid refresh token
        self.user = User.objects.create_user(
            email='ahmadmameen7@gmail.com', 
            password='testpass123',
            first_name='Ahmad',
            last_name='Ameen',
        )
        self.refresh_token_url = reverse('token-refresh')
        login_response = self.client.post(
            reverse('token-obtain-pair'),
            {'email': 'ahmadmameen7@gmail.com', 'password': 'testpass123'}
        )
        self.refresh_token = login_response.data.get('refresh')
        self.client.cookies['refresh'] = self.refresh_token  # Simulate cookie storage

    def test_successful_refresh_sets_access_cookie(self):
        """
        Test that a valid refresh cookie successfully refreshes the access token
        and sets the access cookie with correct attributes.
        """
        response = self.client.post(self.refresh_token_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.cookies)
        
        # Validate access cookie attributes
        access_cookie = response.cookies['access']
        self.assertEqual(access_cookie.value, response.data['access'])
        self.assertEqual(access_cookie['max-age'], settings.AUTH_COOKIE_ACCESS_MAX_AGE)
        self.assertEqual(access_cookie['path'], settings.AUTH_COOKIE_PATH)
        self.assertEqual(access_cookie['secure'], 'Secure' if settings.AUTH_COOKIE_SECURE else '')
        self.assertEqual(access_cookie['httponly'], settings.AUTH_COOKIE_HTTP_ONLY)
        self.assertEqual(access_cookie['samesite'], settings.AUTH_COOKIE_SAMESITE)

    def test_missing_refresh_cookie_returns_error(self):
        new_client = APIClient()  # Use a new client without cookies
        response = new_client.post(self.refresh_token_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access', response.cookies)

    def test_invalid_refresh_cookie_returns_error(self):
        self.client.cookies['refresh'] = 'invalid_token'  # Override with invalid token
        response = self.client.post(self.refresh_token_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.cookies)

    def test_refresh_token_in_body_works_if_no_cookie(self):
        """
        Test that a refresh token sent in the request body (instead of a cookie) works.
        """
        new_client = APIClient()  # Client without cookies
        response = new_client.post(
            self.refresh_token_url,
            {'refresh': self.refresh_token}  # Send refresh token in body
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.cookies)

    def test_cookie_refresh_token_overrides_body(self):
        """
        Test that the refresh cookie takes precedence over the request body.
        """
        # Send valid token in body but invalid token in cookie
        self.client.cookies['refresh'] = 'invalid_token'
        response = self.client.post(
            self.refresh_token_url,
            {'refresh': self.refresh_token}  # Valid token in body
        )
        
        # Expect error because cookie (invalid) overrides body (valid)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.cookies)

    
class TestCustomTokenVerifyView(APITestCase):
    def setUp(self):
        # Create a test user and generate a valid access token
        self.user = User.objects.create_user(
            email='ahmadmameen7@gmail.com', 
            password='testpass123',
            first_name='Ahmad',
            last_name='Ameen',
        )
        self.client = APIClient()
        self.access_token = str(RefreshToken.for_user(self.user).access_token)
        self.url = reverse('token-verify')

    def test_valid_token_in_cookie(self):
        self.client.cookies['access'] = self.access_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_in_cookie(self):
        self.client.cookies['access'] = 'invalid_token'
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_token_in_body(self):
        data = {'token': self.access_token}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_in_body(self):
        data = {'token': 'invalid_token'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cookie_token_overrides_valid_body_token(self):
        self.client.cookies['access'] = self.access_token
        data = {'token': 'invalid_token'}
        response = self.client.post(
            self.url, 
            data, 
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cookie_token_overrides_invalid_body_token(self):
        self.client.cookies['access'] = 'invalid_token'
        data = {'token': self.access_token}
        response = self.client.post(
            self.url, 
            data, 
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_token_provided(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ahmadmameen7@gmail.com', 
            password='testpass123',
            first_name='Ahmad',
            last_name='Ameen',
        )
        self.access_token = str(RefreshToken.for_user(self.user).access_token)
        self.client = APIClient()
        self.url = reverse('logout')

    def test_logout_unauthorized_access(self):
        self.client.post(self.url)

        # Attempt to log out again
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_post_returns_204(self):
        self.client.cookies['access'] = self.access_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_deletes_access_cookie(self):
        self.client.cookies['access'] = self.access_token
        response = self.client.post(self.url)
        
        access_cookie = response.cookies.get('access')
        self.assertIsNotNone(access_cookie, '')

    def test_logout_deletes_refresh_cookie(self):
        self.client.cookies['access'] = self.access_token
        response = self.client.post(self.url)
        
        refresh_cookie = response.cookies.get('refresh')
        self.assertIsNotNone(refresh_cookie, '')

class ProfileViewSetTests(BaseAPITestCaseAuthenticated):
    def setUp(self):
        super().setUp()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create profiles
        self.profile1 = Profile.objects.create(
            user=self.user1,
            dark_mode=True
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            dark_mode=False
        )
        
        # URLS
        self.list_url = '/api/profiles/'
        self.detail_url = f'/api/profiles/{self.profile1.id}/'
        self.me_url = '/api/profiles/me/'
        self.filter_url = '/api/profiles/?user_id={}'
       

    def test_list_profiles_authenticated(self):
        """Test listing profiles as authenticated user"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both profiles visible

    def test_filter_profiles_by_user_id(self):
        """Test filtering profiles by user_id"""
        self.client.force_authenticate(user=self.user1)
        url = self.filter_url.format(self.user2.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user2.id)

    def test_retrieve_profile(self):
        """Test retrieving a single profile"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user1.id)

    def test_me_endpoint_get(self):
        """Test GET /profiles/me/ endpoint"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user1.id)

    def test_me_endpoint_put(self):
        """Test updating profile via PUT /profiles/me/"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'user': self.user1.id,
            'dark_mode': False
        }
        response = self.client.put(self.me_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertFalse(self.profile1.dark_mode)

    def test_me_endpoint_patch(self):
        """Test partial update via PATCH /profiles/me/"""
        self.client.force_authenticate(user=self.user1)
        data = {'dark_mode': False}
        response = self.client.patch(self.me_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertFalse(self.profile1.dark_mode)

    def test_me_endpoint_delete(self):
        """Test deleting profile via DELETE /profiles/me/"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Profile.objects.filter(id=self.profile1.id).exists())

    def test_me_endpoint_profile_not_found(self):
        """Test /profiles/me/ when profile doesn't exist"""
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user3)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
