from core.models import Ingredient
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
            'asdf@asdf',
            'asdf'
        )
        Ingredient.objects.create(user=user2, name='asdf')
        u1_ingre = Ingredient.objects.create(user=self.user, name='asdf1')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0].get('name'), u1_ingre.name)
