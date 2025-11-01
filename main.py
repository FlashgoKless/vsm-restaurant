from flask import Flask
from models import db
from routes.menu import menu_bp
from routes.orders import orders_bp
from routes.products import products_bp
from routes.supplier import supplier_bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Регистрация blueprint'ов
    app.register_blueprint(menu_bp, url_prefix='/api')
    app.register_blueprint(orders_bp, url_prefix='/api')
    app.register_blueprint(products_bp, url_prefix='/api')
    app.register_blueprint(supplier_bp, url_prefix='/api')
    
    @app.route('/')
    def hello():
        return 'VSM Restaurant API is running!'
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)