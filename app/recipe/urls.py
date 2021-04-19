from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()

router.register('tags', viewset=views.TagViewSet)
router.register('ingredients', viewset=views.IngredientViewSet)
router.register('recipe', viewset=views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
