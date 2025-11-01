from flask import Blueprint, request, jsonify
from models import db, Order, OrderItem, MenuItem, Product, MenuItemIngredient
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders', methods=['GET'])
def get_orders():
    """Получить список всех заказов"""
    status = request.args.get('status')
    
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return jsonify([{
        'id': order.id,
        'table_number': order.table_number,
        'status': order.status,
        'total_amount': order.total_amount,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
        'items': [{
            'id': item.id,
            'menu_item_id': item.menu_item_id,
            'menu_item_name': item.menu_item.name,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.order_items]
    } for order in orders])

@orders_bp.route('/orders', methods=['POST'])
def create_order():
    """Создать новый заказ"""
    data = request.get_json()
    
    # Проверяем доступность всех блюд в заказе
    for item in data['items']:
        menu_item = MenuItem.query.get(item['menu_item_id'])
        if not menu_item:
            return jsonify({'error': f'Menu item {item["menu_item_id"]} not found'}), 404
        
        if not menu_item.is_available:
            return jsonify({'error': f'Menu item {menu_item.name} is not available'}), 400
        
        # Проверяем наличие ингредиентов
        if not menu_item.is_available_calculated:
            missing = menu_item.get_missing_ingredients()
            return jsonify({
                'error': f'Not enough ingredients for {menu_item.name}',
                'missing_ingredients': missing
            }), 400
    
    # Создаем заказ
    order = Order(
        table_number=data['table_number'],
        status='pending',
        total_amount=0
    )
    
    db.session.add(order)
    db.session.flush()  # Получаем ID заказа
    
    # Добавляем позиции заказа и списываем ингредиенты
    total_amount = 0
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item_data['menu_item_id'],
            quantity=item_data['quantity'],
            price=menu_item.price
        )
        
        total_amount += menu_item.price * item_data['quantity']
        
        # Списываем ингредиенты
        for ingredient in menu_item.ingredients:
            ingredient.product.current_stock -= ingredient.quantity_required * item_data['quantity']
            ingredient.product.updated_at = datetime.utcnow()
        
        db.session.add(order_item)
    
    order.total_amount = total_amount
    db.session.commit()
    
    return jsonify({
        'message': 'Order created successfully',
        'order_id': order.id,
        'total_amount': total_amount
    }), 201

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Получить информацию о конкретном заказе"""
    order = Order.query.get_or_404(order_id)
    
    return jsonify({
        'id': order.id,
        'table_number': order.table_number,
        'status': order.status,
        'total_amount': order.total_amount,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
        'items': [{
            'id': item.id,
            'menu_item_id': item.menu_item_id,
            'menu_item_name': item.menu_item.name,
            'quantity': item.quantity,
            'price': item.price,
            'subtotal': item.quantity * item.price
        } for item in order.order_items]
    })

@orders_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Обновить статус заказа"""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    new_status = data.get('status')
    
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    # Если заказ отменен, возвращаем ингредиенты на склад
    if new_status == 'cancelled' and order.status != 'cancelled':
        for order_item in order.order_items:
            menu_item = order_item.menu_item
            for ingredient in menu_item.ingredients:
                ingredient.product.current_stock += ingredient.quantity_required * order_item.quantity
                ingredient.product.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': f'Order status updated to {new_status}'})

@orders_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Отменить заказ"""
    order = Order.query.get_or_404(order_id)
    
    # Возвращаем ингредиенты на склад
    for order_item in order.order_items:
        menu_item = order_item.menu_item
        for ingredient in menu_item.ingredients:
            ingredient.product.current_stock += ingredient.quantity_required * order_item.quantity
            ingredient.product.updated_at = datetime.utcnow()
    
    order.status = 'cancelled'
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Order cancelled and ingredients restored'})

@orders_bp.route('/orders/table/<int:table_number>', methods=['GET'])
def get_orders_by_table(table_number):
    """Получить заказы для конкретного стола"""
    orders = Order.query.filter_by(table_number=table_number)\
        .order_by(Order.created_at.desc())\
        .all()
    
    return jsonify([{
        'id': order.id,
        'table_number': order.table_number,
        'status': order.status,
        'total_amount': order.total_amount,
        'created_at': order.created_at.isoformat(),
        'items': [{
            'menu_item_name': item.menu_item.name,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.order_items]
    } for order in orders])

@orders_bp.route('/orders/stats', methods=['GET'])
def get_order_stats():
    """Получить статистику по заказам"""
    # Статистика за сегодня
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    
    today_orders = Order.query.filter(Order.created_at >= today_start).all()
    completed_orders = [o for o in today_orders if o.status == 'completed']
    
    total_revenue = sum(order.total_amount for order in completed_orders)
    avg_order_value = total_revenue / len(completed_orders) if completed_orders else 0
    
    # Самые популярные блюда
    from sqlalchemy import func
    popular_items = db.session.query(
        OrderItem.menu_item_id,
        MenuItem.name,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(MenuItem).filter(
        Order.order_id == OrderItem.order_id,
        Order.status == 'completed',
        Order.created_at >= today_start
    ).group_by(OrderItem.menu_item_id)\
     .order_by(func.sum(OrderItem.quantity).desc())\
     .limit(5).all()
    
    return jsonify({
        'today': {
            'total_orders': len(today_orders),
            'completed_orders': len(completed_orders),
            'total_revenue': total_revenue,
            'average_order_value': avg_order_value
        },
        'popular_items': [{
            'menu_item_id': item.menu_item_id,
            'name': item.name,
            'total_quantity': item.total_quantity
        } for item in popular_items]
    })