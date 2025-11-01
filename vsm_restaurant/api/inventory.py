# vsm_restaurant/api/inventory.py
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlmodel import Session, select
from typing import List
from vsm_restaurant.database import get_session
from models import MenuItem, Ingredient, MenuItemIngredient

router = APIRouter()

# Простой статический токен (в проде - заменить на env/config)
SERVICE_TOKEN = "super-secret-static-token"


def require_service_token(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no auth")
    # ожидаем "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad auth")
    token = authorization.split(" ", 1)[1]
    if token != SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return True


# --------- Ingredients CRUD (служебный) ----------
@router.post("/service/ingredients", dependencies=[Depends(require_service_token)])
def create_ingredient(payload: Ingredient, session: Session = Depends(get_session)):
    # payload may include stock
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return payload


@router.get("/service/ingredients", dependencies=[Depends(require_service_token)])
def list_ingredients(session: Session = Depends(get_session)) -> List[Ingredient]:
    return session.exec(select(Ingredient)).all()


@router.patch("/service/ingredients/{ingredient_id}", dependencies=[Depends(require_service_token)])
def update_ingredient(ingredient_id: int, payload: Ingredient, session: Session = Depends(get_session)):
    ing = session.get(Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(404, "ingredient not found")
    ing.name = payload.name or ing.name
    ing.unit = payload.unit or ing.unit
    # если payload.stock задан явно — перезаписать
    if payload.stock is not None:
        ing.stock = payload.stock
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return ing


# --------- Supplier endpoint: пополнение остатков ----------
class RestockPayload(SQLModel):
    ingredient_id: Optional[int] = None
    ingredient_name: Optional[str] = None
    quantity: float


@router.post("/supplier/restock")
def supplier_restock(payload: RestockPayload, session: Session = Depends(get_session)):
    """
    Поставщик присылает {ingredient_id | ingredient_name, quantity}
    Если ingredient_name и ingredient не существует — создаём.
    """
    if not payload.ingredient_id and not payload.ingredient_name:
        raise HTTPException(400, "ingredient_id or ingredient_name required")
    if payload.ingredient_id:
        ing = session.get(Ingredient, payload.ingredient_id)
        if not ing:
            raise HTTPException(404, "ingredient not found")
    else:
        ing = session.exec(select(Ingredient).where(Ingredient.name == payload.ingredient_name)).first()
        if not ing:
            ing = Ingredient(name=payload.ingredient_name, stock=0.0)
            session.add(ing)
            session.commit()
            session.refresh(ing)
    # безопасно пополняем в транзакции
    ing.stock = (ing.stock or 0.0) + float(payload.quantity)
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return {"ingredient_id": ing.id, "new_stock": ing.stock}


# --------- Menu management (служебные) ----------
@router.post("/service/menu", dependencies=[Depends(require_service_token)])
def create_menu_item(payload: MenuItem, session: Session = Depends(get_session)):
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return payload


@router.get("/service/menu", dependencies=[Depends(require_service_token)])
def list_menu_service(session: Session = Depends(get_session)) -> List[MenuItem]:
    return session.exec(select(MenuItem)).all()
