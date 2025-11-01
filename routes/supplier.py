from flask import Blueprint, request, jsonify
from models import db, ProductSupply, Product
from datetime import datetime, timedelta

supplier_bp = Blueprint('supplier', __name__)

@supplier_bp.route('/supplier/supplies', methods=['GET'])
def get_supplies():
    """Получить историю поставок (для поставщиков)"""
    days = request.args.get('days', 30, type=int)
    supplier_name = request.args.get('supplier_name')
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = ProductSupply.query.filter(ProductSupply.supply_date >= start_date)
    
    if supplier_name:
        query = query.filter(ProductSupply.supplier_name.ilike(f'%{supplier_name}%'))
    
    supplies = query.order_by(ProductSupply.supply_date.desc()).all()
    
    return jsonify([{
        'id': s.id,
        'product_id': s.product_id,
        'product_name': s.product.name,
        'quantity': s.quantity,
        'unit': s.product.unit,
        'supply_date': s.supply_date.isoformat(),
        'supplier_name': s.supplier_name,
        'cost': s.cost,
        'batch_number': s.batch_number,
        'total_cost': s.quantity * (s.cost or 0)
    } for s in supplies])

@supplier_bp.route('/supplier/supplies', methods=['POST'])
def create_supply_bulk():
    """Массовое добавление поставок (для поставщиков)"""
    data = request.get_json()
    supplies_data = data['supplies']
    
    created_supplies = []
    
    for supply_data in supplies_data:
        product = Product.query.get(supply_data['product_id'])
        if not product:
            continue
            
        supply = ProductSupply(
            product_id=supply_data['product_id'],
            quantity=supply_data['quantity'],
            supplier_name=supply_data.get('supplier_name'),
            cost=supply_data.get('cost'),
            batch_number=supply_data.get('batch_number'),
            supply_date=datetime.utcnow()
        )
        
        # Обновляем запас
        product.current_stock += supply_data['quantity']
        product.updated_at = datetime.utcnow()
        
        db.session.add(supply)
        created_supplies.append({
            'product_id': supply.product_id,
            'product_name': product.name,
            'quantity': supply.quantity
        })
    
    db.session.commit()
    
    return jsonify({
        'message': f'{len(created_supplies)} supplies added',
        'supplies': created_supplies
    }), 201

@supplier_bp.route('/supplier/products-to-order', methods=['GET'])
def get_products_to_order():
    """Получить список продуктов для заказа у поставщиков"""
    # Продукты с низким запасом
    low_stock_products = Product.query.filter(
        Product.current_stock <= Product.min_stock
    ).all()
    
    return jsonify([{
        'product_id': p.id,
        'product_name': p.name,
        'current_stock': p.current_stock,
        'min_stock': p.min_stock,
        'unit': p.unit,
        'quantity_to_order': max(p.min_stock - p.current_stock, 0),
        'cost_per_unit': p.cost_per_unit,
        'estimated_cost': max(p.min_stock - p.current_stock, 0) * p.cost_per_unit
    } for p in low_stock_products])

@supplier_bp.route('/supplier/monthly-report', methods=['GET'])
def get_monthly_supplier_report():
    """Получить месячный отчет по поставкам"""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    if not month or not year:
        # По умолчанию текущий месяц
        now = datetime.utcnow()
        month = now.month
        year = now.year
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    supplies = ProductSupply.query.filter(
        ProductSupply.supply_date >= start_date,
        ProductSupply.supply_date < end_date
    ).all()
    
    # Группировка по поставщикам
    supplier_stats = {}
    for supply in supplies:
        supplier = supply.supplier_name or 'Unknown'
        if supplier not in supplier_stats:
            supplier_stats[supplier] = {
                'supplier_name': supplier,
                'total_quantity': 0,
                'total_cost': 0,
                'supply_count': 0,
                'products': set()
            }
        
        supplier_stats[supplier]['total_quantity'] += supply.quantity
        supplier_stats[supplier]['total_cost'] += (supply.cost or 0) * supply.quantity
        supplier_stats[supplier]['supply_count'] += 1
        supplier_stats[supplier]['products'].add(supply.product.name)
    
    # Преобразуем sets в lists
    for stat in supplier_stats.values():
        stat['products'] = list(stat['products'])
    
    return jsonify({
        'month': month,
        'year': year,
        'total_supplies': len(supplies),
        'supplier_stats': list(supplier_stats.values())
    })