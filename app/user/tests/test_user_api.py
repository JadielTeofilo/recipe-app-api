from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """ """

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        payload = {
            'email': 'teste@gmail.com',
            'password': 'asdf@asdf.com',
            'name': 'asdf',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        user.check_password(payload['password'])
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        payload = {
            'email': 'teste@gmail.com',
            'password': 'asdf@asdf.com',
            'name': 'asdf',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user(self):
        payload = {
            'email': 'asdf@asdf.com',
            'password': 'asdfsdfg',
            'name': 'asdf',
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        create_user(email='asdf@asdf.com', password='asdf')
        payload = {
            'email': 'asdf@asdf.com',
            'password': 'asdfsdfg',
            'name': 'asdf',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)

    def test_create_token_no_user(self):
        payload = {
            'email': 'asdf@asdf.com',
            'password': 'asdfsdfg',
            'name': 'asdf',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):

    def setUp(self):
        self.user = create_user(**{
            'email': 'asdf@asdf.com',
            'password': 'asdfsdfg',
            'name': 'asdf',
        }
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', res)

    def test_post_not_allowed(self):
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {
            'email': self.user.email,
            'password': 'asdfsdfg6',
            'name': 'asdf',
        }
        self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertEqual(self.user.check_password(payload['password']), True)
