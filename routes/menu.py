from flask import Blueprint, request, jsonify
from models import db, MenuItem, Category, MenuItemIngredient, Product

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/menu', methods=['GET'])
def get_menu():
    """Получить меню с информацией о доступности"""
    category_id = request.args.get('category_id')
    
    query = MenuItem.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    menu_items = query.all()
    
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'price': item.price,
        'category_id': item.category_id,
        'category_name': item.category.name if item.category else None,
        'image_url': item.image_url,
        'cooking_time': item.cooking_time,
        'is_available': item.is_available and item.is_available_calculated,
        'ingredients': [{
            'id': ing.id,
            'product_id': ing.product_id,
            'product_name': ing.product.name,
            'quantity_required': ing.quantity_required,
            'unit': ing.product.unit
        } for ing in item.ingredients],
        'missing_ingredients': item.get_missing_ingredients() if not item.is_available_calculated else []
    } for item in menu_items])

@menu_bp.route('/menu/<int:item_id>/ingredients', methods=['POST'])
def add_ingredient_to_item(item_id):
    """Добавить ингредиент в блюдо"""
    menu_item = MenuItem.query.get_or_404(item_id)
    data = request.get_json()
    
    ingredient = MenuItemIngredient(
        menu_item_id=item_id,
        product_id=data['product_id'],
        quantity_required=data['quantity_required']
    )
    
    db.session.add(ingredient)
    db.session.commit()
    
    return jsonify({'message': 'Ingredient added'}), 201

@menu_bp.route('/menu/<int:item_id>/ingredients/<int:ingredient_id>', methods=['DELETE'])
def remove_ingredient_from_item(item_id, ingredient_id):
    """Удалить ингредиент из блюда"""
    ingredient = MenuItemIngredient.query.filter_by(
        id=ingredient_id, 
        menu_item_id=item_id
    ).first_or_404()
    
    db.session.delete(ingredient)
    db.session.commit()
    
    return jsonify({'message': 'Ingredient removed'})

@menu_bp.route('/menu/<int:item_id>/availability', methods=['GET'])
def check_availability(item_id):
    """Проверить доступность блюда и показать недостающие ингредиенты"""
    menu_item = MenuItem.query.get_or_404(item_id)
    
    return jsonify({
        'item_id': menu_item.id,
        'item_name': menu_item.name,
        'is_available': menu_item.is_available_calculated,
        'missing_ingredients': menu_item.get_missing_ingredients()
    })