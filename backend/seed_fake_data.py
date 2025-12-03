import random
from datetime import datetime, timedelta
from app import create_app, db, Product, Transaction, TransactionItem

app = create_app()

import random
from datetime import datetime, timedelta


PRODUCT_NAMES = [
    'Espresso', 'Latte', 'Cappuccino', 'Tea', 'Orange Juice', 'Muffin', 'Bagel', 'Sandwich',
    'Chocolate', 'Soda', 'Water', 'Cookie', 'Salad', 'Burger', 'Fries', 'Milk', 'Yogurt', 'Granola', 'Apple', 'Banana'
]


def reset_data(app):
    """Clear all tables and recreate sample products + random transactions.

    `app` should be a Flask app instance (so caller provides app or uses create_app()).
    """
    # import inside function to avoid circular imports at module import time
    from app import db, Product, Transaction, TransactionItem

    with app.app_context():
        # ensure tables exist
        db.create_all()

        # delete existing data (delete children first)
        try:
            TransactionItem.query.delete()
            Transaction.query.delete()
            Product.query.delete()
            db.session.commit()
        except Exception:
            db.session.rollback()

        # create products
        created = 0
        products = []
        for name in PRODUCT_NAMES:
            p = Product(name=name,
                        price=round(random.uniform(0.5, 10.0), 2),
                        cost=round(random.uniform(0.2, 5.0), 2),
                        stock=random.randint(10, 200))
            db.session.add(p)
            products.append(p)
            created += 1
        db.session.commit()

        # generate random transactions
        tx_count = 50
        created_tx = 0
        if products:
            products = Product.query.all()
            for i in range(tx_count):
                items = []
                for _ in range(random.randint(1, 4)):
                    p = random.choice(products)
                    qty = random.randint(1, 5)
                    items.append((p, qty))
                total = sum(p.price * q for p, q in items)
                t = Transaction(timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                                total_amount=round(total, 2))
                db.session.add(t)
                db.session.flush()
                for p, q in items:
                    ti = TransactionItem(transaction_id=t.id, product_id=p.id, quantity=q, price_at_sale=p.price)
                    db.session.add(ti)
                    p.stock = max(0, p.stock - q)
                created_tx += 1
            db.session.commit()

        return {'products_created': created, 'transactions_created': created_tx}


if __name__ == '__main__':
    # allow running as standalone script
    from app import create_app

    app = create_app()
    res = reset_data(app)
    print(f"Products created: {res.get('products_created', 0)}, transactions: {res.get('transactions_created', 0)}")
