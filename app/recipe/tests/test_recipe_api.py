import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from core.models import Recipe, Tag, Ingredient
from django.test import TestCase
from django.urls import reverse

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main Counrse'):
    return Tag.objects.create(user=user, name=name)


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def sample_ingredient(user, name='Main Ing'):
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    defaults = {
        'title': 'Sample',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPI(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'asdf@asdf',
            'asdf@asdf',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):

        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'asdf2@asdf',
            'asdf@asdf',
        )
        r2 = sample_recipe(user=self.user, title='test2')
        sample_recipe(user=user2)
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.data[0]['title'], r2.title)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        recipe.ingredients.add(sample_ingredient(self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        payload = {
            'title': 'asdf',
            'link': '#',
            'time_minutes': 30,
            'price': 30.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        tag1 = sample_tag(self.user, '1')
        tag2 = sample_tag(self.user, '2')
        payload = {
            'title': 'qwer',
            'link': '#',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 30,
            'price': 30.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        ingredient1 = sample_ingredient(self.user, '1')
        ingredient2 = sample_ingredient(self.user, '2')
        payload = {
            'title': 'qwer',
            'link': '#',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 30,
            'price': 30.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)


    def test_partial_update_recipe(self):
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        new_tag = sample_tag(self.user, 'qouih')

        payload = {
            'title': 'qwer21',
            'tags': [new_tag.id],
        }

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):

        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        payload = {
            'title': 'qwe2312d21r',
            'time_minutes': 20,
            'price': 20.00,
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.tags.count(), 0)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'asdf@asdf',
            'asdf@asdf',
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')
        self.recipe.refresh_from_db()
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'not'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_filter_recipes_by_tags(self):
    #     recipe1 = sample_recipe(
    #         user=self.user, title='asdf'
    #     )
    #     recipe2 = sample_recipe(
    #         user=self.user, title='asdf2'
    #     )
    #     tag1 = sample_tag(user=self.user, name='tag1')
    #     tag2 = sample_tag(user=self.user, name='tag2')
    #     recipe1.tags.add(tag1)
    #     recipe2.tags.add(tag2)
    #
    #     recipe3 = sample_recipe(user=self.user, title='oiweqhkj')
    #
    #     res = self.client.get(
    #         RECIPES_URL,
    #         {'tags': f'{tag1.id},{tag2.id}'}
    #     )
    #     serializer1 = RecipeSerializer(recipe1)
    #     serializer2 = RecipeSerializer(recipe2)
    #     serializer3 = RecipeSerializer(recipe3)
    #     self.assertIn(serializer1.data, res.data)
    #     self.assertIn(serializer2.data, res.data)
    #     self.assertNotIn(serializer3.data, res.data)
    #
    # def test_filter_recipes_by_ingredients(self):
    #     recipe1 = sample_recipe(
    #         user=self.user, title='asdf'
    #     )
    #     recipe2 = sample_recipe(
    #         user=self.user, title='asdf2'
    #     )
    #     ingredient1 = sample_ingredient(user=self.user, name='ingredient1')
    #     ingredient2 = sample_ingredient(user=self.user, name='ingredient2')
    #     recipe1.ingredients.add(ingredient1)
    #     recipe2.ingredients.add(ingredient2)
    #
    #     recipe3 = sample_recipe(user=self.user, title='oiweqhkj')
    #
    #     res = self.client.get(
    #         RECIPES_URL,
    #         {'ingredients__in': [ingredient1.id, ingredient2.id]}
    #     )
    #     serializer1 = RecipeSerializer(recipe1)
    #     serializer2 = RecipeSerializer(recipe2)
    #     serializer3 = RecipeSerializer(recipe3)
    #     self.assertIn(serializer1.data, res.data)
    #     self.assertIn(serializer2.data, res.data)
    #     self.assertNotIn(serializer3.data, res.data)
