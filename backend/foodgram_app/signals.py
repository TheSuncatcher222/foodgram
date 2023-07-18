import os

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Ingredients, Recipes, RecipesIngredients, RecipesTags, Tags


@receiver(signal=pre_delete, sender=Ingredients)
def delete_recipe_ingredients(sender, instance, *args, **kwargs) -> None:
    """При удалении объекта модели Ingredients также удаляет те объекты модели
    Recipes, с которыми существует связь через RecipesIngredients.
    Дополнительно уда"""
    recipes_del_ids: list[int] = RecipesIngredients.objects.filter(
        ingredient=instance).values_list('recipe_id', flat=True)
    recipes_del: list[Recipes] = Recipes.objects.filter(id__in=recipes_del_ids)
    media: list[str] = recipes_del.values_list('image', flat=True)
    for path in media:
        full_path: str = os.path.join('foodgram_app', 'media', path)
        try:
            os.remove(full_path)
        except FileNotFoundError:
            pass
    recipes_del.delete()
    return


@receiver(signal=pre_delete, sender=Tags)
def delete_recipe_tags(sender, instance, *args, **kwargs) -> None:
    """При удалении объекта модели Tags также удаляет связанные объекты
    в модели RecipesTags."""
    RecipesTags.objects.filter(tag=instance).delete()
    return
