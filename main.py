from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime, timedelta
#import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='created')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref=db.backref('orders', lazy=True))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    total = db.Column(db.Float, nullable=False) 
    order_created_at = db.Column(db.DateTime)  
    invoice_generated_at = db.Column(db.DateTime, default=datetime.utcnow) 
    order = db.relationship('Order', backref=db.backref('invoice', lazy=True))

with app.app_context():
    db.create_all()


class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True

product_schema = ProductSchema()
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


@app.route('/products', methods=['POST'])
def add_product():
    name = request.json['name']
    price = request.json['price']
    new_product = Product(name=name, price=price)
    db.session.add(new_product)
    db.session.commit()
    return product_schema.jsonify(new_product)


@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "created_at": product.created_at
    } for product in products])

@app.route('/orders', methods=['POST'])
def add_order():
    product_id = request.json['product_id']
    new_order = Order(product_id=product_id)
    db.session.add(new_order)
    db.session.commit()
    return order_schema.jsonify(new_order)

@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    order = Order.query.get(order_id)
    if order:
        order.status = request.json['status']
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return order_schema.jsonify(order)
    return jsonify({'message': 'Order not found'}), 404


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)
    if order:
        return order_schema.jsonify(order)
    return jsonify({'message': 'Order not found'}), 404


@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)

@app.route('/products/discounted', methods=['GET'])
def get_discounted_products():
    current_date = datetime.utcnow()
    threshold_date = current_date - timedelta(days=30)
    
    products = Product.query.filter(Product.created_at <= threshold_date).all()
    
    discounted_products = []
    for product in products:
        discount = 0.20 if product.created_at <= threshold_date else 0
        discounted_price = product.price * (1 - discount)
        discounted_products.append({
            'name': product.name,
            'price': product.price,
            'discounted_price': discounted_price
        })
    
    return jsonify(discounted_products)



@app.route('/invoices', methods=['POST'])
def generate_invoice():
    data = request.get_json()
    order_id = data.get('order_id')  
    if not order_id:
        return jsonify({"message": "Order ID is required"}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404

    product = Product.query.get(order.product_id)
    if not product:
        return jsonify({"message": "Product for the order not found"}), 404

    total_price = product.price
    invoice = Invoice(order_id=order.id, total=total_price, order_created_at = order.created_at )
    db.session.add(invoice)
    db.session.commit()
    
    return jsonify({"message": "Invoice generated successfully!"}), 201


@app.route('/invoices', methods=['GET'])
def get_invoices():
    invoices = Invoice.query.all()
    result = []
    for invoice in invoices:
        order = Order.query.get(invoice.order_id)
        product = Product.query.get(order.product_id)
        result.append({
            "id": invoice.id,
            "order_id": invoice.order_id,
            "total": invoice.total,
            "order_created_at": invoice.order_created_at,  
            "invoice_generated_at": invoice.invoice_generated_at, 
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price
            }
        })
    return jsonify(result)


@app.route('/orders/<int:order_id>/pay', methods=['GET'])
def pay_order(order_id):
    order = Order.query.get(order_id)
    if order:
        order.status = 'paid'
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return order_schema.jsonify(order)
    return jsonify({'message': 'Order not found'}), 404


@app.route('/orders/filter', methods=['GET'])
def filter_orders():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS.mmmmmm)'}), 400

    orders = Order.query.filter(Order.created_at.between(start_date, end_date)).all()
    return orders_schema.jsonify(orders)


if __name__ == '__main__':
    app.run(debug=True)