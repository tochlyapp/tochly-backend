from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from users.models import Profile
from users.serializers import UserSerializer, ProfileSerializer


User = get_user_model()

class UserSerializerTests(TestCase):
    def setUp(self):
        """Create a test user"""
        self.user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_serializer_with_valid_data(self):
        """Test serialization (model instance to JSON)"""
        serializer = UserSerializer(instance=self.user)
        expected_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
        }
        self.assertEqual(serializer.data, expected_data)

    def test_serializer_with_invalid_data(self):
        """Test deserialization (JSON to model instance) with invalid data"""
        invalid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',  # Invalid email format
        }
        serializer = UserSerializer(data=invalid_data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_serializer_with_missing_required_field(self):
        """Test deserialization with missing required field (email)"""
        incomplete_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            # 'email' is missing
        }
        serializer = UserSerializer(data=incomplete_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_serializer_create_user(self):
        """Test creating a new user via the serializer"""
        new_user_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
        }
        serializer = UserSerializer(data=new_user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Smith')
        self.assertEqual(user.email, 'jane.smith@example.com')

    def test_serializer_update_user(self):
        """Test updating an existing user via the serializer"""
        updated_data = {
            'first_name': 'Johnny',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
        }
        serializer = UserSerializer(instance=self.user, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, 'Johnny')  # Updated
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'john.doe@example.com')


class ProfileSerializerTests(TestCase):
    def setUp(self):
        """Create test user and profile"""
        self.user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
        }
        self.user = User.objects.create_user(**self.user_data)

        self.profile = Profile.objects.create(
            user=self.user,
            display_name='Test User',
            phone_number='+1234567890'
        )

    def test_serialization(self):
        """Test serialization of Profile instance to JSON"""
        serializer = ProfileSerializer(instance=self.profile)
        
        # Get dynamically generated ID
        expected_data = {
            'id': self.profile.id,
            'user': self.user.id,
            'display_name': 'Test User',
            'title': None,
            'phone_number': '+1234567890',
            'online': False,
            'status': '',
            'timezone': None,
            'dark_mode': False
        }
    
        self.assertDictEqual(serializer.data, expected_data)

    def test_create_profile_valid_data(self):
        """Test creating a new profile with valid data"""
        data = {
            'display_name': 'New User',
            'phone_number': '+1122334455'
        }
        serializer = ProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Create new user for this profile
        new_user = User.objects.create_user(email='new@example.com')
        profile = serializer.save(user=new_user)
        
        self.assertEqual(profile.user, new_user)
        self.assertEqual(profile.display_name, 'New User')
        self.assertEqual(profile.phone_number, '+1122334455')

    def test_create_profile_duplicate_phone_number(self):
        """Test unique phone number validation"""
        data = {
            'display_name': 'Duplicate Phone',
            'phone_number': '+1234567890'  # Same as setUp profile
        }
        serializer = ProfileSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)

    def test_update_profile(self):
        """Test updating an existing profile"""
        data = {
            'display_name': 'Updated Name',
            'title': 'Developer',
            'online': True
        }
        serializer = ProfileSerializer(instance=self.profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        
        self.assertEqual(updated_profile.display_name, 'Updated Name')
        self.assertEqual(updated_profile.title, 'Developer')
        self.assertTrue(updated_profile.online)

    def test_read_only_user_field(self):
        """Test that user field cannot be modified through serializer"""
        # Create test users with required names
        user1 = User.objects.create_user(
            email='user1@example.com',
            first_name='User',
            last_name='One',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            email='user2@example.com',
            first_name='User',
            last_name='Two',
            password='testpass123'
        )

        # Test 1: Attempt to create profile with user in data (should be ignored)
        data = {
            'user': user1.id,  # Serializer should ignore this
            'display_name': 'Test Profile'
        }
        serializer = ProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Should raise ValidationError due to missing user assignment
        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertEqual(context.exception.detail['user'], 'User is required')

        # Test 2: Proper creation with explicit user assignment
        profile = serializer.save(user=user2)
        self.assertEqual(profile.user, user2)
        self.assertEqual(profile.display_name, 'Test Profile')

        # Test 3: Attempt to update user through serializer (should be ignored)
        update_data = {
            'user': user1.id,  # Should be ignored
            'display_name': 'Updated Name'
        }
        serializer = ProfileSerializer(instance=profile, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        
        # Verify user remains unchanged
        self.assertEqual(updated_profile.user, user2)
        self.assertEqual(updated_profile.display_name, 'Updated Name')

    def test_optional_fields(self):
        """Test that optional fields can be omitted"""
        data = {
            'phone_number': '+2348083431164'
        }
        serializer = ProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        new_user = User.objects.create_user(email='optional@example.com')
        profile = serializer.save(user=new_user)
        
        self.assertEqual(profile.phone_number, '+2348083431164')
        self.assertIsNone(profile.display_name)
        self.assertIsNone(profile.title)
