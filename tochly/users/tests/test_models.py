from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import Profile


User = get_user_model()
class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            timezone='America/New_York',
            dark_mode=True
        )

    def test_profile_creation(self):
        """Test that a profile is properly created"""
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.timezone, 'America/New_York')
        self.assertTrue(self.profile.dark_mode)

    def test_profile_str_representation(self):
        """Test the __str__ method of Profile"""
        self.assertEqual(str(self.profile), 'John Doe')

    def test_email_property(self):
        """Test the email property"""
        self.assertEqual(self.profile.email, 'test@example.com')

    def test_full_name_property(self):
        """Test the full_name property"""
        self.assertEqual(self.profile.full_name, 'John Doe')
        
        # Test with empty names
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='',
            last_name=''
        )
        profile2 = Profile.objects.create(user=user2)
        self.assertEqual(profile2.full_name, ' ')

    def test_auto_timestamps(self):
        """Test that created and updated timestamps work properly"""
        self.assertIsNotNone(self.profile.created)
        self.assertIsNotNone(self.profile.updated)
        self.assertLessEqual(self.profile.created, timezone.now())
        self.assertLessEqual(self.profile.updated, timezone.now())

    def test_optional_fields(self):
        """Test that optional fields can be null/blank"""
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123'
        )
        profile3 = Profile.objects.create(user=user3)
        
        self.assertIsNone(profile3.timezone)
        self.assertFalse(profile3.dark_mode)

    def test_profile_update(self):
        """Test updating profile fields"""
        self.profile.timezone = 'Europe/London'
        self.profile.dark_mode = False
        self.profile.save()
        
        updated_profile = Profile.objects.get(id=self.profile.id)
        self.assertEqual(updated_profile.timezone, 'Europe/London')
        self.assertFalse(updated_profile.dark_mode)
