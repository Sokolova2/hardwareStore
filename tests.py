import unittest
from main import app, db, Product, Order

class OrderManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_add_product(self):
        response = self.app.post('/products', json={'name': 'Test Product', 'price': 100.0})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Product', response.get_data(as_text=True))

    def test_add_order(self):
        with app.app_context():
            product = Product(name='Test Product', price=100.0)
            db.session.add(product)
            db.session.commit()
            product_id = product.id  
        response = self.app.post('/orders', json={'product_id': product_id})
        self.assertEqual(response.status_code, 200)
        self.assertIn('created', response.get_data(as_text=True))

    def test_update_order_status(self):
        with app.app_context():
            product = Product(name='Test Product', price=100.0)
            db.session.add(product)
            db.session.commit()
            order = Order(product_id=product.id)
            db.session.add(order)
            db.session.commit()
            order_id = order.id  
        response = self.app.put(f'/orders/{order_id}', json={'status': 'completed'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('completed', response.get_data(as_text=True))

    def test_generate_invoice(self):
        with app.app_context():
            product = Product(name='Test Product', price=100.0)
            db.session.add(product)
            db.session.commit()
            order = Order(product_id=product.id, status='completed')
            db.session.add(order)
            db.session.commit()
            order_id = order.id  
        response = self.app.post('/invoices', json={'order_id': order_id})
        self.assertEqual(response.status_code, 201)
        self.assertIn('Invoice generated successfully!', response.get_data(as_text=True))

    def test_pay_order(self):
        with app.app_context():
            product = Product(name='Test Product', price=100.0)
            db.session.add(product)
            db.session.commit()
            order = Order(product_id=product.id)
            db.session.add(order)
            db.session.commit()
            order_id = order.id 
        response = self.app.get(f'/orders/{order_id}/pay', json={'status': 'paid'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('paid', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()