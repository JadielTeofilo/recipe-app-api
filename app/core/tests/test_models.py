from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='asdf@asdf', password='asdf'):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = "test@email.com"
        password = "asdf"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = "test@asdfDSF"
        user = get_user_model().objects.create_user(email, 'asdf')

        self.assertEquals(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test invalid email"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'asdf')

    def test_create_new_superuser(self):
        """Test that created a superuser"""
        user = get_user_model().objects.create_superuser('asdf@asdf', 'asdf')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_tag_str(self):
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='vegan'
        )
        self.assertEqual(str(tag), tag.name)
