from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from users.models import Profile
from users.serializers import ProfileSerializer


User = get_user_model()
class ProfileSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.profile_data = {
            'user': self.user.id,
            'dark_mode': True
        }

    def test_serializer_fields(self):
        """Test that serializer contains all model fields"""
        profile = Profile.objects.create(user=self.user)
        serializer = ProfileSerializer(profile)
        expected_fields = ['id', 'user', 'dark_mode', 'created', 'updated', 'email', 'full_name']
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_get_email_method(self):
        """Test the get_email method"""
        profile = Profile.objects.create(user=self.user)
        serializer = ProfileSerializer(profile)
        self.assertEqual(serializer.data['email'], 'test@example.com')

    def test_get_full_name_method(self):
        """Test the get_full_name method"""
        profile = Profile.objects.create(user=self.user)
        serializer = ProfileSerializer(profile)
        self.assertEqual(serializer.data['full_name'], 'John Doe')

    def test_create_valid_profile(self):
        """Test creating a profile with valid data"""
        # Create a new user for this test to avoid conflicts
        new_user = User.objects.create_user(
            email='new@example.com',
            password='testpass123'
        )
        profile_data = {
            'user': new_user.id,
            'dark_mode': True
        }
        
        serializer = ProfileSerializer(data=profile_data)
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        self.assertEqual(profile.user, new_user)
        self.assertTrue(profile.dark_mode)

    def test_create_profile_missing_user(self):
        """Test creating a profile without a user"""
        invalid_data = {
            'dark_mode': False
        }
        serializer = ProfileSerializer(data=invalid_data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        
        self.assertIn('user', context.exception.detail)
        self.assertEqual(str(context.exception.detail['user'][0]), 'This field is required.')

    def test_serializer_output_format(self):
        """Test the serializer output format"""
        profile = Profile.objects.create(
            user=self.user,
            dark_mode=False
        )
        serializer = ProfileSerializer(profile)
        expected_data = {
            'id': profile.id,
            'user': self.user.id,
            'dark_mode': False,
            'created': profile.created.isoformat().replace('+00:00', 'Z'),
            'updated': profile.updated.isoformat().replace('+00:00', 'Z'),
            'email': 'test@example.com',
            'full_name': 'John Doe'
        }
        self.assertEqual(serializer.data, expected_data)

    def test_update_profile(self):
        """Test updating a profile"""
        profile = Profile.objects.create(
            user=self.user,
            dark_mode=True
        )
        update_data = {
            'dark_mode': False
        }
        serializer = ProfileSerializer(instance=profile, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        self.assertFalse(updated_profile.dark_mode)

    def test_read_only_fields(self):
        """Test that read_only fields cannot be updated"""
        profile = Profile.objects.create(user=self.user)
        update_data = {
            'email': 'new@example.com',  # Should be ignored
            'full_name': 'New Name'  # Should be ignored
        }
        serializer = ProfileSerializer(instance=profile, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        # Verify the read-only fields weren't changed
        self.assertEqual(updated_profile.email, 'test@example.com')
        self.assertEqual(updated_profile.full_name, 'John Doe')
