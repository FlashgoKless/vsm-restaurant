from flask import Blueprint, request, jsonify
from models import db, Product, ProductSupply, MenuItem
from datetime import datetime

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    """Получить список всех продуктов"""
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'unit': p.unit,
        'current_stock': p.current_stock,
        'min_stock': p.min_stock,
        'cost_per_unit': p.cost_per_unit,
        'created_at': p.created_at.isoformat(),
        'is_low_stock': p.current_stock <= p.min_stock
    } for p in products])

@products_bp.route('/products', methods=['POST'])
def create_product():
    """Создать новый продукт"""
    data = request.get_json()
    
    product = Product(
        name=data['name'],
        unit=data['unit'],
        current_stock=data.get('current_stock', 0),
        min_stock=data.get('min_stock', 0),
        cost_per_unit=data.get('cost_per_unit', 0)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'message': 'Product created', 'id': product.id}), 201

@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Получить информацию о продукте"""
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'unit': product.unit,
        'current_stock': product.current_stock,
        'min_stock': product.min_stock,
        'cost_per_unit': product.cost_per_unit,
        'created_at': product.created_at.isoformat(),
        'supplies': [{
            'id': s.id,
            'quantity': s.quantity,
            'supply_date': s.supply_date.isoformat(),
            'supplier_name': s.supplier_name,
            'cost': s.cost,
            'batch_number': s.batch_number
        } for s in product.supplies]
    })

@products_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Обновить информацию о продукте"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    product.name = data.get('name', product.name)
    product.unit = data.get('unit', product.unit)
    product.min_stock = data.get('min_stock', product.min_stock)
    product.cost_per_unit = data.get('cost_per_unit', product.cost_per_unit)
    product.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Product updated'})

@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Удалить продукт"""
    product = Product.query.get_or_404(product_id)
    
    # Проверяем, используется ли продукт в каких-либо блюдах
    if product.menu_item_ingredients:
        return jsonify({'error': 'Cannot delete product that is used in menu items'}), 400
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'message': 'Product deleted'})

@products_bp.route('/products/<int:product_id>/supply', methods=['POST'])
def add_product_supply(product_id):
    """Добавить поставку продукта"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    quantity = data['quantity']
    supply = ProductSupply(
        product_id=product_id,
        quantity=quantity,
        supplier_name=data.get('supplier_name'),
        cost=data.get('cost'),
        batch_number=data.get('batch_number'),
        supply_date=datetime.utcnow()
    )
    
    # Обновляем текущий запас
    product.current_stock += quantity
    product.updated_at = datetime.utcnow()
    
    db.session.add(supply)
    db.session.commit()
    
    return jsonify({'message': 'Supply added', 'new_stock': product.current_stock})

@products_bp.route('/products/low-stock', methods=['GET'])
def get_low_stock_products():
    """Получить продукты с низким запасом"""
    low_stock_products = Product.query.filter(Product.current_stock <= Product.min_stock).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'unit': p.unit,
        'current_stock': p.current_stock,
        'min_stock': p.min_stock,
        'needed': p.min_stock - p.current_stock
    } for p in low_stock_products])

@products_bp.route('/products/stock-report', methods=['GET'])
def get_stock_report():
    """Получить отчет по остаткам"""
    products = Product.query.all()
    
    total_value = sum(p.current_stock * p.cost_per_unit for p in products)
    low_stock_count = sum(1 for p in products if p.current_stock <= p.min_stock)
    
    return jsonify({
        'total_products': len(products),
        'low_stock_count': low_stock_count,
        'total_inventory_value': total_value,
        'products': [{
            'id': p.id,
            'name': p.name,
            'current_stock': p.current_stock,
            'min_stock': p.min_stock,
            'unit': p.unit,
            'value': p.current_stock * p.cost_per_unit,
            'status': 'low' if p.current_stock <= p.min_stock else 'normal'
        } for p in products]
    })