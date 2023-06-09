from django.contrib.admin import site

from footgram_app.models import (
    Ingredients, Recipes, RecipesFavoritesUsers, RecipesIngredients,
    RecipesTags, ShoppingCarts, Subscriptions, Tags)

site.register(Ingredients)
site.register(Recipes)
site.register(RecipesFavoritesUsers)
site.register(RecipesIngredients)
site.register(RecipesTags)
site.register(ShoppingCarts)
site.register(Subscriptions)
site.register(Tags)
