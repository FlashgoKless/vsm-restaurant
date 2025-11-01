from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # кг, шт, л и т.д.
    current_stock = db.Column(db.Float, default=0)
    min_stock = db.Column(db.Float, default=0)
    cost_per_unit = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с составом блюд
    menu_item_ingredients = db.relationship('MenuItemIngredient', back_populates='product', cascade='all, delete-orphan')
    # История поставок
    supplies = db.relationship('ProductSupply', back_populates='product', cascade='all, delete-orphan')

class MenuItemIngredient(db.Model):
    __tablename__ = 'menu_item_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_required = db.Column(db.Float, nullable=False)
    
    # Связи
    menu_item = db.relationship('MenuItem', back_populates='ingredients')
    product = db.relationship('Product', back_populates='menu_item_ingredients')

class ProductSupply(db.Model):
    __tablename__ = 'product_supplies'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    supply_date = db.Column(db.DateTime, default=datetime.utcnow)
    supplier_name = db.Column(db.String(200))
    cost = db.Column(db.Float)
    batch_number = db.Column(db.String(100))
    
    # Связи
    product = db.relationship('Product', back_populates='supplies')

# Обновляем модель MenuItem
class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255))
    cooking_time = db.Column(db.Integer)  # время приготовления в минутах
    
    # Связи
    category = db.relationship('Category', back_populates='menu_items')
    ingredients = db.relationship('MenuItemIngredient', back_populates='menu_item', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', back_populates='menu_item')
    
    @property
    def is_available_calculated(self):
        """Рассчитывает доступность на основе остатков продуктов"""
        for ingredient in self.ingredients:
            if ingredient.product.current_stock < ingredient.quantity_required:
                return False
        return True
    
    def get_missing_ingredients(self):
        """Возвращает список недостающих ингредиентов"""
        missing = []
        for ingredient in self.ingredients:
            if ingredient.product.current_stock < ingredient.quantity_required:
                missing.append({
                    'product_name': ingredient.product.name,
                    'required': ingredient.quantity_required,
                    'available': ingredient.product.current_stock,
                    'unit': ingredient.product.unit
                })
        return missing

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    
    menu_items = db.relationship('MenuItem', back_populates='category')

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    total_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    order = db.relationship('Order', back_populates='order_items')
    menu_item = db.relationship('MenuItem', back_populates='order_items')