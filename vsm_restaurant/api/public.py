# vsm_restaurant/api/public.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from vsm_restaurant.database import get_session
from models import MenuItem, MenuItemIngredient, Ingredient
from typing import List

router = APIRouter()

@router.get("/menu")
def public_menu(session: Session = Depends(get_session)):
    # Загружаем меню с рецептами и ингредиентами чтобы не делать N+1 запрос
    stmt = select(MenuItem).options(
        selectinload(MenuItem.recipe).selectinload(MenuItemIngredient.ingredient)
    ).where(MenuItem.enabled == True)
    menu_items = session.exec(stmt).all()

    result = []
    for item in menu_items:
        # собираем рецепт
        recipe = []
        ok = True
        for ri in item.recipe:
            ing = ri.ingredient
            recipe.append({
                "ingredient_id": ing.id,
                "ingredient_name": ing.name,
                "quantity": ri.quantity,
                "unit": ing.unit,
                "stock": ing.stock
            })
            if (ing.stock or 0.0) < ri.quantity:
                ok = False
        result.append({
            "id": item.id,
            "name": item.name,
            "price": item.price,
            "available": ok,
            "recipe": recipe
        })
    return result
