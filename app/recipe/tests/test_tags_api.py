from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import Tag
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'asdf@asdf', 'asdf'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):

        Tag.objects.create(user=self.user, name='nasdf')
        Tag.objects.create(user=self.user, name='213')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')

        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):

        user2 = get_user_model().objects.create_user(
            'asdf1@asdf', 'asdf1'
        )
        tag = Tag.objects.create(user=user2, name='nasdf')
        Tag.objects.create(user=self.user, name='nasdf')

        res = self.client.get(TAGS_URL)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_success(self):

        payload = {
            "name": "asdf",
        }
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload.get('name'),
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):

        payload = {
            'name': '',
        }
        res = self.client.post(TAGS_URL, payload)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)
