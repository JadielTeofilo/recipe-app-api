from core.models import Ingredient, Recipe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'asdf@asdf',
            'asdf'
        )
        self.client.force_authenticate(self.user)

    def test_restrieve_ingredient_list(self):
        Ingredient.objects.create(user=self.user, name='asdf')
        Ingredient.objects.create(user=self.user, name='asdf1')

        res = self.client.get(INGREDIENTS_URL)

        ingreds = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingreds, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'asdf@asdf3',
            'asdf'
        )
        Ingredient.objects.create(user=user2, name='asdf')
        u1_ingre = Ingredient.objects.create(user=self.user, name='asdf1')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0].get('name'), u1_ingre.name)

    def test_create_ingredient_success(self):
        payload = {
            'name': 'asdf'
        }
        self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects\
            .filter(user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        payload = {
            'name': ''
        }
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name='asdf')
        ingredient2 = Ingredient.objects.create(user=self.user, name='asdf2')

        recipe = Recipe.objects.create(
            title='asdf',
            time_minutes=10,
            price=10.0,
            user=self.user,
        )
        recipe.ingredients.add(ingredient1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name='asdf')
        Ingredient.objects.create(user=self.user, name='asdf2')

        recipe = Recipe.objects.create(
            title='asdf',
            time_minutes=10,
            price=10.0,
            user=self.user,
        )
        recipe.ingredients.add(ingredient1)
        recipe2 = Recipe.objects.create(
            title='asdf',
            time_minutes=10,
            price=10.0,
            user=self.user,
        )
        recipe2.ingredients.add(ingredient1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
