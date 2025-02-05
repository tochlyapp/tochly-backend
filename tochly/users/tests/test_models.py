from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from users.models import Profile

User = get_user_model()

class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            display_name='Test Display',
            title='Developer',
            phone_number='+1234567890',
            status='meeting',
            timezone='UTC'
        )


    def test_model_field_definitions(self):
        # Test user relationship
        user_field = Profile._meta.get_field('user')
        self.assertEqual(user_field.related_model, User)

        # Test display_name field
        display_name_field = Profile._meta.get_field('display_name')
        self.assertEqual(display_name_field.max_length, 50)
        self.assertTrue(display_name_field.null)
        self.assertTrue(display_name_field.blank)

        # Test phone_number field
        phone_field = Profile._meta.get_field('phone_number')
        self.assertEqual(phone_field.max_length, 15)
        self.assertTrue(phone_field.unique)
        self.assertTrue(phone_field.db_index)

        # Test online field
        online_field = Profile._meta.get_field('online')
        self.assertFalse(online_field.default)

        # Test status field
        status_field = Profile._meta.get_field('status')
        self.assertEqual(status_field.max_length, 20)
        self.assertEqual(status_field.default, '')
        self.assertTrue(status_field.blank)
        self.assertTrue(status_field.null)

    def test_properties(self):
        # Test email property
        self.assertEqual(self.profile.email, 'test@example.com')
        
        # Test full_name property
        self.assertEqual(self.profile.full_name, 'John Doe')

    def test_str_representation(self):
        self.assertEqual(str(self.profile), 'John Doe')

    def test_default_values(self):
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        new_profile = Profile.objects.create(user=new_user)
        
        # Test default values
        self.assertFalse(new_profile.online)
        self.assertEqual(new_profile.status, '')
        self.assertFalse(new_profile.dark_mode)

    def test_status_choices(self):
        status_field = Profile._meta.get_field('status')
        expected_choices = [
            ('', ''),
            ('meeting', 'In a Meeting'),
            ('commuting', 'Commuting'),
            ('remote', 'Working Remotely'),
            ('sick', 'Sick'),
            ('leave', 'In Leave'),
        ]
        self.assertEqual(status_field.choices, expected_choices)

    def test_valid_status_values(self):
        valid_statuses = ['', 'meeting', 'commuting', 'remote', 'sick', 'leave']
        for status in valid_statuses:
            self.profile.status = status
            self.profile.full_clean()  # Should not raise validation error

    def test_invalid_status_raises_error(self):
        self.profile.status = 'invalid_status'
        with self.assertRaises(ValidationError):
            self.profile.full_clean()

    def test_phone_number_uniqueness(self):
        user2 = User.objects.create_user(
            email='newuser2@example.com',
            password='testpass123'
        )
        with self.assertRaises(IntegrityError):
            Profile.objects.create(
                user=user2,
                phone_number=self.profile.phone_number
            )

    def test_user_deletion_cascades(self):
        user_id = self.user.id
        self.user.delete()
        with self.assertRaises(Profile.DoesNotExist):
            Profile.objects.get(user_id=user_id)

    def test_optional_fields(self):
        # Test blank/null fields can be empty
        self.profile.display_name = None
        self.profile.title = None
        self.profile.phone_number = None
        self.profile.timezone = None
        self.profile.full_clean()  # Should not raise validation error
        self.profile.save()

        updated_profile = Profile.objects.get(pk=self.profile.pk)
        self.assertIsNone(updated_profile.display_name)
        self.assertIsNone(updated_profile.title)
        self.assertIsNone(updated_profile.phone_number)
        self.assertIsNone(updated_profile.timezone)
