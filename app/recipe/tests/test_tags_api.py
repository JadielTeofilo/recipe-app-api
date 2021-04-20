from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import Tag, Recipe
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

    def test_retrieve_tags_assigned_to_recipes(self):
        tag1 = Tag.objects.create(user=self.user, name='asdf')
        tag2 = Tag.objects.create(user=self.user, name='asdf2')

        recipe = Recipe.objects.create(
            title='asdf',
            time_minutes=10,
            price=10.0,
            user=self.user,
        )
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        tag1 = Tag.objects.create(user=self.user, name='asdf')
        Tag.objects.create(user=self.user, name='asdf2')

        recipe = Recipe.objects.create(
            title='asdf',
            time_minutes=10,
            price=10.0,
            user=self.user,
        )
        recipe.tags.add(tag1)
        recipe2 = Recipe.objects.create(
            title='asdf',
            time_minutes=10,
            price=10.0,
            user=self.user,
        )
        recipe2.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
