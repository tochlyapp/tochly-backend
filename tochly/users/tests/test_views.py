from django.urls import reverse
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.test import APITestCase, APIClient
from rest_framework.response import Response
from rest_framework import status

from unittest.mock import patch

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
            '/api/jwt/create/', 
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
        self.refresh_token_url = reverse('token_refresh')
        login_response = self.client.post(
            reverse('token_obtain_pair'),
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
        self.url = reverse('token_verify')

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


class LogoutViewTestCas(TestCase):
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


class ProfileViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='ahmadmameen7@gmail.com', 
            password='testpassword',
            first_name='Ahmad',
            last_name='Ameen',
        )
        self.profile = Profile.objects.create(
            user=self.user, 
            display_name='Ahmad Ameen',
            phone_number='+2348083431164',
        )

        self.url = '/api/profiles/me/'

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_get_user_profile_authenticated(self):
        """Test that an authenticated user can retrieve their profile."""
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_name'], 'Ahmad Ameen')

    def test_get_user_profile_unauthenticated(self):
        """Test that an unauthenticated user cannot retrieve a profile."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile_authenticated(self):
        """Test that an authenticated user can update their profile."""
        self.authenticate()
        data = {'display_name': 'Ahmad M'}
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, 'Ahmad M')

    def test_partial_update_user_profile_authenticated(self):
        """Test that an authenticated user can partially update their profile."""
        self.authenticate()
        data = {'phone_number': '+2349068387166'}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone_number, '+2349068387166')

    def test_delete_user_profile_authenticated(self):
        """Test that an authenticated user can delete their profile."""
        self.authenticate()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Profile.objects.filter(user=self.user).exists())

    def test_delete_user_profile_unauthenticated(self):
        """Test that an unauthenticated user cannot delete a profile."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
