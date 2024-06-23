import click
from datetime import datetime
from flask.cli import with_appcontext
from main import app, db, Product

@app.cli.command("load-fixtures")
@with_appcontext
def load_fixtures():
    products = [
        Product(name='Laptop', price=15000.0, created_at=datetime(2024, 5, 1)),
        Product(name='Monitor', price=5000.0, created_at=datetime(2024, 5, 1)),
        Product(name='Keyboard', price=1000.0, created_at=datetime(2024, 5, 1)),
        Product(name='Computer mouse', price=500.0, created_at=datetime(2024, 5, 1)),
    ]
    db.session.add_all(products)
    db.session.commit()
    click.echo('Fixtures loaded.')
    
if __name__ == '__main__':
    with app.app_context():
        load_fixtures()