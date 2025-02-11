from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient


User = get_user_model()

class BaseAPITestCaseAuthenticated(APITestCase):
    """Base test class for API views that require authentication."""

    def setUp(self):
        """Set up a test user and authenticate them."""
        self.user = self.create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def create_user(self, **kwargs):
        defaults = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User',
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)

    def authenticate(self, user=None):
        user = user or self.user
        self.client.force_authenticate(user=user)

    def unauthenticate(self):
        self.client.force_authenticate(user=None)
